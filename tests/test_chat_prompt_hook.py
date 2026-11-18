"""Exercise the actual hook CLI, including relocated paths and invalid events."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1] / ".agents/skills/ascend-chat-organization"


class PromptHookTests(unittest.TestCase):
    def run_hook(self, script, payload, cwd=None):
        return subprocess.run([sys.executable, str(script)], input=payload,
                              capture_output=True, cwd=cwd, check=False)

    def test_relocated_skill_from_unrelated_cwd(self):
        with tempfile.TemporaryDirectory(prefix="chat hook ") as directory:
            root = Path(directory)
            copied = root / "另一个工作台" / "skill"
            shutil.copytree(SKILL, copied)
            before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
            event = {"hook_event_name": "UserPromptSubmit", "prompt": "PRIVATE_PROMPT"}
            result = self.run_hook(copied / "scripts/prompt_hook.py",
                                   json.dumps(event).encode(), cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            output = data["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "UserPromptSubmit")
            self.assertIn((copied / "SKILL.md").as_posix(), output["additionalContext"])
            self.assertNotIn("PRIVATE_PROMPT", result.stdout.decode())
            self.assertEqual(before, sorted(str(p.relative_to(root)) for p in root.rglob("*")))
            repeated = self.run_hook(copied / "scripts/prompt_hook.py", json.dumps(event).encode(), root)
            self.assertEqual(result.stdout, repeated.stdout)

    def test_unrelated_event_does_not_emit_context(self):
        for event in [{"hook_event_name": "Stop"}, {}, [], None]:
            with self.subTest(event=event):
                result = self.run_hook(SKILL / "scripts/prompt_hook.py", json.dumps(event).encode())
                self.assertEqual((result.returncode, result.stdout), (0, b""))

    def test_malformed_input_is_nonblocking_and_not_echoed(self):
        for payload in [b"", b"SECRET malformed json", b"\xff"]:
            with self.subTest(payload=payload):
                result = self.run_hook(SKILL / "scripts/prompt_hook.py", payload)
                self.assertEqual((result.returncode, result.stdout), (0, b""))
                self.assertNotIn(b"SECRET", result.stderr)

    def test_missing_skill_is_nonblocking(self):
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "scripts/prompt_hook.py"
            script.parent.mkdir()
            shutil.copy2(SKILL / "scripts/prompt_hook.py", script)
            result = self.run_hook(script, b'{"hook_event_name":"UserPromptSubmit"}')
            self.assertEqual((result.returncode, result.stdout), (0, b""))
            self.assertIn(b"skill unavailable", result.stderr)

    def test_windows_utf8_bom_event(self):
        result = self.run_hook(SKILL / "scripts/prompt_hook.py",
                               b'\xef\xbb\xbf{"hook_event_name":"UserPromptSubmit"}')
        self.assertEqual(result.returncode, 0)
        json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main()
