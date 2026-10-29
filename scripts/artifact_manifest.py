#!/usr/bin/env python3
"""Read-only artifact snapshots, comparisons and wheel installation byte checks.

Standard library only, Python >=3.10. Hashes raw bytes; never imports target
packages, extracts archives, installs packages or restores build caches.
See docs/tools/runtime-tools.md for scope, CLI and interpretation.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import importlib.machinery
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile


def digest(handle):
    result = hashlib.sha256()
    while chunk := handle.read(1024 * 1024):
        result.update(chunk)
    return result.hexdigest()


def pairs(values):
    result = {}
    for value in values:
        label, separator, path = value.partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z0-9_-]+", label) or not path or label in result:
            raise ValueError("paths must be unique LABEL=PATH pairs")
        result[label] = Path(path).absolute()
    return result


def safe_relative(name):
    path = PurePosixPath(name)
    if not name or "\\" in name or "\0" in name or path.is_absolute() or any(
        part in {"", ".", ".."} or ":" in part for part in name.split("/")
    ):
        raise ValueError(f"unsafe relative path: {name!r}")
    return path


def file_record(path):
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("not a regular file")
    with path.open("rb") as handle:
        sha = digest(handle)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError("file changed while hashing")
    return {"type": "file", "size": after.st_size, "sha256": sha,
            "mode": stat.S_IMODE(after.st_mode)}


def tree_record(root, excludes):
    records, errors = {}, []
    if root.is_symlink() or not root.is_dir():
        return {"path": str(root), "entries": {}, "errors": ["root must be an existing non-symlink directory"]}

    def walk(directory, prefix=""):
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda item: item.name)
        except OSError as exc:
            errors.append({"path": prefix or ".", "error": str(exc)})
            return
        for entry in entries:
            relative = f"{prefix}/{entry.name}" if prefix else entry.name
            if any(fnmatch.fnmatchcase(relative, pattern) for pattern in excludes):
                continue
            try:
                safe_relative(relative)
                path = Path(entry.path)
                if entry.is_symlink():
                    records[relative] = {"type": "symlink", "target": os.readlink(path)}
                elif entry.is_dir(follow_symlinks=False):
                    records[relative] = {"type": "directory", "mode": stat.S_IMODE(entry.stat().st_mode)}
                    walk(path, relative)
                else:
                    records[relative] = file_record(path)
            except (OSError, ValueError) as exc:
                errors.append({"path": relative, "error": str(exc)})
    walk(root)
    return {"path": str(root), "entries": records, "errors": errors}


def wheel_record(path):
    result = {"path": str(path), "entries": {}, "errors": []}
    try:
        result.update(file_record(path))
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                # ZipInfo may normalize backslashes on Windows; validate the
                # original archive spelling before using the normalized name.
                safe_relative(member.orig_filename.rstrip("/") if member.is_dir() else member.orig_filename)
                safe_relative(member.filename.rstrip("/") if member.is_dir() else member.filename)
                if member.is_dir():
                    continue
                if member.filename in result["entries"]:
                    raise ValueError("duplicate wheel member")
                if stat.S_ISLNK(member.external_attr >> 16):
                    raise ValueError("symlink wheel member unsupported")
                with archive.open(member) as handle:
                    sha = digest(handle)
                result["entries"][member.filename] = {"type": "file", "size": member.file_size, "sha256": sha}
            if not result["entries"]:
                raise ValueError("wheel has no file members")
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        result["errors"].append(str(exc))
    return result


def distribution_record(name):
    """Record current interpreter metadata without importing target modules."""
    normalized = re.sub(r"[-_.]+", "-", name).lower()
    result = {"name": normalized, "errors": [], "entries": {}}
    try:
        dist = importlib.metadata.distribution(name)
        result.update(version=dist.version, installation_root=str(Path(dist.locate_file("")).absolute()))
        direct_url = dist.read_text("direct_url.json")
        # Editable source location only; omit possible authenticated URL details.
        if direct_url:
            data = json.loads(direct_url)
            result["editable"] = bool(data.get("dir_info", {}).get("editable"))
        top_level = (dist.read_text("top_level.txt") or "").splitlines()
        origins = {}
        for module in top_level:
            if re.fullmatch(r"[A-Za-z_]\w*", module):
                spec = importlib.machinery.PathFinder.find_spec(module)
                origins[module] = None if spec is None else {
                    "origin": spec.origin, "search_locations": list(spec.submodule_search_locations or [])}
        result["module_locations"] = origins
        if dist.files is None:
            raise ValueError("distribution file list unavailable (editable packages may require explicit source root)")
        for item in dist.files:
            # Metadata paths may legitimately traverse to installed scripts.
            relative = str(item).replace("\\", "/")
            path = Path(dist.locate_file(item))
            if path.is_symlink():
                result["entries"][relative] = {"type": "symlink", "target": os.readlink(path)}
            elif path.is_file():
                result["entries"][relative] = file_record(path)
            else:
                result["errors"].append({"path": relative, "error": "missing or non-file distribution entry"})
    except (importlib.metadata.PackageNotFoundError, OSError, ValueError) as exc:
        result["errors"].append(str(exc))
    return result


def snapshot(roots, wheels, distributions, excludes):
    packages = {}
    for name in distributions:
        record = distribution_record(name)
        if record["name"] in packages:
            raise ValueError("duplicate normalized distribution name")
        packages[record["name"]] = record
    result = {"schema_version": 1, "kind": "artifact_manifest",
              "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "interpreter": sys.executable, "python_version": sys.version,
              "excludes": excludes, "roots": {k: tree_record(p, excludes) for k, p in roots.items()},
              "wheels": {k: wheel_record(p) for k, p in wheels.items()}, "distributions": packages}
    result["status"] = "incomplete" if any(
        item["errors"] for section in ("roots", "wheels", "distributions") for item in result[section].values()
    ) else "complete"
    return result


def compare(expected, actual, check_modes=False, check_origins=False):
    for manifest in (expected, actual):
        if manifest.get("kind") != "artifact_manifest" or manifest.get("schema_version") != 1:
            raise ValueError("unsupported manifest schema")
        for section in ("roots", "wheels", "distributions"):
            if not isinstance(manifest.get(section), dict):
                raise ValueError("invalid manifest sections")
    differences = []
    if expected.get("excludes") != actual.get("excludes"):
        differences.append({"section": "excludes", "reason": "coverage differs"})
    for section in ("roots", "wheels", "distributions"):
        left, right = expected[section], actual[section]
        for label in sorted(left.keys() | right.keys()):
            if label not in left or label not in right:
                differences.append({"section": section, "label": label, "reason": "missing" if label not in right else "extra"})
                continue
            a, b = left[label], right[label]
            if section == "distributions" and a.get("version") != b.get("version"):
                differences.append({"section": section, "label": label, "reason": "version differs"})
            if check_origins and any(a.get(k) != b.get(k) for k in ("path", "installation_root", "module_locations")):
                differences.append({"section": section, "label": label, "reason": "origin differs"})
            if section == "wheels" and a.get("sha256") != b.get("sha256"):
                differences.append({"section": section, "label": label, "reason": "wheel archive differs"})
            for path in sorted(a["entries"].keys() | b["entries"].keys()):
                if path not in a["entries"] or path not in b["entries"]:
                    reason = "missing" if path not in b["entries"] else "extra"
                else:
                    x, y = a["entries"][path], b["entries"][path]
                    keys = ("type", "sha256", "size", "target") + (("mode",) if check_modes else ())
                    if all(x.get(k) == y.get(k) for k in keys):
                        continue
                    reason = "content or type differs"
                differences.append({"section": section, "label": label, "path": path, "reason": reason})
    incomplete = any(m.get("status") != "complete" or any(
        r.get("errors") for section in ("roots", "wheels", "distributions") for r in m[section].values()
    ) for m in (expected, actual))
    return {"schema_version": 1, "kind": "artifact_comparison",
            "status": "inconclusive" if incomplete else "different" if differences else "matched",
            "check_modes": check_modes, "check_origins": check_origins, "differences": differences,
            "limits": "File identity only; no runtime/ABI/model/PD compatibility claim."}


def wheel_installation(path, schemes):
    wheel = wheel_record(path)
    result = {"schema_version": 1, "kind": "wheel_installation_check", "wheel": str(path),
              "schemes": {k: str(v) for k, v in schemes.items()}, "checked_files": 0,
              "excluded": [], "differences": [], "errors": list(wheel["errors"])}
    for name, expected in wheel["entries"].items():
        parts = safe_relative(name).parts
        if parts[0].endswith(".dist-info") and parts[-1] in {"RECORD", "RECORD.jws", "RECORD.p7s"}:
            result["excluded"].append({"path": name, "reason": "installer-generated RECORD/signature"})
            continue
        if parts[0].endswith(".data"):
            if len(parts) < 3:
                result["errors"].append(f"invalid wheel data path: {name}")
                continue
            scheme, relative = parts[1], PurePosixPath(*parts[2:])
        else:
            scheme, relative = "site", PurePosixPath(*parts)
        if scheme not in schemes:
            result["errors"].append(f"missing installation scheme {scheme}: {name}")
            continue
        root = schemes[scheme].resolve()
        destination = root.joinpath(*relative.parts)
        # Resolve links before opening; reject any path escaping the chosen scheme.
        if not destination.resolve().is_relative_to(root):
            result["errors"].append(f"destination escapes installation root: {name}")
            continue
        result["checked_files"] += 1
        try:
            actual = file_record(destination)
            if actual["sha256"] != expected["sha256"] or actual["size"] != expected["size"]:
                result["differences"].append({"path": name, "installed_path": str(destination), "reason": "bytes differ"})
        except (OSError, ValueError) as exc:
            result["differences"].append({"path": name, "installed_path": str(destination), "reason": str(exc)})
    if not result["checked_files"]:
        result["errors"].append("no wheel members available for installation byte verification")
    result["status"] = "inconclusive" if result["errors"] else "different" if result["differences"] else "matched"
    result["limits"] = "Wheel-covered bytes only; extra installed files and runtime compatibility are not checked."
    return result


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("snapshot", help="record explicit trees/wheels/installed distributions")
    capture.add_argument("--root", action="append", default=[], metavar="LABEL=PATH")
    capture.add_argument("--wheel", action="append", default=[], metavar="LABEL=PATH")
    capture.add_argument("--distribution", action="append", default=[])
    capture.add_argument("--exclude", action="append", default=[], help="relative POSIX path glob, tree roots only")
    capture.add_argument("--output", type=Path, required=True)
    comparison = commands.add_parser("compare", help="compare two saved snapshots")
    comparison.add_argument("--expected", type=Path, required=True)
    comparison.add_argument("--actual", type=Path, required=True)
    comparison.add_argument("--check-modes", action="store_true")
    comparison.add_argument("--check-origins", action="store_true")
    comparison.add_argument("--output", type=Path, required=True)
    installed = commands.add_parser("verify-wheel", help="compare wheel members with explicit installation schemes")
    installed.add_argument("--wheel", type=Path, required=True)
    installed.add_argument("--site-root", type=Path, required=True)
    installed.add_argument("--scheme", action="append", default=[], metavar="NAME=PATH")
    installed.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "snapshot":
            if not (args.root or args.wheel or args.distribution):
                raise ValueError("specify at least one root, wheel or distribution")
            result = snapshot(pairs(args.root), pairs(args.wheel), args.distribution, args.exclude)
        elif args.command == "compare":
            result = compare(json.loads(args.expected.read_text(encoding="utf-8")),
                             json.loads(args.actual.read_text(encoding="utf-8")), args.check_modes, args.check_origins)
        else:
            schemes = {"site": args.site_root.absolute(), "purelib": args.site_root.absolute(), "platlib": args.site_root.absolute()}
            overrides = pairs(args.scheme)
            if set(overrides) - {"site", "purelib", "platlib", "scripts", "headers", "data"}:
                raise ValueError("unknown installation scheme")
            schemes.update(overrides)
            result = wheel_installation(args.wheel.absolute(), schemes)
        write_new(args.output, result)
        print(json.dumps({"status": result["status"], "report": str(args.output.resolve())}))
        return 0 if result["status"] in {"complete", "matched"} else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"manifest configuration/read error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
