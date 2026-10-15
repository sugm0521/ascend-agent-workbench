"""Observable behavior tests; real local subprocesses/files, no NPU or network."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


artifact = load_script("artifact_manifest")


class NativeProbeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def run_probe(self, cases, **options):
        config = self.directory / "config.json"
        config.write_text(json.dumps({"cases": cases}), encoding="utf-8")
        output = self.directory / "probe"
        command = [sys.executable, str(ROOT / "scripts/native_import_probe.py"),
                   "--config", str(config), "--output-dir", str(output)]
        for name, value in options.items():
            command.extend(["--" + name.replace("_", "-"), str(value)])
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        report = json.loads((output / "report.json").read_text(encoding="utf-8")) if (output / "report.json").exists() else None
        return result, report, output, command

    def test_normal_import_actual_origin_and_no_overwrite(self):
        result, report, output, command = self.run_probe([{"name": "normal", "imports": ["ssl", "hashlib"]}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "passed")
        metadata = report["cases"][0]["metadata"]
        self.assertTrue(Path(metadata["module_origins"]["ssl"]).is_file())
        self.assertTrue(Path(metadata["python_executable"]).is_file())
        self.assertEqual(metadata["loaded_libraries_available"], sys.platform.startswith("linux"))
        saved = (output / "report.json").read_bytes()
        rerun = subprocess.run(command, capture_output=True, timeout=10)
        self.assertEqual(rerun.returncode, 2)
        self.assertEqual((output / "report.json").read_bytes(), saved)

    def test_success_body_then_failure_during_exit(self):
        result, report, _, _ = self.run_probe([{
            "name": "exit", "code": "import atexit, os; atexit.register(lambda: os._exit(23)); print('body done')"}])
        self.assertEqual(result.returncode, 1)
        case = report["cases"][0]
        self.assertEqual(case["exit_code"], 23)
        self.assertTrue(case["metadata"]["completed"])
        self.assertEqual(case["status"], "exit_failure")

    def test_unterminated_stdout_does_not_hide_completion(self):
        result, report, _, _ = self.run_probe([
            {"name": "python_stdout", "code": "print('progress', end='')"},
            {"name": "fd_stdout", "code": "import os; os.write(1, b'progress')"}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "passed")
        for case in report["cases"]:
            self.assertEqual(case["status"], "passed")
            self.assertEqual(case["exit_code"], 0)
            self.assertTrue(case["metadata"]["completed"])
            self.assertIn("progress", Path(case["logs"]["stdout"]["path"]).read_text())

    def test_exit_zero_without_probe_completion_is_inconclusive(self):
        result, report, _, _ = self.run_probe([{"name": "early", "code": "import os; os._exit(0)"}])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["cases"][0]["status"], "inconclusive")

    def test_timeout_does_not_skip_following_case(self):
        result, report, _, _ = self.run_probe([
            {"name": "slow", "code": "import time; time.sleep(10)", "timeout_seconds": 0.2},
            {"name": "next", "imports": ["json"]}])
        self.assertEqual(result.returncode, 1)
        self.assertEqual([c["status"] for c in report["cases"]], ["timeout", "passed"])

    def test_missing_module_retains_failure_log(self):
        result, report, _, _ = self.run_probe([{"name": "missing", "imports": ["nonexistent_probe_module_7d9a"]}])
        self.assertEqual(result.returncode, 1)
        case = report["cases"][0]
        self.assertEqual(case["status"], "exit_failure")
        self.assertIn("ModuleNotFoundError", Path(case["logs"]["stderr"]["path"]).read_text())

    def test_noisy_streams_are_bounded_and_env_values_not_in_report(self):
        # Evidence paths may legitimately contain common words such as private.
        self.directory = self.directory / "private"
        self.directory.mkdir()
        sentinel = "probe-env-value-8e0be45c20f14319819a26f1b9bd51d6"
        code = (f"import os, sys; assert os.getenv('PROBE_TEST_SECRET') == {sentinel!r}; "
                "print('x'*20000); sys.stderr.write('y'*20000)")
        result, report, _, _ = self.run_probe([{"name": "noise", "code": code,
                                               "env": {"PROBE_TEST_SECRET": sentinel}}], log_bytes=1024)
        self.assertEqual(result.returncode, 0, result.stderr)
        for log in report["cases"][0]["logs"].values():
            self.assertTrue(log["truncated"])
            self.assertLessEqual(Path(log["path"]).stat().st_size, 1024)
        self.assertNotIn(sentinel, json.dumps(report))

    def test_bad_config_is_rejected_without_creating_output(self):
        result, report, output, _ = self.run_probe([{"name": "../unsafe", "imports": ["json"]}])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)
        self.assertFalse(output.exists())

    def test_launch_failure_recorded(self):
        result, report, _, _ = self.run_probe([{"name": "launch", "imports": ["json"]}],
                                            python=self.directory / "missing-python")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["cases"][0]["status"], "launch_error")

    @unittest.skipUnless(os.name == "posix", "POSIX signal semantics require POSIX")
    def test_signal_after_body_completion(self):
        code = "import atexit, os, signal; atexit.register(lambda: os.kill(os.getpid(), signal.SIGTERM))"
        result, report, _, _ = self.run_probe([{"name": "signal", "code": code}])
        self.assertEqual(result.returncode, 1)
        self.assertTrue(report["cases"][0]["metadata"]["completed"])
        self.assertEqual(report["cases"][0]["signal_name"], "SIGTERM")


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.source = self.directory / "source"
        self.source.mkdir()
        (self.source / "native.so").write_bytes(b"binary\r\n\x00\xff")

    def snap(self, path=None, excludes=None):
        return artifact.snapshot({"source": path or self.source}, {}, [], excludes or [])

    def make_wheel(self, members):
        path = self.directory / "sample.whl"
        with zipfile.ZipFile(path, "w") as archive:
            for name, value in members:
                # Keep hostile archive spelling; ZipInfo(name) normalizes '\\'
                # to '/' on Windows, which would silently sanitize the fixture.
                member = zipfile.ZipInfo()
                member.filename = name
                member.orig_filename = name
                archive.writestr(member, value)
        return path

    def test_relocated_identical_tree_matches_and_origin_check_is_optional(self):
        other = self.directory / "other"
        other.mkdir()
        (other / "native.so").write_bytes((self.source / "native.so").read_bytes())
        self.assertEqual(artifact.compare(self.snap(), self.snap(other))["status"], "matched")
        self.assertEqual(artifact.compare(self.snap(), self.snap(other), check_origins=True)["status"], "different")

    def test_binary_crlf_is_not_normalized(self):
        before = self.snap()
        (self.source / "native.so").write_bytes(b"binary\n\x00\xff")
        self.assertEqual(artifact.compare(before, self.snap())["status"], "different")

    def test_missing_extra_and_type_change_reported(self):
        before = self.snap()
        (self.source / "native.so").unlink()
        (self.source / "native.so").mkdir()
        (self.source / "extra").write_bytes(b"new")
        reasons = [r["reason"] for r in artifact.compare(before, self.snap())["differences"]]
        self.assertIn("content or type differs", reasons)
        self.assertIn("extra", reasons)
        (self.source / "native.so").rmdir()
        self.assertIn("missing", [r["reason"] for r in artifact.compare(before, self.snap())["differences"]])

    def test_missing_root_is_incomplete_not_empty_success(self):
        missing = self.snap(self.directory / "missing")
        self.assertEqual(missing["status"], "incomplete")
        self.assertEqual(artifact.compare(missing, missing)["status"], "inconclusive")

    def test_filters_do_not_modify_source_and_coverage_difference_is_visible(self):
        lock = self.source / "active.lock"
        lock.write_text("keep", encoding="utf-8")
        filtered = self.snap(excludes=["*.lock"])
        self.assertEqual(lock.read_text(), "keep")
        self.assertNotIn("active.lock", filtered["roots"]["source"]["entries"])
        self.assertEqual(artifact.compare(filtered, self.snap())["status"], "different")

    def test_wheel_data_purelib_and_record_mapping(self):
        site = self.directory / "site"
        (site / "pkg").mkdir(parents=True)
        (site / "pkg/a.py").write_bytes(b"a=1\n")
        (site / "pkg/b.so").write_bytes(b"native")
        wheel = self.make_wheel([("pkg/a.py", b"a=1\n"), ("pkg.data/purelib/pkg/b.so", b"native"),
                                 ("pkg.dist-info/RECORD", b"original")])
        result = artifact.wheel_installation(wheel, {"site": site, "purelib": site})
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["checked_files"], 2)
        self.assertEqual(len(result["excluded"]), 1)
        (site / "pkg/b.so").write_bytes(b"different")
        self.assertEqual(artifact.wheel_installation(wheel, {"site": site, "purelib": site})["status"], "different")

    def test_wheel_unknown_scheme_is_inconclusive(self):
        wheel = self.make_wheel([("pkg.data/scripts/tool", b"tool")])
        self.assertEqual(artifact.wheel_installation(wheel, {"site": self.source})["status"], "inconclusive")

    def test_record_or_signature_only_wheel_has_no_verifiable_coverage(self):
        site = self.directory / "empty-site"
        site.mkdir()
        for name in ("RECORD", "RECORD.jws", "RECORD.p7s"):
            with self.subTest(name=name):
                wheel = self.make_wheel([("pkg.dist-info/" + name, b"installer metadata")])
                output = self.directory / (name + ".json")
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts/artifact_manifest.py"), "verify-wheel",
                     "--wheel", str(wheel), "--site-root", str(site), "--output", str(output)],
                    capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 1, result.stderr)
                report = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(report["status"], "inconclusive")
                self.assertEqual(report["checked_files"], 0)
                self.assertEqual(len(report["excluded"]), 1)
                self.assertIn("no wheel members", " ".join(report["errors"]))
                self.assertEqual(list(site.iterdir()), [])

    def test_wheel_traversal_absolute_and_backslash_rejected(self):
        for name in ("../escape", "/absolute", "C:/escape", "pkg\\escape"):
            with self.subTest(name=name):
                wheel = self.make_wheel([(name, b"bad")])
                self.assertTrue(artifact.wheel_record(wheel)["errors"])
                self.assertEqual(artifact.wheel_installation(wheel, {"site": self.source})["status"], "inconclusive")

    def test_duplicate_wheel_member_is_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            wheel = self.make_wheel([("pkg/a", b"a"), ("pkg/a", b"b")])
        self.assertTrue(artifact.wheel_record(wheel)["errors"])

    def test_empty_corrupt_and_unsafe_directory_wheels_not_matched(self):
        for members in ([], [("../escape/", b"")]):
            with self.subTest(members=members):
                wheel = self.make_wheel(members)
                self.assertEqual(artifact.wheel_installation(wheel, {"site": self.source})["status"], "inconclusive")
        corrupt = self.directory / "corrupt.whl"
        corrupt.write_bytes(b"not a zip")
        self.assertEqual(artifact.wheel_installation(corrupt, {"site": self.source})["status"], "inconclusive")

    def test_distribution_metadata_does_not_import_target(self):
        site = self.directory / "site"
        package = site / "probe_demo"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("raise RuntimeError('must not import')", encoding="utf-8")
        info = site / "probe_demo-1.2.dist-info"
        info.mkdir()
        (info / "METADATA").write_text("Metadata-Version: 2.1\nName: probe-demo\nVersion: 1.2\n", encoding="utf-8")
        (info / "top_level.txt").write_text("probe_demo\n", encoding="utf-8")
        (info / "RECORD").write_text("probe_demo/__init__.py,,\nprobe_demo-1.2.dist-info/METADATA,,\n", encoding="utf-8")
        sys.path.insert(0, str(site))
        self.addCleanup(lambda: sys.path.remove(str(site)))
        result = artifact.distribution_record("probe_demo")
        self.assertEqual(result["version"], "1.2")
        self.assertFalse(result["errors"])
        self.assertTrue(result["module_locations"]["probe_demo"]["origin"].endswith("__init__.py"))
        self.assertNotIn("probe_demo", sys.modules)

    def test_missing_distribution_is_incomplete(self):
        result = artifact.snapshot({}, {}, ["missing-package-8bf032"], [])
        self.assertEqual(result["status"], "incomplete")

    def test_cli_exit_codes_and_output_preservation(self):
        script = str(ROOT / "scripts/artifact_manifest.py")
        output = self.directory / "manifest.json"
        command = [sys.executable, script, "snapshot", "--root", f"source={self.source}", "--output", str(output)]
        first = subprocess.run(command, capture_output=True, timeout=10)
        self.assertEqual(first.returncode, 0, first.stderr)
        original = output.read_bytes()
        self.assertEqual(subprocess.run(command, capture_output=True, timeout=10).returncode, 2)
        self.assertEqual(output.read_bytes(), original)
        missing = subprocess.run([sys.executable, script, "snapshot", "--root", f"source={self.directory / 'missing'}",
                                  "--output", str(self.directory / "missing.json")], capture_output=True, timeout=10)
        self.assertEqual(missing.returncode, 1)

    def test_compare_and_wheel_cli_actions(self):
        script = str(ROOT / "scripts/artifact_manifest.py")
        baseline = self.directory / "baseline.json"
        baseline.write_text(json.dumps(self.snap()), encoding="utf-8")
        (self.source / "native.so").write_bytes(b"changed")
        candidate = self.directory / "candidate.json"
        candidate.write_text(json.dumps(self.snap()), encoding="utf-8")
        comparison = self.directory / "comparison.json"
        result = subprocess.run([sys.executable, script, "compare", "--expected", str(baseline), "--actual", str(candidate),
                                 "--output", str(comparison)], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(json.loads(comparison.read_text())["status"], "different")
        wheel = self.make_wheel([("native.so", b"changed")])
        installed = self.directory / "installed.json"
        result = subprocess.run([sys.executable, script, "verify-wheel", "--wheel", str(wheel), "--site-root", str(self.source),
                                 "--output", str(installed)], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(installed.read_text())["status"], "matched")

    def test_symlink_target_is_recorded_without_following(self):
        link = self.source / "linked"
        target = self.directory / "target"
        target.write_bytes(b"old")
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("platform requires symlink permission")
        before = self.snap()
        target.write_bytes(b"new")
        self.assertEqual(artifact.compare(before, self.snap())["status"], "matched")
        wheel = self.make_wheel([("linked", b"new")])
        self.assertEqual(artifact.wheel_installation(wheel, {"site": self.source})["status"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
