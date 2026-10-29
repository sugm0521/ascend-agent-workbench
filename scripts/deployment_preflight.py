#!/usr/bin/env python3
"""Check declared host prerequisites and Docker mounts/env; never deploy or repair.

Python 3.10+, standard library only. Run on the target host through its existing
execution tool. See docs/tools/deployment-preflight.md for the plan and evidence scope.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys


def load_json(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def host_path(value):
    if not isinstance(value, str) or not value or "\0" in value or "," in value or not Path(value).is_absolute():
        raise ValueError("host paths must be absolute and contain no NUL or comma")
    return Path(value)


def target_path(value):
    if not isinstance(value, str) or "\0" in value or "," in value:
        raise ValueError("invalid container path")
    path = PurePosixPath(value)
    if not path.is_absolute() or ".." in path.parts or str(path) != value:
        raise ValueError("container paths must be normalized absolute POSIX paths")
    return value


def validate_plan(plan):
    if not isinstance(plan, dict) or plan.get("schema_version") != 1:
        raise ValueError("plan schema_version must be 1")
    allowed = {"schema_version", "node", "container", "mounts", "env", "communication", "required_paths", "required_commands"}
    if set(plan) - allowed:
        raise ValueError("unknown plan fields: " + ", ".join(sorted(set(plan) - allowed)))
    if not isinstance(plan.get("node"), str) or not plan["node"]:
        raise ValueError("node must identify the actual target")
    if not isinstance(plan.get("container"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", plan["container"]):
        raise ValueError("container must be an explicit Docker name")
    mounts = plan.get("mounts")
    if not isinstance(mounts, list):
        raise ValueError("mounts must be a list of required bind mounts")
    targets = set()
    for mount in mounts:
        if not isinstance(mount, dict) or set(mount) != {"source", "target", "kind", "read_only"}:
            raise ValueError("mount requires source, target, kind and read_only")
        host_path(mount["source"])
        target_path(mount["target"])
        if mount["kind"] not in ("file", "directory") or type(mount["read_only"]) is not bool:
            raise ValueError("bind mount kind must be file/directory; read_only must be boolean")
        if mount["target"] in targets:
            raise ValueError("duplicate mount target: " + mount["target"])
        targets.add(mount["target"])
    env = plan.get("env", {})
    if not isinstance(env, dict) or any(not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) or not isinstance(value, str) or "\0" in value for key, value in env.items()):
        raise ValueError("env must map environment names to strings (empty clears a value)")
    comm = plan.get("communication")
    if not isinstance(comm, dict) or comm.get("mode") not in ("none", "static", "auto"):
        raise ValueError("communication.mode must be none, static or auto")
    if set(comm) - {"mode", "physical_device_ids", "endpoint_directory", "connector_extra_config"}:
        raise ValueError("unknown communication fields")
    extra = comm.get("connector_extra_config", {})
    if not isinstance(extra, dict):
        raise ValueError("connector_extra_config must be an object")
    endpoint = extra.get("ascend_local_comm_res_path")
    if endpoint:
        target_path(endpoint)
    if comm["mode"] == "static":
        host_path(comm.get("endpoint_directory"))
        ids = comm.get("physical_device_ids")
        if not isinstance(ids, list) or not ids or any(type(n) is not int or n < 0 for n in ids) or len(set(ids)) != len(ids):
            raise ValueError("static mode requires distinct host physical_device_ids")
    requirements = plan.get("required_paths", [])
    if not isinstance(requirements, list):
        raise ValueError("required_paths must be a list")
    for requirement in requirements:
        if not isinstance(requirement, dict) or set(requirement) != {"path", "kind"} or requirement["kind"] not in ("file", "directory", "character_device"):
            raise ValueError("required_paths entries require path and kind")
        host_path(requirement["path"])
    commands = plan.get("required_commands", [])
    if not isinstance(commands, list) or any(not isinstance(c, str) or not c or "\0" in c for c in commands):
        raise ValueError("required_commands must be a list of executable names/paths")


def check_kind(path, kind):
    try:
        mode = Path(path).stat().st_mode
        return {"file": stat.S_ISREG, "directory": stat.S_ISDIR, "character_device": stat.S_ISCHR}[kind](mode)
    except OSError:
        return False


def preflight(plan, environ=None):
    validate_plan(plan)
    errors = []

    def fail(code, detail):
        errors.append({"code": code, "detail": detail})

    for mount in plan["mounts"]:
        if not check_kind(mount["source"], mount["kind"]):
            fail("mount_source", f"{mount['source']}: expected {mount['kind']} for {mount['target']}")
    for requirement in plan.get("required_paths", []):
        if not check_kind(requirement["path"], requirement["kind"]):
            fail("required_path", f"{requirement['path']}: expected {requirement['kind']}")
    for command in plan.get("required_commands", []):
        if shutil.which(command) is None:
            fail("command_missing", command)
    comm = plan["communication"]
    extra = comm.get("connector_extra_config", {})
    endpoint = extra.get("ascend_local_comm_res_path")
    env = dict(os.environ if environ is None else environ)
    env.update(plan.get("env", {}))
    if comm["mode"] == "static":
        source = Path(comm["endpoint_directory"])
        if not endpoint or not any(Path(m["source"]).resolve() == source.resolve() and m["target"] == endpoint and m["kind"] == "directory" for m in plan["mounts"]):
            fail("endpoint_mount", "static endpoint_directory must bind to ascend_local_comm_res_path")
        for device in comm["physical_device_ids"]:
            path = source / f"ub_endpoint_npu_{device}.json"
            if not check_kind(path, "file"):
                fail("endpoint_missing", str(path))
                continue
            try:
                value = load_json(path)
                if not isinstance(value, dict) or not value:
                    raise ValueError("endpoint JSON must be a nonempty object")
            except (OSError, ValueError) as exc:
                fail("endpoint_json", f"{path}: {exc}")
    elif comm["mode"] == "auto":
        if not plan.get("required_paths") or not plan.get("required_commands"):
            fail("auto_prerequisites", "declare the devices/paths and tools required by the selected auto-resource implementation")
        if endpoint:
            fail("auto_static_conflict", "remove ascend_local_comm_res_path before using auto resources")
        if env.get("ASCEND_GLOBAL_RESOURCE_CONFIG"):
            fail("auto_global_conflict", "clear the inherited static ASCEND_GLOBAL_RESOURCE_CONFIG")
        try:
            value = json.loads(plan.get("env", {}).get("ASCEND_LOCAL_COMM_RES", ""))
            if not isinstance(value, dict) or set(value) != {"version"} or not isinstance(value["version"], str) or not value["version"]:
                raise ValueError("auto resource JSON must explicitly contain only the supported version")
        except ValueError as exc:
            fail("auto_resource_config", str(exc))
    elif endpoint:
        fail("undeclared_static_mode", "ascend_local_comm_res_path requires static communication mode")
    return {"node": plan["node"], "container": plan["container"], "mode": comm["mode"], "ok": not errors, "errors": errors}


def docker_args(plan):
    """Render only declared bind mounts/env; existing tools own the lifecycle."""
    args = []
    for mount in plan["mounts"]:
        value = f"type=bind,src={mount['source']},dst={mount['target']}"
        if mount["read_only"]:
            value += ",readonly"
        args.extend(["--mount", value])
    for key, value in sorted(plan.get("env", {}).items()):
        args.extend(["--env", f"{key}={value}"])
    return args


def verify(plan, inspection, environ=None):
    report = preflight(plan, environ)
    if isinstance(inspection, list):
        if len(inspection) != 1:
            raise ValueError("inspect input must contain exactly one container")
        inspection = inspection[0]
    if not isinstance(inspection, dict) or not isinstance(inspection.get("Mounts"), list):
        raise ValueError("inspect input must contain the actual Docker Mounts list")
    if any(not isinstance(m, dict) for m in inspection["Mounts"]):
        raise ValueError("inspect Mounts entries must be objects")
    config = inspection.get("Config", {})
    if not isinstance(config, dict) or not isinstance(config.get("Env", []), list):
        raise ValueError("inspect Config.Env must be a list")
    errors = report["errors"]
    if inspection.get("Name") not in (plan["container"], "/" + plan["container"]):
        errors.append({"code": "container_mismatch", "detail": "inspect Name differs from plan"})
    mounts = inspection["Mounts"]
    for wanted in plan["mounts"]:
        actual = [m for m in mounts if m.get("Destination") == wanted["target"]]
        matches = len(actual) == 1 and actual[0].get("Type") == "bind" and isinstance(actual[0].get("Source"), str) and Path(actual[0]["Source"]).resolve() == Path(wanted["source"]).resolve() and type(actual[0].get("RW")) is bool and actual[0]["RW"] == (not wanted["read_only"])
        if not matches:
            errors.append({"code": "mount_mismatch", "detail": f"{wanted['target']}: expected bind from {wanted['source']}, read_only={wanted['read_only']}"})
    actual_env = dict(item.split("=", 1) for item in config.get("Env", []) if isinstance(item, str) and "=" in item)
    for key, value in plan.get("env", {}).items():
        if actual_env.get(key) != value:
            errors.append({"code": "env_mismatch", "detail": key})
    if plan["communication"]["mode"] == "auto" and actual_env.get("ASCEND_GLOBAL_RESOURCE_CONFIG"):
        errors.append({"code": "auto_global_conflict", "detail": "container image still defines ASCEND_GLOBAL_RESOURCE_CONFIG"})
    report["ok"] = not errors
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("preflight", "docker-args", "verify"))
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--inspect", type=Path, help="target container's docker inspect JSON; required for verify")
    args = parser.parse_args(argv)
    try:
        plan = load_json(args.plan)
        if args.phase == "verify":
            if args.inspect is None:
                raise ValueError("verify requires --inspect")
            report = verify(plan, load_json(args.inspect))
        else:
            report = preflight(plan)
        if args.phase == "docker-args" and report["ok"]:
            print(json.dumps(docker_args(plan), ensure_ascii=False))
        else:
            print(json.dumps(report, ensure_ascii=False), file=sys.stderr if args.phase == "docker-args" else sys.stdout)
        return 0 if report["ok"] else 1
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr if args.phase == "docker-args" else sys.stdout)
        return 2


if __name__ == "__main__":
    sys.exit(main())
