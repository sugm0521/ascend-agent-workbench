#!/usr/bin/env python3
"""Generate a read-only HCCL plan or summarize local logs; never execute remotely."""

import argparse
import hashlib
import json
import posixpath
import re
import shlex
from pathlib import Path


ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
CHECK = re.compile(r"\bcheck_result\s*[:=]\s*([^\s,;]+)", re.I)
CHECK_LABEL = re.compile(r"\bcheck_result\s*[:=]", re.I)
HOST = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SIZE = re.compile(r"([1-9][0-9]*)([KMG]?)\Z", re.I)
FAIL_VALUES = {"fail", "failed", "failure", "error", "false"}
NUMBER = r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
TABLE_ROW = re.compile(r"\s*([0-9]+)\s*\|\s*(" + NUMBER + r")\s*\|\s*(" + NUMBER + r")\s*\|\s*([^\s|]+)\s*\Z")
RANK_FAILURE = re.compile(r"\blocal rank_id\s+[0-9]+,\s*check result failed\b", re.I)
INIT_FAILURE = re.compile(r"\bProcess\s+[0-9]+\s+HcclGetRootInfo failed\b", re.I)
INTERFACE_FAILURE = re.compile(r"\bhccl interface return err\s+.+:[0-9]+,\s*retcode:\s*(-?[0-9]+)\b", re.I)
HINTS = (
    ("ssh_or_hydra", re.compile(
        r"Permission denied \(publickey|Host key verification failed|"
        r"ssh: connect to host|HYDU_sock_write|execvp error on file ssh", re.I)),
    ("process_startup", re.compile(
        r"error while loading shared libraries|execvp error|"
        r"No such file or directory|command not found", re.I)),
    ("hccl_initialization", re.compile(
        r"HCCL.*(?:init|initialize).*(?:fail|error)|"
        r"(?:fail|error).*HCCL.*(?:init|initialize)", re.I)),
)


