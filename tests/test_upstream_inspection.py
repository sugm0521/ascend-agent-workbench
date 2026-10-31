"""Real synthetic Git histories exercise read-only source/consumer inspection."""
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('upstream_inspection', ROOT / 'scripts/inspect_upstream.py')
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


@unittest.skipIf(TOOL.yaml is None, 'optional inspection parser unavailable; install requirements-upstream.txt')
class InspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'deps/engine'
        self.source.mkdir(parents=True)
        self.git(self.root, 'init', '-q')
        self.git(self.source, 'init', '-q')
        self.git(self.source, 'remote', 'add', 'origin', 'https://example.invalid/org/engine.git')
        self.write(self.source, 'skills/feature/SKILL.md', '# Feature\nOriginal input/output contract.\n')
        self.commit(self.source)
        self.base = self.git(self.source, 'rev-parse', 'HEAD')
        self.write(self.root, '.gitmodules', '[submodule "deps/engine"]\n path = deps/engine\n url = https://example.invalid/org/engine.git\n')
        self.write(self.root, 'config/workbench.local.yaml', 'schema_version: 1\ndependencies:\n  engine:\n    enabled: true\n')
        self.lock = {'schema_version': 1, 'sources': {'engine': {
            'path': 'deps/engine', 'url': 'https://example.invalid/org/engine.git',
            'commit': self.base, 'declared_dependencies': [],
        }}}
        self.save_lock()
        self.consumer('leaf', [{'source_id': 'engine', 'resources': ['skills/feature/SKILL.md'],
                                'relationship': 'method_reference', 'when': 'feature input',
                                'upstream_basis_revision': self.base}])
        self.git(self.root, 'add', '.gitmodules', 'upstream', '.agents')
        self.git(self.root, 'update-index', '--add', '--cacheinfo', '160000,' + self.base + ',deps/engine')
        self.commit(self.root, add=False)

    def git(self, directory, *args):
        value = subprocess.run(['git', '-C', str(directory), *args], capture_output=True, text=True,
                               encoding='utf-8', check=True)
        return value.stdout.strip()

    def write(self, directory, relative, text):
        path = directory / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def commit(self, directory, add=True):
        if add:
            self.git(directory, 'add', '.')
        self.git(directory, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'fixture')

    def save_lock(self):
        self.write(self.root, 'upstream/sources.lock.yaml', TOOL.yaml.safe_dump(self.lock, sort_keys=False))

    def consumer(self, name, uses):
        self.write(self.root, f'.agents/skills/{name}/SKILL.md', '# Local capability\n')
        self.write(self.root, f'.agents/skills/{name}/references/upstream-usage.json',
                   json.dumps({'schema_version': 1, 'consumer': name, 'uses': uses}))

    def candidate(self, path='skills/feature/SKILL.md', text='# Feature\nEnhanced contract.\n'):
        self.write(self.source, path, text)
        self.commit(self.source)
        new = self.git(self.source, 'rev-parse', 'HEAD')
        self.git(self.source, 'checkout', '-q', '--detach', self.base)
        return new

    def inspect(self, **kwargs):
        return TOOL.inspect(self.root, ['engine'], **kwargs)

    def test_no_delta_is_not_an_automatic_network_or_write_operation(self):
        before = self.git(self.root, 'status', '--porcelain')
        contents = (self.source / 'skills/feature/SKILL.md').read_bytes()
        with mock.patch.object(TOOL, 'remote_head', side_effect=AssertionError('unexpected network')):
            report = self.inspect()
        self.assertEqual(report['sources'][0]['status'], 'no_source_delta')
        self.assertEqual(report['sources'][0]['basis_checks'][0]['status'], 'basis_matches_target')
        self.assertEqual(report['affected_consumers'], [])
        self.assertEqual(before, self.git(self.root, 'status', '--porcelain'))
        self.assertEqual(contents, (self.source / 'skills/feature/SKILL.md').read_bytes())

    def test_changed_resource_propagates_through_project_calls_and_rule_backedge(self):
        self.consumer('entry', [{'source_id': 'workbench', 'resources': ['.agents/skills/leaf/SKILL.md'],
                                 'relationship': 'skill_call', 'when': 'feature target', 'upstream_basis_revision': None}])
        path = self.root / '.agents/skills/leaf/references/upstream-usage.json'
        data = json.loads(path.read_text())
        data['uses'].append({'source_id': 'workbench', 'resources': ['.agents/skills/entry/SKILL.md'],
                             'relationship': 'rule_reference', 'when': 'domain rules', 'upstream_basis_revision': None})
        path.write_text(json.dumps(data))
        candidate = self.candidate()
        report = self.inspect(candidates={'engine': candidate})
        self.assertEqual(report['sources'][0]['status'], 'changed')
        self.assertEqual({x['consumer'] for x in report['affected_consumers']}, {'leaf', 'entry'})
        self.assertEqual(self.git(self.source, 'rev-parse', 'HEAD'), self.base)

    def test_absorption_delta_exists_when_adopted_source_has_no_new_candidate(self):
        self.write(self.source, 'skills/feature/SKILL.md', '# Already adopted source enhancement\n')
        self.commit(self.source)
        new = self.git(self.source, 'rev-parse', 'HEAD')
        self.lock['sources']['engine']['commit'] = new
        self.save_lock()
        self.git(self.root, 'update-index', '--cacheinfo', '160000,' + new + ',deps/engine')
        report = self.inspect()
        source = report['sources'][0]
        self.assertEqual(source['changes'], [])
        self.assertTrue(source['basis_checks'][0]['adopted_delta'])
        self.assertEqual(source['basis_checks'][0]['status'], 'review_delta')
        self.assertEqual(report['affected_consumers'][0]['consumer'], 'leaf')
        self.assertEqual(report['affected_consumers'][0]['reasons'][0]['reason'],
                         'historical_basis_delta_requires_review')

    def test_missing_candidate_is_needs_fetch_without_fetch(self):
        report = self.inspect(candidates={'engine': 'f' * 40})
        self.assertEqual(report['sources'][0]['status'], 'needs_fetch')
        self.assertEqual(self.git(self.source, 'rev-parse', 'HEAD'), self.base)

    def test_missing_tracked_declaration_cannot_hide_a_changed_source_consumer(self):
        candidate = self.candidate()
        path = self.root / '.agents/skills/leaf/references/upstream-usage.json'
        original = path.read_bytes()
        path.unlink()
        captured = io.StringIO()
        with redirect_stdout(captured):
            code = TOOL.main(['--root', str(self.root), '--source', 'engine', '--candidate', 'engine=' + candidate])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(captured.getvalue())['status'], 'inspection_error')
        path.write_bytes(original)
        report = self.inspect(candidates={'engine': candidate})
        self.assertEqual([item['consumer'] for item in report['affected_consumers']], ['leaf'])

    def test_missing_known_basis_is_incomplete_in_cli_and_saved_summary(self):
        path = self.root / '.agents/skills/leaf/references/upstream-usage.json'
        data = json.loads(path.read_text())
        data['uses'][0]['upstream_basis_revision'] = 'f' * 40
        path.write_text(json.dumps(data))
        captured = io.StringIO()
        with redirect_stdout(captured):
            code = TOOL.main(['--root', str(self.root), '--source', 'engine', '--output', str(self.root / 'tasks/check')])
        summary = json.loads(captured.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(summary['inspection_status'], 'incomplete')
        self.assertEqual(summary['sources'][0]['basis_summary'], {'needs_fetch': 1})
        markdown = Path(summary['report_path']).with_suffix('.md').read_text(encoding='utf-8')
        self.assertIn('incomplete', markdown)
        self.assertIn('needs_fetch=1', markdown)
        data['uses'][0]['upstream_basis_revision'] = None
        path.write_text(json.dumps(data))
        captured = io.StringIO()
        with redirect_stdout(captured):
            code = TOOL.main(['--root', str(self.root), '--source', 'engine'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(captured.getvalue())['inspection_status'], 'review_required')

    def test_missing_explicit_config_fails_while_default_absence_remains_optional(self):
        before = self.git(self.source, 'status', '--porcelain')
        captured = io.StringIO()
        with redirect_stdout(captured):
            code = TOOL.main(['--root', str(self.root), '--source', 'engine', '--config', str(self.root / 'misspelled.yaml')])
        self.assertEqual(code, 2)
        self.assertIn('Explicit --config', json.loads(captured.getvalue())['error'])
        self.assertEqual(before, self.git(self.source, 'status', '--porcelain'))
        (self.root / 'config/workbench.local.yaml').unlink()
        report = self.inspect()
        self.assertEqual(report['sources'][0]['selection_state'], 'pending_decision')
        self.assertEqual(report['sources'][0]['status'], 'no_source_delta')

    def test_orphaned_consumer_manifest_is_a_configuration_error(self):
        (self.root / '.agents/skills/leaf/SKILL.md').unlink()
        with self.assertRaisesRegex(ValueError, 'no SKILL.md'):
            self.inspect()

    def test_provenance_resource_removal_does_not_become_a_runtime_dependency_failure(self):
        path = self.root / '.agents/skills/leaf/references/upstream-usage.json'
        data = json.loads(path.read_text())
        data['uses'][0]['relationship'] = 'provenance'
        path.write_text(json.dumps(data))
        self.git(self.source, 'rm', 'skills/feature/SKILL.md')
        self.commit(self.source)
        candidate = self.git(self.source, 'rev-parse', 'HEAD')
        self.git(self.source, 'checkout', '-q', '--detach', self.base)
        report = self.inspect(candidates={'engine': candidate})
        self.assertEqual(report['sources'][0]['status'], 'changed')
        self.assertEqual(report['affected_consumers'], [])
        self.assertNotIn('missing_resources', report['sources'][0])

    def test_non_string_relation_ids_return_configuration_error_instead_of_traceback(self):
        path = self.root / '.agents/skills/leaf/references/upstream-usage.json'
        original = path.read_text()
        for field in ('source_id', 'relationship'):
            with self.subTest(field=field):
                data = json.loads(original)
                data['uses'][0][field] = []
                path.write_text(json.dumps(data))
                captured = io.StringIO()
                with redirect_stdout(captured):
                    code = TOOL.main(['--root', str(self.root), '--source', 'engine'])
                self.assertEqual(code, 2)
                self.assertEqual(json.loads(captured.getvalue())['status'], 'inspection_error')

    def test_retired_project_provenance_does_not_require_a_current_file_or_snapshot(self):
        path = self.root / '.agents/skills/leaf/references/upstream-usage.json'
        data = json.loads(path.read_text())
        data['uses'].append({'source_id': 'workbench', 'resources': ['retired/method.py'],
                             'relationship': 'provenance', 'when': 'historical method credit',
                             'upstream_basis_revision': None})
        path.write_text(json.dumps(data))
        report = self.inspect()
        self.assertEqual(report['affected_consumers'], [])
        self.assertNotIn('retired/method.py', report['consumer_snapshot'])

    def test_configured_external_source_works_without_a_default_checkout(self):
        external = self.root / 'external engine'
        self.source.rename(external)
        self.write(self.root, 'config/workbench.local.yaml',
                   'schema_version: 1\ndependencies:\n  engine:\n    enabled: true\n    path: "' + external.as_posix() + '"\n')
        report = self.inspect()
        source = report['sources'][0]
        self.assertEqual(source['status'], 'no_source_delta')
        self.assertEqual(Path(source['path']), external)
        self.assertFalse(self.source.exists())
        self.assertEqual(self.git(external, 'status', '--porcelain'), '')

    def test_unknown_or_missing_historical_basis_is_not_filled_with_current_pin(self):
        path = self.root / '.agents/skills/leaf/references/upstream-usage.json'
        data = json.loads(path.read_text())
        data['uses'][0]['upstream_basis_revision'] = None
        path.write_text(json.dumps(data))
        self.assertEqual(self.inspect()['sources'][0]['basis_checks'][0]['status'], 'unknown_basis')
        data['uses'][0]['upstream_basis_revision'] = 'f' * 40
        path.write_text(json.dumps(data))
        self.assertEqual(self.inspect()['sources'][0]['basis_checks'][0]['status'], 'needs_fetch')

    def test_rename_is_preserved_and_old_resource_path_is_reported_missing(self):
        self.git(self.source, 'mv', 'skills/feature/SKILL.md', 'skills/feature/renamed.md')
        self.commit(self.source)
        candidate = self.git(self.source, 'rev-parse', 'HEAD')
        self.git(self.source, 'checkout', '-q', '--detach', self.base)
        source = self.inspect(candidates={'engine': candidate})['sources'][0]
        self.assertEqual(source['status'], 'missing_resource')
        self.assertTrue(source['changes'][0]['status'].startswith('R'))
        self.assertEqual(len(source['changes'][0]['paths']), 2)

    def test_unrelated_source_change_is_conservatively_marked_for_review(self):
        candidate = self.candidate('shared/runtime.py', '# changed shared interface\n')
        report = self.inspect(candidates={'engine': candidate})
        self.assertEqual(report['affected_consumers'][0]['reasons'][0]['reason'],
                         'source_changed_indirect_scope_requires_review')

    def test_wrong_url_or_gitlink_never_reports_a_valid_source(self):
        self.lock['sources']['engine']['url'] = 'https://example.invalid/other/project.git'
        self.save_lock()
        self.assertEqual(self.inspect()['sources'][0]['status'], 'identity_mismatch')
        self.lock['sources']['engine']['url'] = 'https://example.invalid/org/engine.git'
        self.lock['sources']['engine']['commit'] = 'f' * 40
        self.save_lock()
        self.assertEqual(self.inspect()['sources'][0]['status'], 'identity_mismatch')

    def test_external_path_must_be_a_git_root_not_a_subdirectory_falling_back(self):
        self.write(self.root, 'config/workbench.local.yaml',
                   'schema_version: 1\ndependencies:\n  engine:\n    enabled: true\n    path: deps/engine/skills\n')
        self.assertEqual(self.inspect()['sources'][0]['status'], 'identity_mismatch')

    def test_uninitialized_submodule_directory_is_missing_not_the_parent_repository(self):
        self.source.rename(self.root / 'prepared-source')
        self.source.mkdir()
        source = self.inspect()['sources'][0]
        self.assertEqual(source['status'], 'missing_source')
        self.assertNotIn('head_revision', source)
        self.assertNotIn('gitlink_revision', source)

    def test_explicit_disabled_or_missing_decision_never_enables_or_queries_remote(self):
        self.write(self.root, 'config/workbench.local.yaml', 'schema_version: 1\ndependencies:\n  engine:\n    enabled: false\n')
        with mock.patch.object(TOOL, 'remote_head', side_effect=AssertionError('network')):
            self.assertEqual(self.inspect(check_remote=True)['sources'][0]['status'], 'not_enabled')
            self.write(self.root, 'config/workbench.local.yaml', 'schema_version: 1\n')
            source = self.inspect(check_remote=True)['sources'][0]
            self.assertEqual(source['selection_state'], 'pending_decision')
            self.assertEqual(source['remote']['status'], 'pending_decision')

    def test_canonical_upstream_remote_can_identify_a_fork_checkout(self):
        self.git(self.source, 'remote', 'set-url', 'origin', 'https://example.invalid/user/fork.git')
        self.git(self.source, 'remote', 'add', 'upstream', 'git@example.invalid:org/engine.git')
        with mock.patch.object(TOOL, 'remote_head', return_value={'status': 'unavailable'}) as call:
            source = self.inspect(check_remote=True)['sources'][0]
        self.assertEqual(source['status'], 'no_source_delta')
        self.assertEqual(call.call_args.args[1], 'upstream')

    def test_resource_traversal_and_source_id_typos_are_rejected(self):
        path = self.root / '.agents/skills/leaf/references/upstream-usage.json'
        data = json.loads(path.read_text())
        data['uses'][0]['resources'] = ['../../private']
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'escapes'):
            self.inspect()
        data['uses'][0]['resources'] = ['skills/feature/SKILL.md']
        data['uses'][0]['source_id'] = 'wrong_source'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Unknown source'):
            self.inspect()

    def test_yaml_errors_do_not_echo_private_configuration_values(self):
        self.write(self.root, 'config/workbench.local.yaml', 'schema_version: 1\nsecret: [private-token-value\n')
        with self.assertRaises(ValueError) as caught:
            self.inspect()
        self.assertNotIn('private-token-value', str(caught.exception))

    def test_missing_optional_parser_fails_clearly_without_installing(self):
        with mock.patch.object(TOOL, 'yaml', None):
            with self.assertRaisesRegex(ValueError, 'Nothing was installed'):
                self.inspect()

    def test_cli_report_is_bounded_preserves_history_and_rejects_source_output(self):
        report_dir = self.root / 'tasks/check/results'
        for _ in range(2):
            captured = io.StringIO()
            with redirect_stdout(captured):
                code = TOOL.main(['--root', str(self.root), '--source', 'engine', '--output', str(report_dir)])
            self.assertEqual(code, 0)
            summary = json.loads(captured.getvalue())
            self.assertTrue(Path(summary['report_path']).is_file())
            self.assertNotIn('basis_checks', summary)
        self.assertEqual(len(list(report_dir.glob('*.json'))), 2)
        with redirect_stdout(io.StringIO()):
            code = TOOL.main(['--root', str(self.root), '--source', 'engine', '--output', str(self.source / 'reports')])
        self.assertEqual(code, 2)
        self.assertFalse((self.source / 'reports').exists())

    def test_explicit_remote_failure_returns_nonzero_not_up_to_date(self):
        with mock.patch.object(TOOL, 'remote_head', return_value={'status': 'unavailable'}):
            captured = io.StringIO()
            with redirect_stdout(captured):
                code = TOOL.main(['--root', str(self.root), '--source', 'engine', '--check-remote'])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(captured.getvalue())['sources'][0]['remote']['status'], 'unavailable')


if __name__ == '__main__':
    unittest.main()
