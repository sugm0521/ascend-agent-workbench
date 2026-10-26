"""Local helper contract tests; all logs/topologies are synthetic, no remote calls."""

import hashlib
import importlib.util
import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".agents/skills/ascend-hccl-traffic-test/scripts/hccl_traffic.py"
SPEC = importlib.util.spec_from_file_location("hccl_traffic", HELPER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HcclTrafficTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(HELPER), *args],
                              capture_output=True, text=True, encoding="utf-8")

    def plan(self, *extra):
        return self.cli("plan", "--work-dir", "/task/work", "--hccl-dir", "/task/hccl",
                        "--mpirun", "/mpi/bin/mpirun", "--host", "node-a:8",
                        "--p-value", "8", *extra)

    def summary(self, payload, code):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "synthetic.log"
            path.write_bytes(payload)
            result = MODULE.summarize(path, code)
            self.assertEqual(result["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(result["bytes"], len(payload))
            self.assertFalse(result["coverage_verified"])
            return result

    def test_two_host_plan_preserves_modes_and_counts(self):
        result = self.plan("--host", "node-b:8", "--np", "16")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["hostfile"]["content"], "node-a:8\nnode-b:8\n")
        self.assertEqual(data["hostfile"]["path"], "/task/hccl/hostfile16")
        self.assertEqual([c["algorithm"] for c in data["commands"]], ["ccu_ms", "aicpu_ts"])
        self.assertEqual(data["commands"][0]["argv"], [
            "/mpi/bin/mpirun", "-hostfile", "hostfile16", "-n", "16",
            "./bin/alltoallvc_test", "-b", "8", "-e", "4G", "-f", "2",
            "-d", "int16", "-p", "8", "-a", "ccu_ms"])
        self.assertFalse(data["executed"])
        self.assertFalse(data["environment_verified"])

    def test_single_node_bounded_fork_plan(self):
        result = self.plan("--single-node", "--end", "64M", "--iters", "10",
                           "--warmup-iters", "3", "--timeout-seconds", "120")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIsNone(data["hostfile"])
        self.assertFalse(data["executed"])
        self.assertFalse(data["resource_admission_verified"])
        self.assertTrue(data["must_run_on_declared_host"])
        argv = data["commands"][0]["argv"]
        self.assertEqual(argv[:10], ["timeout", "-k", "10s", "120s", "/mpi/bin/mpirun",
                                    "-launcher", "fork", "-n", "8", "./bin/alltoallvc_test"])
        self.assertNotIn("-hostfile", argv)
        self.assertEqual(argv[-4:], ["-n", "10", "-w", "3"])
        inner = shlex.split(data["commands"][0]["shell"])[2]
        self.assertEqual(shlex.split(inner.split(" && exec ")[1]), argv)

    def test_single_node_rejects_other_hosts_or_hostfile(self):
        for extra in [("--host", "node-b:8"), ("--hostfile", "hostfile8")]:
            result = self.plan("--single-node", *extra)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_initialization_failure_with_zero_exit_is_failed(self):
        # Exact failure format observed on the real single-node run.
        data = self.summary(b"Process 0 HcclGetRootInfo failed, notify other process to exit\n"
                            b"Process 2 received invalid data from root process 0\n", 0)
        self.assertEqual(data["verdict"], "failed")
        self.assertEqual(data["recognized_initialization_failures"], 1)
        self.assertEqual(data["first_failure_hint"]["layer"], "hccl_initialization")
        self.assertEqual(data["observed_checks"]["success"], 0)

    def test_hccl_interface_error_with_zero_exit_is_failed(self):
        line = b"hccl interface return err ./common/src/hccl_test_common.cc:901, retcode: 4 \n"
        data = self.summary(line * 8, 0)
        self.assertEqual(data["verdict"], "failed")
        self.assertEqual(data["recognized_interface_failures"], 8)
        self.assertEqual(data["first_failure_hint"]["layer"], "hccl_interface")
        data = self.summary(line.replace(b"retcode: 4", b"retcode: 0"), 0)
        self.assertEqual(data["recognized_interface_failures"], 0)
        self.assertEqual(data["verdict"], "inconclusive")

    def test_slots_must_match_verified_p_and_single_mode_is_supported(self):
        for extra in [("--host", "node-b:4"), ("--p-value", "4")]:
            self.assertEqual(self.plan(*extra).returncode, 2)
        result = self.plan("--algorithm", "aicpu_ts")
        data = json.loads(result.stdout)
        self.assertEqual(data["total_ranks"], 8)
        self.assertEqual(data["p_value"], 8)
        self.assertEqual(len(data["commands"]), 1)

    def test_reject_invalid_hosts_slots_duplicates_and_rank_mismatch(self):
        for extra in [("--host", "NODE-A.:8"), ("--host", "node;touch:8"),
                      ("--host", "node-b:0"), ("--host", "::1:8"),
                      ("--host", "node-b:8\n"), ("--np", "9")]:
            with self.subTest(extra=extra):
                result = self.plan(*extra)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_reject_bad_paths_profiles_and_names(self):
        for extra in [("--work-dir", "/"), ("--work-dir", "relative"),
                      ("--hccl-dir", "/bad\npath"), ("--hostfile", "hostfile/other"),
                      ("--begin", "8;id"), ("--begin", "8G", "--end", "4G"),
                      ("--factor", "1"), ("--p-value", "0")]:
            with self.subTest(extra=extra):
                result = self.plan(*extra)
                self.assertEqual(result.returncode, 2, result.stdout)

    def test_p_is_required_and_unsupported_mode_rejected(self):
        args = ("plan", "--work-dir", "/task", "--hccl-dir", "/task/hccl",
                "--mpirun", "/mpi/mpirun", "--host", "node-a:8")
        self.assertEqual(self.cli(*args).returncode, 2)
        self.assertEqual(self.plan("--algorithm", "other").returncode, 2)

    def test_shell_quotes_special_paths_as_single_tokens(self):
        work, hccl, mpi = "/work with space;$(id)'", "/hccl ' dir", "/mpi;$(id)/mpirun"
        result = self.plan("--work-dir", work, "--hccl-dir", hccl, "--mpirun", mpi)
        command = json.loads(result.stdout)["commands"][0]
        outer = shlex.split(command["shell"])
        self.assertEqual(outer[:2], ["bash", "-c"])
        self.assertEqual(len(outer), 3)
        inner = shlex.split(outer[2])
        self.assertEqual(inner[:8], ["source", work + "/env.sh", "&&", "cd", "--", hccl, "&&", "exec"])
        self.assertEqual(inner[8:], command["argv"])

    def test_plan_does_not_execute_or_write_even_with_existing_files(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "env.sh"
            path.write_text("this must never be executed", encoding="utf-8")
            before = {p.name: p.read_bytes() for p in Path(temp).iterdir()}
            result = self.plan("--work-dir", "/" + Path(temp).as_posix().lstrip("/"))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, {p.name: p.read_bytes() for p in Path(temp).iterdir()})

    def test_success_is_only_observed_not_complete_coverage(self):
        result = self.summary(b"size 8 check_result: success\n", 0)
        self.assertEqual(result["verdict"], "passed_observed")
        self.assertEqual(result["observed_checks"], {"success": 1, "failure": 0, "unknown": 0})

    def test_ansi_and_multiple_checks_are_counted(self):
        result = self.summary(b"\x1b[32mcheck_result: SUCCESS\x1b[0m check_result=success\n", 0)
        self.assertEqual(result["observed_checks"]["success"], 2)
        self.assertEqual(result["verdict"], "passed_observed")

    def test_mixed_failure_and_nonzero_exit_cannot_pass(self):
        for payload, code in [(b"check_result: success\ncheck_result: failed\n", 0),
                              (b"check_result: success\n", 255)]:
            result = self.summary(payload, code)
            self.assertEqual(result["verdict"], "failed")

    def test_empty_missing_unknown_encoding_and_exit_are_inconclusive(self):
        for payload, code in [(b"", 0), (b"completed\n", 0),
                              (b"check_result: success\n", None),
                              (b"check_result: N/A\n", 0),
                              (b"\xff check_result: success\n", 0)]:
            with self.subTest(payload=payload, code=code):
                self.assertEqual(self.summary(payload, code)["verdict"], "inconclusive")

    def test_truncated_check_value_cannot_pass(self):
        result = self.summary(b"check_result: success\ncheck_result:\n", 0)
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertEqual(result["observed_checks"]["unknown"], 1)

    def test_first_error_hint_is_not_overwritten_by_hydra(self):
        result = self.summary(b"Host key verification failed.\nHYDU_sock_write Bad file descriptor\n", 255)
        self.assertEqual(result["first_failure_hint"]["layer"], "ssh_or_hydra")
        self.assertEqual(result["first_failure_hint"]["line"], 1)

    def test_error_hint_with_zero_exit_stays_inconclusive(self):
        result = self.summary(b"error while loading shared libraries: libmpi.so\ncheck_result: success\n", 0)
        self.assertEqual(result["verdict"], "inconclusive")

    def test_large_log_has_bounded_summary_and_preserves_digest(self):
        result = self.summary(b"check_result: N/A\n" * 25000, 0)
        self.assertEqual(result["observed_checks"]["unknown"], 25000)
        self.assertEqual(len(result["non_success_examples"]), 10)
        self.assertLess(len(json.dumps(result)), 4000)

    def test_summary_cli_exit_codes_and_missing_log(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "synthetic.log"
            for payload, expected in [("check_result: success\n", 0),
                                      ("check_result: fail\n", 1), ("", 2)]:
                path.write_text(payload, encoding="utf-8")
                result = self.cli("summarize", "--log", str(path), "--exit-code", "0")
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(json.loads(result.stdout)["exit_code"], 0)
            self.assertEqual(self.cli("summarize", "--log", str(path) + ".absent").returncode, 2)

    def test_cann_table_observations_preserve_sizes_and_performance(self):
        payload = b"data_size: | avg_time: | alg_bandwidth: | check_result:\n8 | 12.50 | 0.01234 | success\n16 | 13.25 | 0.02345 | success\n"
        data = self.summary(payload, 0)
        self.assertEqual(data["verdict"], "passed_observed")
        self.assertEqual(data["observed_checks"]["success"], 2)
        self.assertEqual([row["data_size_bytes"] for row in data["table_rows"]], [8, 16])
        self.assertEqual(data["table_rows"][0]["algorithm_bandwidth_GBytes_s"], "0.01234")

    def test_non_root_rank_failure_overrides_root_table_success(self):
        payload = b"data_size: | avg_time: | alg_bandwidth: | check_result:\n8 | 12.50 | 0.01234 | success\nlocal rank_id 3, check result failed, 8 | 12.50 | 0.01234 | failed\n"
        data = self.summary(payload, 0)
        self.assertEqual(data["verdict"], "failed")
        self.assertEqual(data["observed_checks"]["failure"], 1)

    def test_cann_disabled_checks_or_broken_row_are_inconclusive(self):
        header = b"data_size: | avg_time: | alg_bandwidth: | check_result:\n"
        for tail in [b"8 | 12.50 | 0.01234 | NULL\n", b"8 | 12.50 | 0.01234 | success\n16 | 1.0 |\n"]:
            self.assertEqual(self.summary(header + tail, 0)["verdict"], "inconclusive")

    def test_table_like_rows_without_cann_header_do_not_pass(self):
        data = self.summary(b"8 | 12.50 | 0.01234 | success\n", 0)
        self.assertEqual(data["verdict"], "inconclusive")

    def test_cann_failed_table_row_is_failed(self):
        payload = b"data_size: | avg_time: | alg_bandwidth: | check_result:\n8 | 12.50 | 0.01234 | failed\n"
        self.assertEqual(self.summary(payload, 0)["verdict"], "failed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
