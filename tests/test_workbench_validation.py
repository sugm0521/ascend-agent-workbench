"""Published-reference checks use Git membership, including in a clean clone."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('workbench_validation', ROOT / 'scripts/validate_workbench.py')
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        (self.root / '.gitignore').write_text('tasks/\n.workbench-local/\n')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.STDOUT)

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')

    def test_local_existence_cannot_hide_unpublished_evidence(self):
        self.write('README.md', '[Evidence](tasks/evidence.json)')
        self.write('tasks/evidence.json', '{}')
        value = CHECKER.check_links(self.root)
        self.assertEqual(value['errors'][0]['target'], 'tasks/evidence.json')

    def test_marked_local_evidence_and_historical_archives_are_separate(self):
        self.write('README.md', '[Evidence (local-only)](tasks/evidence.json)')
        self.write('tasks/old.md', '[Evidence](../.workbench-local/run.json)')
        self.git('add', '-f', 'tasks/old.md')
        value = CHECKER.check_links(self.root)
        self.assertEqual(value['errors'], [])
        self.assertEqual(len(value['local_only']), 1)
        self.assertEqual(len(value['historical_local_only']), 1)

    def test_local_only_label_cannot_hide_missing_public_document(self):
        self.write('README.md', '[Missing (local-only)](docs/missing.md)')
        self.assertEqual(len(CHECKER.check_links(self.root)['errors']), 1)

    def test_committed_reference_does_not_read_dirty_or_untracked_repairs(self):
        self.write('README.md', '[Missing](docs/new.md)')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        self.write('docs/new.md', '# New')
        self.assertEqual(CHECKER.check_links(self.root)['errors'], [])
        self.assertEqual(len(CHECKER.check_links(self.root, 'HEAD')['errors']), 1)

    def test_dependency_paths_and_fragments_do_not_require_full_initialization(self):
        self.write('README.md', '[dep](deps/optional/SKILL.md) [here](#here) [doc](docs/existing.md#x)')
        self.write('docs/existing.md', '# x')
        value = CHECKER.check_links(self.root)
        self.assertEqual(value['errors'], [])
        self.assertEqual(value['dependency_links_unchecked'], 1)

    def test_incompatible_marked_fails_before_running_suites(self):
        node = shutil.which(os.environ.get('NODE_BINARY', 'node'))
        if not node:
            self.skipTest('Existing Node.js is required for incompatible-module regression')
        self.write('node_modules/marked/index.js', 'module.exports = {};')
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/validate_workbench.py'), '--node', node,
             '--node-modules', str(self.root / 'node_modules')],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('unavailable or incompatible', result.stderr)
        self.assertNotIn('unittest discover', result.stdout)


if __name__ == '__main__':
    unittest.main()