def positive(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def absolute_path(value):
    if not value.startswith("/") or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("remote paths must be absolute POSIX paths without control characters")
    return posixpath.normpath(value)


def size_bytes(value):
    match = SIZE.fullmatch(value)
    if not match:
        raise ValueError("size must be a positive integer with optional K/M/G suffix")
    return int(match[1]) * {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3}[match[2].upper()]


def plan(args):
    work = absolute_path(args.work_dir)
    hccl = absolute_path(args.hccl_dir)
    mpirun = absolute_path(args.mpirun)
    if work == "/":
        raise ValueError("work directory cannot be /")
    hosts = []
    seen = set()
    for spec in args.host:
        parts = spec.split(":")
        if len(parts) != 2 or not HOST.fullmatch(parts[0]) or not re.fullmatch(r"[1-9][0-9]*", parts[1]):
            raise ValueError("host must be an IPv4 address or hostname followed by :SLOTS")
        host, slots = parts[0], int(parts[1])
        canonical = host.lower().rstrip(".")
        if canonical in seen:
            raise ValueError("duplicate host: " + host)
        seen.add(canonical)
        hosts.append({"host": host, "slots": slots})
    total = sum(item["slots"] for item in hosts)
    if any(item["slots"] != args.p_value for item in hosts):
        raise ValueError("every host's slots must equal verified -p npus per node; heterogeneous mapping is unsupported")
    if args.np is not None and args.np != total:
        raise ValueError("--np must equal hostfile slot total " + str(total))
    if args.single_node and (len(hosts) != 1 or args.hostfile is not None):
        raise ValueError("--single-node requires exactly one host and no --hostfile")
    name = args.hostfile or "hostfile" + str(total)
    if not re.fullmatch(r"hostfile[A-Za-z0-9._-]*", name):
        raise ValueError("hostfile must be a basename beginning with hostfile")
    if size_bytes(args.begin) > size_bytes(args.end):
        raise ValueError("begin size cannot exceed end size")
    if args.factor < 2:
        raise ValueError("factor must be at least 2")
    environment = posixpath.join(work, "env.sh")
    algorithms = ["ccu_ms", "aicpu_ts"] if args.algorithm == "all" else [args.algorithm]
    commands = []
    for algorithm in algorithms:
        launch = ["-launcher", "fork"] if args.single_node else ["-hostfile", name]
        argv = [mpirun, *launch, "-n", str(total),
                "./bin/alltoallvc_test", "-b", args.begin, "-e", args.end,
                "-f", str(args.factor), "-d", "int16", "-p", str(args.p_value), "-a", algorithm]
        if args.iters is not None:
            argv += ["-n", str(args.iters)]
        if args.warmup_iters is not None:
            argv += ["-w", str(args.warmup_iters)]
        if args.timeout_seconds is not None:
            argv = ["timeout", "-k", "10s", str(args.timeout_seconds) + "s", *argv]
        inner = "source " + shlex.quote(environment) + " && cd -- " + shlex.quote(hccl)
        inner += " && exec " + shlex.join(argv)
        commands.append({"algorithm": algorithm, "argv": argv,
                         "shell": shlex.join(["bash", "-c", inner])})
    return {
        "schema_version": 1, "kind": "plan", "executed": False,
        "environment_verified": False, "work_dir": work, "env_file": environment,
        "hccl_dir": hccl, "mpirun": mpirun, "hosts": hosts, "total_ranks": total,
        "p_value": args.p_value,
        "launch_mode": "local_fork" if args.single_node else "hostfile",
        "must_run_on_declared_host": args.single_node,
        "resource_admission_verified": False,
        "timeout_seconds": args.timeout_seconds,
        "hostfile": None if args.single_node else {"path": posixpath.join(hccl, name),
                     "content": "".join(f"{item['host']}:{item['slots']}\n" for item in hosts)},
        "commands": commands,
    }


def summarize(log_path, exit_code):
    path = Path(log_path)
    digest = hashlib.sha256()
    success = failure = unknown = decode_errors = lines = size = init_failures = interface_failures = 0
    examples = []
    first_hint = None
    table_active = False
    table_rows = []
    table_row_count = 0
    with path.open("rb") as stream:
        for lines, raw in enumerate(stream, 1):
            digest.update(raw)
            size += len(raw)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                decode_errors += 1
                text = raw.decode("utf-8", errors="replace")
            text = ANSI.sub("", text)
            if INIT_FAILURE.search(text):
                init_failures += 1
                if first_hint is None:
                    first_hint = {"layer": "hccl_initialization", "line": lines,
                                  "text": text.strip()[:300]}
            interface_error = INTERFACE_FAILURE.search(text)
            if interface_error and int(interface_error[1]) != 0:
                interface_failures += 1
                if first_hint is None:
                    first_hint = {"layer": "hccl_interface", "line": lines,
                                  "text": text.strip()[:300]}
            cells = [cell.strip() for cell in text.strip().split("|")]
            header = len(cells) == 4 and re.fullmatch(r"check_result\s*:", cells[-1], re.I) is not None
            if header:
                table_active = True
            row = TABLE_ROW.fullmatch(text.strip()) if table_active else None
            table_value = None
            if row:
                table_row_count += 1
                table_value = row[4].lower().rstrip(".")
                if len(table_rows) < 64:
                    table_rows.append({"line": lines, "data_size_bytes": int(row[1]),
                                       "average_time_us": row[2], "algorithm_bandwidth_GBytes_s": row[3],
                                       "check_result": table_value[:100]})
            rank_failed = RANK_FAILURE.search(text) is not None
            matches = list(CHECK.finditer(text))
            incomplete = 0 if header else len(CHECK_LABEL.findall(text)) - len(matches)
            unknown += incomplete
            if incomplete and len(examples) < 10:
                examples.append({"line": lines, "value": "missing value"})
            values = [match[1].lower().rstrip(".") for match in matches]
            if table_value is not None:
                values.append(table_value)
            if rank_failed:
                values.append("failed")
            # A damaged numeric table row must not disappear from the observation.
            if table_active and not row and re.match(r"\s*[0-9]+\s*\|", text):
                values.append("unparsed_table_row")
            for value in values:
                if value == "success":
                    success += 1
                elif value in FAIL_VALUES:
                    failure += 1
                    if first_hint is None:
                        first_hint = {"layer": "correctness", "line": lines,
                                      "text": text.strip()[:300]}
                else:
                    unknown += 1
                if value != "success" and len(examples) < 10:
                    examples.append({"line": lines, "value": value[:100]})
            # The earliest suspicious line is evidence for investigation, not a root cause.
            if first_hint is None:
                for layer, pattern in HINTS:
                    if pattern.search(text):
                        first_hint = {"layer": layer, "line": lines, "text": text.strip()[:300]}
                        break
    if (exit_code is not None and exit_code != 0) or failure or init_failures or interface_failures:
        verdict = "failed"
    elif exit_code is None or not success or unknown or decode_errors or first_hint:
        verdict = "inconclusive"
    else:
        verdict = "passed_observed"
    return {
        "schema_version": 1, "kind": "log_summary", "log": str(path.resolve()),
        "sha256": digest.hexdigest(), "bytes": size, "lines": lines,
        "exit_code": exit_code, "verdict": verdict, "coverage_verified": False,
        "observed_checks": {"success": success, "failure": failure, "unknown": unknown},
        "recognized_initialization_failures": init_failures,
        "recognized_interface_failures": interface_failures,
        "utf8_decode_error_lines": decode_errors, "non_success_examples": examples,
        "table_row_count": table_row_count, "table_rows": table_rows,
        "table_rows_truncated": table_row_count > len(table_rows),
        "first_failure_hint": first_hint,
        "coverage_note": "Explicit checks and recognized CANN table/rank failure records are observed; verify expected sizes and all-rank completion separately.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    planning = commands.add_parser("plan", help="print JSON only; never execute or write files")
    planning.add_argument("--work-dir", required=True)
    planning.add_argument("--hccl-dir", required=True)
    planning.add_argument("--mpirun", required=True)
    planning.add_argument("--host", action="append", required=True, help="repeat HOST:SLOTS; IPv4/hostname only")
    planning.add_argument("--hostfile")
    planning.add_argument("--single-node", action="store_true", help="run on the one declared host using verified MPICH fork launcher; no hostfile/SSH")
    planning.add_argument("--np", type=positive)
    planning.add_argument("--p-value", type=positive, required=True, help="verified value for hccl_test -p; no card-count inference")
    planning.add_argument("--algorithm", choices=["all", "ccu_ms", "aicpu_ts"], default="all")
    planning.add_argument("--begin", default="8")
    planning.add_argument("--end", default="4G")
    planning.add_argument("--factor", type=positive, default=2)
    planning.add_argument("--iters", type=positive, help="verified hccl_test iteration count; omit to keep its default")
    planning.add_argument("--warmup-iters", type=positive, help="verified hccl_test warmup count; omit to keep its default")
    planning.add_argument("--timeout-seconds", type=positive, help="requires verified GNU timeout; includes 10s termination grace")
    analysis = commands.add_parser("summarize", help="stream a local log; does not verify workload coverage")
    analysis.add_argument("--log", required=True)
    analysis.add_argument("--exit-code", type=int, help="actual remote exit code; omit when unknown")
    args = parser.parse_args(argv)
    try:
        result = plan(args) if args.action == "plan" else summarize(args.log, args.exit_code)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return {"failed": 1, "inconclusive": 2}.get(result.get("verdict"), 0)


if __name__ == "__main__":
    raise SystemExit(main())
