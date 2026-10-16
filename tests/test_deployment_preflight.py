"""Synthetic local checks; no Docker daemon, SSH, NPU or author's data required."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deployment_preflight.py"
SPEC = importlib.util.spec_from_file_location("deployment_preflight", SCRIPT)
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


class DeploymentPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model = self.root / "model files"
        self.model.mkdir()
        self.endpoints = self.root / "endpoints"
        self.endpoints.mkdir()
        self.plan = {"schema_version": 1, "node": "synthetic-node", "container": "synthetic-service",
                     "mounts": [{"source": str(self.model), "target": "/models", "kind": "directory", "read_only": True}],
                     "communication": {"mode": "none"}, "env": {}}

    def static(self):
        self.plan["mounts"].append({"source": str(self.endpoints), "target": "/endpoints", "kind": "directory", "read_only": True})
        self.plan["communication"] = {"mode": "static", "endpoint_directory": str(self.endpoints), "physical_device_ids": [2, 5],
                                      "connector_extra_config": {"ascend_local_comm_res_path": "/endpoints"}}

    def auto(self):
        self.plan["communication"] = {"mode": "auto"}
        self.plan["env"] = {"ASCEND_LOCAL_COMM_RES": '{"version":"1.3"}', "ASCEND_GLOBAL_RESOURCE_CONFIG": ""}
        self.plan["required_paths"] = [{"path": str(self.root), "kind": "directory"}]
        self.plan["required_commands"] = [sys.executable]

    def endpoints_ready(self):
        for n in [2, 5]:
            (self.endpoints / f"ub_endpoint_npu_{n}.json").write_text(json.dumps({"synthetic_physical_device": n}), encoding="utf-8")

    def inspection(self):
        return [{"Name": "/synthetic-service", "Mounts": [{"Type": "bind", "Source": m["source"], "Destination": m["target"], "RW": not m["read_only"]} for m in self.plan["mounts"]],
                 "Config": {"Env": [k + "=" + v for k, v in self.plan["env"].items()]}}]

    def codes(self, report):
        return {e["code"] for e in report["errors"]}

    def cli(self, phase, plan=None, inspection=None):
        path = self.root / "plan.json"
        path.write_text(json.dumps(self.plan if plan is None else plan), encoding="utf-8")
        args = [sys.executable, str(SCRIPT), phase, "--plan", str(path)]
        if inspection is not None:
            snapshot = self.root / "inspect.json"
            snapshot.write_text(json.dumps(inspection), encoding="utf-8")
            args.extend(["--inspect", str(snapshot)])
        env = dict(os.environ)
        env.pop("ASCEND_GLOBAL_RESOURCE_CONFIG", None)
        env.pop("PYTHONPATH", None)
        return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", env=env, timeout=15)

    def test_static_empty_directory_reports_each_physical_device(self):
        self.static()
        result = TOOL.preflight(self.plan, {})
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["errors"]), 2)
        self.assertTrue(all(e["code"] == "endpoint_missing" for e in result["errors"]))
        self.assertIn("ub_endpoint_npu_5.json", result["errors"][1]["detail"])

    def test_static_valid_then_missing_one_device(self):
        self.static()
        self.endpoints_ready()
        self.assertTrue(TOOL.preflight(self.plan, {})["ok"])
        (self.endpoints / "ub_endpoint_npu_5.json").unlink()
        self.assertEqual(self.codes(TOOL.preflight(self.plan, {})), {"endpoint_missing"})

    def test_static_rejects_invalid_json_and_endpoint_mount(self):
        self.static()
        self.endpoints_ready()
        (self.endpoints / "ub_endpoint_npu_2.json").write_text("[]", encoding="utf-8")
        self.plan["mounts"][1]["target"] = "/wrong-endpoints"
        self.assertEqual(self.codes(TOOL.preflight(self.plan, {})), {"endpoint_json", "endpoint_mount"})

    def test_file_mount_cannot_pass_as_an_empty_directory(self):
        self.plan["mounts"][0]["kind"] = "file"
        self.assertEqual(self.codes(TOOL.preflight(self.plan, {})), {"mount_source"})

    def test_auto_passes_without_any_endpoint_files(self):
        self.auto()
        # An unrelated empty host directory does not make static endpoints required.
        self.plan["communication"]["endpoint_directory"] = str(self.endpoints)
        self.assertTrue(TOOL.preflight(self.plan, {})["ok"])
        self.assertEqual(list(self.endpoints.iterdir()), [])

    def test_auto_rejects_static_path_and_inherited_protocol(self):
        self.auto()
        self.plan["communication"]["connector_extra_config"] = {"ascend_local_comm_res_path": "/endpoints"}
        del self.plan["env"]["ASCEND_GLOBAL_RESOURCE_CONFIG"]
        self.assertEqual(self.codes(TOOL.preflight(self.plan, {"ASCEND_GLOBAL_RESOURCE_CONFIG": "legacy"})), {"auto_static_conflict", "auto_global_conflict"})

    def test_auto_explicit_clear_handles_inherited_protocol(self):
        self.auto()
        self.assertTrue(TOOL.preflight(self.plan, {"ASCEND_GLOBAL_RESOURCE_CONFIG": "legacy"})["ok"])

    def test_auto_must_declare_version_without_static_resource_data(self):
        self.auto()
        for value in ["", "{", "[]", '{"version":"1.3","endpoints":[]}']:
            with self.subTest(value=value):
                self.plan["env"]["ASCEND_LOCAL_COMM_RES"] = value
                self.assertIn("auto_resource_config", self.codes(TOOL.preflight(self.plan, {})))

    def test_declared_device_and_command_requirements_are_checked(self):
        self.auto()
        self.plan["required_paths"] = [{"path": str(self.root / "missing-device"), "kind": "character_device"}]
        self.plan["required_commands"] = [str(self.root / "missing-tool")]
        self.assertEqual(self.codes(TOOL.preflight(self.plan, {})), {"required_path", "command_missing"})

    def test_auto_without_declared_prerequisites_is_not_accepted(self):
        self.auto()
        self.plan["required_paths"] = []
        self.assertIn("auto_prerequisites", self.codes(TOOL.preflight(self.plan, {})))

    def test_file_exists_but_missing_bind_mount_is_rejected(self):
        self.assertTrue(self.model.is_dir())
        inspection = self.inspection()
        inspection[0]["Mounts"] = []
        self.assertEqual(self.codes(TOOL.verify(self.plan, inspection, {})), {"mount_mismatch"})

    def test_wrong_bind_source_type_and_access_are_rejected(self):
        for update in [{"Source": str(self.endpoints)}, {"Type": "volume"}, {"RW": True}]:
            with self.subTest(update=update):
                inspection = self.inspection()
                inspection[0]["Mounts"][0].update(update)
                self.assertFalse(TOOL.verify(self.plan, inspection, {})["ok"])

    def test_wrong_container_and_env_drift_are_rejected(self):
        self.auto()
        inspection = self.inspection()
        inspection[0]["Name"] = "/other-container"
        inspection[0]["Config"]["Env"] = ["ASCEND_GLOBAL_RESOURCE_CONFIG=old"]
        self.assertEqual(self.codes(TOOL.verify(self.plan, inspection, {})), {"container_mismatch", "env_mismatch", "auto_global_conflict"})

    def test_shared_renderer_preserves_spaces_and_matches_inspect(self):
        self.auto()
        first = TOOL.docker_args(self.plan)
        self.assertEqual(first, TOOL.docker_args(copy.deepcopy(self.plan)))
        self.assertIn("type=bind,src=" + str(self.model) + ",dst=/models,readonly", first)
        self.assertTrue(TOOL.verify(self.plan, self.inspection(), {})["ok"])

    def test_cli_rejects_empty_static_before_emitting_launch_args(self):
        self.static()
        result = self.cli("docker-args")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("endpoint_missing", result.stderr)

    def test_cli_auto_preflight_render_and_verify(self):
        self.auto()
        before = self.cli("preflight")
        self.assertEqual(before.returncode, 0, before.stdout + before.stderr)
        self.assertTrue(json.loads(before.stdout)["ok"])
        rendered = self.cli("docker-args")
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertEqual(json.loads(rendered.stdout), TOOL.docker_args(self.plan))
        after = self.cli("verify", inspection=self.inspection())
        self.assertEqual(after.returncode, 0, after.stdout + after.stderr)

    def test_cli_missing_input_and_missing_inspect_are_explicit(self):
        missing = subprocess.run([sys.executable, str(SCRIPT), "preflight", "--plan", str(self.root / "absent.json")], capture_output=True, text=True, timeout=15)
        self.assertEqual(missing.returncode, 2)
        self.assertFalse(json.loads(missing.stdout)["ok"])
        missing_inspect = self.cli("verify")
        self.assertEqual(missing_inspect.returncode, 2)
        self.assertIn("--inspect", json.loads(missing_inspect.stdout)["error"])

    def test_bad_plan_and_ambiguous_inspect_fail_closed(self):
        for change in [{"communication": {"mode": "unknown"}}, {"unexpected": True}]:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    TOOL.preflight(dict(self.plan, **change), {})
        for inspection in [[], [{}, {}], {"Name": "/synthetic-service", "Mounts": [None]}]:
            with self.subTest(inspection=inspection):
                with self.assertRaises(ValueError):
                    TOOL.verify(self.plan, inspection, {})


if __name__ == "__main__":
    unittest.main()
