"""External knowledge binding and public candidate-tree boundaries; no network."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('knowledge_validation', ROOT / 'scripts/validate_workbench.py')
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class KnowledgeLocationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.parent = Path(self.temp.name)
        self.public = self.parent / 'public'
        self.public.mkdir()
        self.private = self.parent / 'personal-notes' / 'project-knowledge'
        self.private.mkdir(parents=True)

    def test_unconfigured_does_not_select_or_create_public_directory(self):
        for value in [None, '', '   ']:
            self.assertEqual(VALIDATOR.check_knowledge_location(self.public, value)['status'], 'not_configured')
        self.assertFalse((self.public / 'knowledge').exists())

    def test_relative_binding_supports_each_developers_external_directory(self):
        result = VALIDATOR.check_knowledge_location(self.public, '../personal-notes/project-knowledge', 'topics/new.md')
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(Path(result['target']), (self.private / 'topics/new.md').resolve())
        self.assertFalse(result['target_exists'])
        self.assertFalse((self.private / 'topics').exists())

    def test_existing_entry_is_only_read(self):
        p = self.private / 'entry.md'
        p.write_text('manual note', encoding='utf-8')
        result = VALIDATOR.check_knowledge_location(self.public, self.private, 'entry.md')
        self.assertEqual(result['status'], 'ready')
        self.assertTrue(result['target_exists'])
        self.assertEqual(p.read_text(encoding='utf-8'), 'manual note')

    def test_missing_binding_has_no_public_fallback(self):
        result = VALIDATOR.check_knowledge_location(self.public, self.parent / 'missing')
        self.assertEqual(result['status'], 'unavailable')
        self.assertFalse((self.parent / 'missing').exists())

    def test_public_workbench_is_never_a_private_binding(self):
        for p in [self.public, self.public / 'knowledge', self.public / '.workbench-local/knowledge']:
            self.assertEqual(VALIDATOR.check_knowledge_location(self.public, p)['status'], 'unavailable')

    def test_entry_cannot_escape_or_be_absolute(self):
        for entry in ['../other-note.md', '../../public/new.md', str(self.parent / 'absolute.md')]:
            self.assertEqual(VALIDATOR.check_knowledge_location(self.public, self.private, entry)['status'], 'unavailable')

    def test_symlink_escape_is_rejected(self):
        link = self.private / 'outside'
        try:
            link.symlink_to(self.public, target_is_directory=True)
        except OSError:
            self.skipTest('directory symlinks unavailable on this platform/account')
        self.assertEqual(VALIDATOR.check_knowledge_location(self.public, self.private, 'outside/new.md')['status'], 'unavailable')


@unittest.skipUnless(shutil.which('git'), 'Git required for candidate tree checks')
class PublicKnowledgeTreeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q')
        (self.repo / 'knowledge').mkdir()
        (self.repo / 'knowledge/README.md').write_text('# Generic connection and evidence protocol\n', encoding='utf-8')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.PIPE).decode().strip()

    def test_public_protocol_works_without_private_config(self):
        self.assertEqual(VALIDATOR.check_links(self.repo)['errors'], [])

    def test_explicit_initial_template_is_allowed_but_other_template_content_is_not(self):
        folder = self.repo / 'knowledge/templates'
        folder.mkdir()
        (folder / 'AGENTS.example.md').write_text('# Initial rules\n', encoding='utf-8')
        self.assertEqual(VALIDATOR.check_links(self.repo)['errors'], [])
        (folder / 'experiment.md').write_text('# Private evidence\n', encoding='utf-8')
        errors = VALIDATOR.check_links(self.repo)['errors']
        self.assertTrue(any(x.get('source') == 'knowledge/templates/experiment.md'
                            and x.get('kind') == 'private_knowledge_content' for x in errors))

    def test_new_engineering_content_is_rejected(self):
        p = self.repo / 'knowledge/topics/experiment.md'
        p.parent.mkdir()
        p.write_text('# Must stay private\n', encoding='utf-8')
        self.assertTrue(any(x.get('kind') == 'private_knowledge_content' for x in VALIDATOR.check_links(self.repo)['errors']))

    def test_committed_tree_cannot_hide_content_behind_ignore_or_disk_deletion(self):
        p = self.repo / 'knowledge/history/old.md'
        p.parent.mkdir()
        p.write_text('# Private historical content\n', encoding='utf-8')
        self.git('add', 'knowledge')
        tree = self.git('write-tree')
        p.unlink()
        (self.repo / '.gitignore').write_text('/knowledge/history/\n', encoding='utf-8')
        errors = VALIDATOR.check_links(self.repo, tree)['errors']
        self.assertTrue(any(x.get('kind') == 'private_knowledge_content' for x in errors))
