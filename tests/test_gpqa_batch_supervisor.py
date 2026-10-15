import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gpqa_supervisor', ROOT / 'tasks/1014/scripts/gpqa_batch_supervisor.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class BatchSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = self.root / 'plan.json'
        self.state = self.root / 'state.json'
        self.processes = []

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=10)
        self.temp.cleanup()

    def start_supervisor(self, resume=False, pause_at=None):
        # Pause a real process inside the critical section so its competitor
        # encounters the exact pre-ownership window, without timing guesses.
        worker = self.root / 'worker.py'
        worker.write_text('''import importlib.util, sys, time
from pathlib import Path
spec = importlib.util.spec_from_file_location('driver', sys.argv[1])
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
root = Path(sys.argv[2])
hook = sys.argv[4]
if hook:
    original = getattr(driver, hook)
    def pause(*args, **kwargs):
        result = original(*args, **kwargs)
        (root / 'ready').write_text('ready')
        deadline = time.monotonic() + 15
        while not (root / 'release').exists():
            if time.monotonic() >= deadline:
                raise RuntimeError('test gate timed out')
            time.sleep(.01)
        return result
    setattr(driver, hook, pause)
driver.supervise(root / 'plan.json', root / 'state.json', sys.argv[3] == '1')
''', encoding='utf-8')
        kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
        process = subprocess.Popen([sys.executable, str(worker), str(spec.origin),
                                    str(self.root), '1' if resume else '0', pause_at or ''],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs)
        self.processes.append(process)
        return process

    def wait_for_gate(self, process):
        deadline = time.monotonic() + 10
        while not (self.root / 'ready').exists():
            if process.poll() is not None:
                self.fail('supervisor exited before gate: ' + str(process.communicate()))
            if time.monotonic() >= deadline:
                self.fail('supervisor did not reach test gate')
            time.sleep(.01)

    def assert_contender_rejected(self, process):
        output, error = process.communicate(timeout=10)
        self.assertNotEqual(process.returncode, 0, output + error)
        self.assertIn('state lock busy', error)

    def test_concurrent_initial_launch_cannot_create_or_rewrite_state(self):
        groups = self.make_plan(1)
        owner = self.start_supervisor(pause_at='validate_plan')
        self.wait_for_gate(owner)
        self.assertFalse(self.state.exists())
        self.assert_contender_rejected(self.start_supervisor())
        self.assertFalse(self.state.exists())
        (self.root / 'release').touch()
        output, error = owner.communicate(timeout=10)
        self.assertEqual(owner.returncode, 0, output + error)
        self.assertEqual(json.loads(self.state.read_text())['status'], 'completed')
        self.assertEqual((Path(groups[0]['root']) / 'sent.txt').read_text(), 'x')

    def test_concurrent_resume_cannot_overwrite_owner_state(self):
        groups = self.make_plan(1)
        driver.atomic_json(self.state, {
            'plan_sha256': hashlib.sha256(self.plan.read_bytes()).hexdigest(),
            'status': 'running', 'owner': {'pid': 999999999, 'starttime': 'dead'},
            'groups': [{'id': 'g0', 'status': 'pending'}]})
        before = self.state.read_bytes()
        owner = self.start_supervisor(resume=True, pause_at='same_live')
        self.wait_for_gate(owner)
        self.assert_contender_rejected(self.start_supervisor(resume=True))
        self.assertEqual(self.state.read_bytes(), before)
        (self.root / 'release').touch()
        output, error = owner.communicate(timeout=10)
        self.assertEqual(owner.returncode, 0, output + error)
        state = json.loads(self.state.read_text())
        self.assertEqual(state['status'], 'completed')
        self.assertEqual(state['owner']['pid'], owner.pid)
        self.assertEqual((Path(groups[0]['root']) / 'sent.txt').read_text(), 'x')

    def test_process_crash_releases_lock_without_removing_sidecar(self):
        self.make_plan(1)
        owner = self.start_supervisor(pause_at='validate_plan')
        self.wait_for_gate(owner)
        lock = self.state.with_name(self.state.name + '.lock')
        self.assertTrue(lock.exists())
        owner.kill()
        owner.communicate(timeout=10)
        self.assertFalse(self.state.exists())
        self.assertEqual(driver.supervise(self.plan, self.state)['status'], 'completed')
        self.assertTrue(lock.exists())

    def test_running_client_is_preserved_after_supervisor_crash(self):
        groups = self.make_plan(1)
        root = Path(groups[0]['root'])
        groups[0]['command'] = [sys.executable, '-c', '''import time
from pathlib import Path
Path('sent.txt').write_text('x')
deadline = time.monotonic() + 10
while not Path('client.release').exists():
    if time.monotonic() > deadline:
        raise RuntimeError('client gate timed out')
    time.sleep(.01)
Path('result.json').write_text('{"samples":1}')
''']
        self.plan.write_text(json.dumps({'groups': groups}))
        owner = self.start_supervisor()
        client = None
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if self.state.exists():
                    state = json.loads(self.state.read_text())
                    client = state['groups'][0].get('process')
                    if client and (root / 'sent.txt').exists():
                        break
                self.assertIsNone(owner.poll(), 'supervisor exited before starting client')
                time.sleep(.01)
            self.assertIsNotNone(client, 'client was not recorded')
            before = self.state.read_bytes()
            self.assert_contender_rejected(self.start_supervisor(resume=True))
            self.assertEqual(self.state.read_bytes(), before)
            owner.kill()
            owner.communicate(timeout=10)
            # The OS lock is released but the unfinished client still owns its
            # requests: do not turn crash recovery into an implicit retry.
            with self.assertRaisesRegex(ValueError, 'client command is still running'):
                driver.supervise(self.plan, self.state, resume=True)
            self.assertEqual(self.state.read_bytes(), before)
            self.assertEqual((root / 'sent.txt').read_text(), 'x')
        finally:
            (root / 'client.release').touch()
            if client:
                deadline = time.monotonic() + 10
                while driver.same_live(client) and time.monotonic() < deadline:
                    time.sleep(.01)
                self.assertFalse(driver.same_live(client), 'task client did not exit')

    def test_exception_releases_lock_and_preserves_state(self):
        self.make_plan(1)
        before = b'not valid json'
        self.state.write_bytes(before)
        with self.assertRaises(json.JSONDecodeError):
            driver.supervise(self.plan, self.state, resume=True)
        with driver.state_lock(self.state):
            self.assertEqual(self.state.read_bytes(), before)

    def make_plan(self, count=2, fail=None, collect=False):
        groups = []
        for i in range(count):
            root = self.root / f'g{i}'
            root.mkdir()
            code = "from pathlib import Path;import json; p=Path('sent.txt');p.write_text(p.read_text()+'x' if p.exists() else 'x');"
            if i == fail:
                code += 'raise SystemExit(7)'
            elif not collect:
                code += "Path('result.json').write_text(json.dumps({'samples':1}))"
            group = {'id': f'g{i}', 'root': str(root), 'command': [sys.executable, '-c', code],
                     'result': 'result.json', 'expected_result': {'samples': 1}}
            if collect:
                group['collect'] = [sys.executable, '-c', "from pathlib import Path;Path('result.json').write_text('{\"samples\":1}')"]
            groups.append(group)
        self.plan.write_text(json.dumps({'groups': groups}))
        return groups

    def test_success_and_completed_resume_do_not_resend(self):
        groups = self.make_plan(3)
        state = driver.supervise(self.plan, self.state)
        self.assertEqual(state['status'], 'completed')
        with self.assertRaises(ValueError):
            driver.supervise(self.plan, self.state)
        state = driver.supervise(self.plan, self.state, resume=True)
        self.assertEqual(state['status'], 'completed')
        self.assertTrue(all((Path(g['root']) / 'sent.txt').read_text() == 'x' for g in groups))

    def test_failure_stops_remaining_groups_and_preserves_result(self):
        groups = self.make_plan(3, fail=1)
        with self.assertRaises(ValueError):
            driver.supervise(self.plan, self.state)
        state = json.loads(self.state.read_text())
        self.assertEqual([g['status'] for g in state['groups']], ['completed', 'failed', 'pending'])
        self.assertFalse((Path(groups[2]['root']) / 'sent.txt').exists())
        with self.assertRaises(ValueError):
            driver.supervise(self.plan, self.state, resume=True)
        self.assertEqual((Path(groups[1]['root']) / 'sent.txt').read_text(), 'x')

    def test_resume_verified_completed_and_pending_only(self):
        groups = self.make_plan(2)
        first = Path(groups[0]['root'])
        (first / 'result.json').write_text('{"samples":1}')
        (first / 'sent.txt').write_text('x')
        old = {'plan_sha256': hashlib.sha256(self.plan.read_bytes()).hexdigest(), 'status': 'interrupted',
            'groups': [{'id': 'g0', 'status': 'completed', 'result_sha256': driver.validate_result(groups[0])},
                       {'id': 'g1', 'status': 'pending'}]}
        driver.atomic_json(self.state, old)
        state = driver.supervise(self.plan, self.state, resume=True)
        self.assertEqual(state['status'], 'completed')
        self.assertEqual((first / 'sent.txt').read_text(), 'x')
        self.assertEqual((Path(groups[1]['root']) / 'sent.txt').read_text(), 'x')

    def test_live_supervisor_blocks_duplicate(self):
        self.make_plan(1)
        import os
        driver.atomic_json(self.state, {'plan_sha256': hashlib.sha256(self.plan.read_bytes()).hexdigest(),
            'status': 'running', 'owner': driver.identity(os.getpid()), 'groups': [{'id': 'g0', 'status': 'pending'}]})
        with self.assertRaisesRegex(ValueError, 'already running'):
            driver.supervise(self.plan, self.state, resume=True)
        self.assertFalse((self.root / 'g0/sent.txt').exists())

    def test_unknown_group_is_never_automatically_retried(self):
        self.make_plan(1)
        driver.atomic_json(self.state, {'plan_sha256': hashlib.sha256(self.plan.read_bytes()).hexdigest(),
            'status': 'interrupted', 'groups': [{'id': 'g0', 'status': 'running'}]})
        with self.assertRaisesRegex(ValueError, 'failed or unknown'):
            driver.supervise(self.plan, self.state, resume=True)
        self.assertFalse((self.root / 'g0/sent.txt').exists())

    def test_changed_result_or_plan_blocks_resume(self):
        groups = self.make_plan(1)
        driver.supervise(self.plan, self.state)
        (Path(groups[0]['root']) / 'result.json').write_text('{"samples":2}')
        with self.assertRaises(ValueError):
            driver.supervise(self.plan, self.state, resume=True)

    def test_original_run_artifacts_without_state_are_not_restarted(self):
        groups = self.make_plan(1)
        root = Path(groups[0]['root'])
        (root / 'setup').mkdir()
        (root / 'setup/aisbench.log').write_text('old run')
        with self.assertRaises(ValueError):
            driver.supervise(self.plan, self.state)
        self.assertFalse((root / 'sent.txt').exists())

    def test_collect_runs_after_evaluate_and_has_separate_log(self):
        groups = self.make_plan(1, collect=True)
        state = driver.supervise(self.plan, self.state)
        self.assertEqual(state['status'], 'completed')
        self.assertEqual(state['groups'][0]['collect_exit_code'], 0)
        root = Path(groups[0]['root'])
        self.assertTrue((root / 'evaluate.client.log').exists())
        self.assertTrue((root / 'collect.client.log').exists())

    def test_corrupt_state_group_list_is_not_silently_zipped(self):
        self.make_plan(2)
        driver.atomic_json(self.state, {'plan_sha256': hashlib.sha256(self.plan.read_bytes()).hexdigest(),
            'status': 'interrupted', 'groups': [{'id': 'g0', 'status': 'pending'}]})
        with self.assertRaisesRegex(ValueError, 'identities'):
            driver.supervise(self.plan, self.state, resume=True)

    def test_linux_proc_identity_parses_command_with_spaces(self):
        text = '123 (python client name) ' + ' '.join(['R'] + ['0'] * 18 + ['4321'])
        with mock.patch.object(driver.sys, 'platform', 'linux'), mock.patch.object(Path, 'read_text', return_value=text):
            value = driver.identity(123)
        self.assertEqual(value, {'pid': 123, 'starttime': '4321', 'state': 'running'})

    def test_reused_pid_is_not_the_saved_process(self):
        with mock.patch.object(driver, 'identity', return_value={'pid': 123, 'starttime': 'new', 'state': 'running'}):
            self.assertFalse(driver.same_live({'pid': 123, 'starttime': 'old'}))

    def test_unknown_process_identity_requires_inspection(self):
        with mock.patch.object(driver, 'identity', return_value={'pid': 123, 'state': 'unknown'}):
            with self.assertRaisesRegex(ValueError, 'unknown'):
                driver.same_live({'pid': 123, 'starttime': 'old'})

    def test_status_reads_matching_plan_without_writing_state(self):
        self.make_plan(1)
        driver.supervise(self.plan, self.state)
        spec = importlib.util.spec_from_file_location('batch_status', ROOT / 'tasks/1014/scripts/gpqa_batch_status.py')
        reader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reader)
        before = self.state.read_bytes()
        value = reader.status(self.plan, self.state)
        self.assertEqual(value['completed_groups_recorded'], 1)
        self.assertEqual(self.state.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
