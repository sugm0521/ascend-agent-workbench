import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gpqa_prepare', ROOT / 'scripts/gpqa_batch_prepare.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


class BatchPrepareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'old'
        files = {'configs/models/kimi_gpqa.py': "models=[dict(model='kimi',max_out_len=81920)]\n",
            'configs/datasets/gpqa_diamond.py': f"path={str(self.source / 'dataset/gpqa')!r}\n",
            'setup/observed_api.py': f"root={str(self.source / 'api-evidence')!r}\n"}
        for name, text in files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        data = self.source / 'dataset/gpqa/gpqa_diamond.csv'
        data.parent.mkdir(parents=True, exist_ok=True)
        data.write_text('Question,Correct Answer\nexample,A\n')
        manifest = {'dataset': str(data), 'dataset_sha256': hashlib.sha256(data.read_bytes()).hexdigest(),
            'config_hashes': {name: hashlib.sha256((self.source / name).read_bytes()).hexdigest() for name in files},
            'samples': 1, 'settings': {'max_tokens': 81920, 'temperature': 1, 'top_p': 1}}
        (self.source / 'setup/eval-manifest.json').write_text(json.dumps(manifest))
        self.collector = ROOT / 'scripts/gpqa_collect_run.py'

    def tearDown(self):
        self.temp.cleanup()

    def test_fresh_groups_preserve_parameters_and_redirect_only_paths(self):
        target = self.root / 'new'
        plan = json.loads(prepare.prepare(self.source, target, 3, self.collector).read_text())
        self.assertEqual(len(plan['groups']), 3)
        for group in plan['groups']:
            root = Path(group['root'])
            namespace = {}
            exec((root / 'setup/observed_api.py').read_text(), namespace)
            self.assertEqual(namespace['root'], str(root / 'api-evidence'))
            namespace = {}
            exec((root / 'configs/models/kimi_gpqa.py').read_text(), namespace)
            self.assertEqual(namespace['models'][0]['max_out_len'], 81920)
            self.assertEqual(group['expected_result']['settings']['temperature'], 1)
            self.assertEqual((root / 'dataset/gpqa/gpqa_diamond.csv').read_bytes(),
                             (self.source / 'dataset/gpqa/gpqa_diamond.csv').read_bytes())
        self.assertFalse((target / 'state.json').exists())

    def test_source_config_change_or_existing_target_is_rejected(self):
        (self.source / 'configs/models/kimi_gpqa.py').write_text('models=[]')
        with self.assertRaises(ValueError):
            prepare.prepare(self.source, self.root / 'new', 2, self.collector)
        self.assertFalse((self.root / 'new').exists())

    def test_existing_target_is_not_overwritten(self):
        target = self.root / 'new'
        prepare.prepare(self.source, target, 1, self.collector)
        with self.assertRaises(ValueError):
            prepare.prepare(self.source, target, 1, self.collector)


if __name__ == '__main__':
    unittest.main()
