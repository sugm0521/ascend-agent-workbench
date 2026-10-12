#!/usr/bin/env python3
"""Run trusted Python import/probe cases in children; require normal final exit.

Standard library only, Python >=3.10. No remote access or environment repair.
See docs/runtime-tools.md for the JSON contract and evidence limits.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time


MARKER = "__IMPORT_PROBE_METADATA__="
CHILD = r'''
import importlib, json, os, sys
case = json.loads(sys.argv[1])
origins = {}
for name in case.get("imports", []):
    module = importlib.import_module(name)
    origins[name] = getattr(module, "__file__", None)
if case.get("code"):
    exec(compile(case["code"], "<trusted-probe>", "exec"), {"__name__": "__main__"})
libraries = []
if sys.platform.startswith("linux"):
    with open("/proc/self/maps", encoding="utf-8", errors="replace") as handle:
        libraries = sorted({line.rstrip().split(maxsplit=5)[-1]
                            for line in handle if len(line.split(maxsplit=5)) == 6
                            and ".so" in line.split(maxsplit=5)[-1]})
# Probe code or native libraries may leave stdout without a trailing newline.
print("\n__IMPORT_PROBE_METADATA__=" + json.dumps({"completed": True,
      "python_executable": sys.executable, "python_version": sys.version,
      "module_origins": origins, "loaded_libraries": libraries[:128],
      "loaded_libraries_truncated": len(libraries) > 128,
      "loaded_libraries_available": sys.platform.startswith("linux")}), flush=True)
'''


class TailCapture:
    """Drain pipes continuously while retaining at most limit bytes in memory."""

    def __init__(self, limit: int):
        self.limit = limit
        self.data = bytearray()
        self.total = 0

    def drain(self, pipe):
        try:
            while chunk := pipe.read(8192):
                self.total += len(chunk)
                self.data.extend(chunk)
                if len(self.data) > self.limit:
                    del self.data[:-self.limit]
        finally:
            pipe.close()


def validate_config(config):
    cases = config.get("cases") if isinstance(config, dict) else None
    if not isinstance(cases, list) or not 1 <= len(cases) <= 128:
        raise ValueError("cases must contain 1..128 objects")
    names = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) - {"name", "imports", "code", "env", "timeout_seconds"}:
            raise ValueError("invalid case keys")
        name = case.get("name", "")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name) or name in names:
            raise ValueError("case names must be unique safe identifiers")
        names.add(name)
        imports = case.get("imports", [])
        if not isinstance(imports, list) or len(imports) > 64 or any(
            not isinstance(n, str) or not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", n)
            for n in imports
        ):
            raise ValueError("imports must be a list of module names")
        code = case.get("code", "")
        if not isinstance(code, str) or not (imports or code):
            raise ValueError("each case requires imports or trusted code")
        env = case.get("env", {})
        if not isinstance(env, dict) or any(
            not isinstance(k, str) or not k or "=" in k or "\0" in k
            or (v is not None and (not isinstance(v, str) or "\0" in v)) for k, v in env.items()
        ):
            raise ValueError("env maps names to strings or null (unset)")
        timeout = case.get("timeout_seconds", 60)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout_seconds must be positive and finite")
    return cases


def terminate_group(process):
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        # The PID belongs to this probe, never a name-based/shared process kill.
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, check=False)
        if process.poll() is None:
            process.kill()


def run_case(case, python, directory, limit):
    started = time.monotonic()
    env = os.environ.copy()
    for key, value in case.get("env", {}).items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    result = {"name": case["name"], "imports": case.get("imports", []),
              "environment_override_names": sorted(case.get("env", {})),
              "timeout_seconds": case.get("timeout_seconds", 60)}
    out, err = TailCapture(limit), TailCapture(limit)
    try:
        payload = {k: case[k] for k in ("imports", "code") if k in case}
        process = subprocess.Popen([python, "-u", "-c", CHILD, json.dumps(payload)],
                                   env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=(os.name == "posix"))
    except OSError as exc:
        return {**result, "status": "launch_error", "error": str(exc), "exit_code": None}
    threads = [threading.Thread(target=capture.drain, args=(pipe,), daemon=True)
               for capture, pipe in ((out, process.stdout), (err, process.stderr))]
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        process.wait(timeout=result["timeout_seconds"])
    except subprocess.TimeoutExpired:
        timed_out = True
        terminate_group(process)
        process.wait(timeout=10)
    for thread in threads:
        thread.join(timeout=2)
    streams_complete = all(not thread.is_alive() for thread in threads)
    if not streams_complete:
        # A descendant retained a pipe after the direct child exited.
        terminate_group(process)
        for thread in threads:
            thread.join(timeout=2)
        streams_complete = all(not thread.is_alive() for thread in threads)
    stdout = bytes(out.data).decode("utf-8", errors="replace")
    metadata = None
    for line in stdout.split("\n"):
        if line.startswith(MARKER):
            try:
                candidate = json.loads(line[len(MARKER):])
                if isinstance(candidate, dict) and candidate.get("completed") is True:
                    metadata = candidate
            except json.JSONDecodeError:
                pass
    rc = process.returncode
    status = ("timeout" if timed_out else "signal" if rc < 0 and os.name == "posix" else "exit_failure" if rc != 0
              else "inconclusive" if not metadata or not streams_complete else "passed")
    logs = {}
    for label, capture in (("stdout", out), ("stderr", err)):
        path = directory / f"{case['name']}.{label}.log"
        path.write_bytes(bytes(capture.data))
        logs[label] = {"path": str(path.resolve()), "observed_bytes": capture.total,
                       "retained_bytes": len(capture.data), "truncated": capture.total > len(capture.data)}
    signal_number = -rc if rc < 0 and os.name == "posix" else None
    return {**result, "status": status, "exit_code": rc, "signal": signal_number,
            "signal_name": signal.Signals(signal_number).name if signal_number else None,
            "metadata": metadata, "streams_complete": streams_complete, "logs": logs,
            "elapsed_seconds": round(time.monotonic() - started, 3)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True, help="new directory; existing directories are refused")
    parser.add_argument("--python", default=sys.executable, help="interpreter in the environment being checked")
    parser.add_argument("--log-bytes", type=int, default=32768, help="retained tail bytes per stream per case")
    args = parser.parse_args(argv)
    try:
        if not 1024 <= args.log_bytes <= 262144:
            raise ValueError("log-bytes must be 1024..262144")
        if args.config.stat().st_size > 1000000:
            raise ValueError("config exceeds 1MB")
        cases = validate_config(json.loads(args.config.read_text(encoding="utf-8")))
        args.output_dir.mkdir(parents=True, exist_ok=False)
        report = {"schema_version": 1, "kind": "native_import_probe",
                  "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "python_requested": args.python, "platform": sys.platform, "cases": []}
        for case in cases:
            report["cases"].append(run_case(case, args.python, args.output_dir, args.log_bytes))
            # Checkpoint after each case; report.status becomes final only below.
            write_report(args.output_dir / "report.json", {**report, "status": "running"})
        report["status"] = "passed" if all(c["status"] == "passed" for c in report["cases"]) else "failed"
        write_report(args.output_dir / "report.json", report)
        print(json.dumps({"status": report["status"], "report": str((args.output_dir / 'report.json').resolve())}))
        return 0 if report["status"] == "passed" else 1
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"probe configuration/execution error: {exc}", file=sys.stderr)
        return 2


def write_report(path, report):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


if __name__ == "__main__":
    raise SystemExit(main())
