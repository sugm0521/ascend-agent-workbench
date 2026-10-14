import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
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

    def tearDown(self):
        self.temp.cleanup()

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
