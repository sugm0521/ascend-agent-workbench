"""Render fresh GPQA groups from a verified previous config, not nested code strings."""
import argparse
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import sys


class RunPaths(ast.NodeTransformer):
    def __init__(self, source, target):
        self.source, self.target = str(source), str(target)

    def visit_Constant(self, node):
        if isinstance(node.value, str) and (node.value == self.source or node.value.startswith((self.source + '/', self.source + '\\'))):
            node.value = self.target + node.value[len(self.source):]
        return node


def prepare(source, target, groups, collector, health_urls=()):
    source, target, collector = source.resolve(), target.resolve(), collector.resolve()
    if target.exists() or target.is_relative_to(source):
        raise ValueError('choose a fresh independent output root')
    if not 1 <= groups <= 100 or not collector.is_file():
        raise ValueError('invalid group count or missing collector')
    manifest = json.loads((source / 'setup/eval-manifest.json').read_text())
    data = Path(manifest['dataset'])
    if not data.is_absolute():
        data = source / data
    if hashlib.sha256(data.read_bytes()).hexdigest() != manifest['dataset_sha256']:
        raise ValueError('source dataset changed')
    files = ['configs/models/kimi_gpqa.py', 'configs/datasets/gpqa_diamond.py', 'setup/observed_api.py']
    for name in files:
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != manifest['config_hashes'][name]:
            raise ValueError('source config changed: ' + name)
    target.mkdir(parents=True)
    plan = {'groups': [], 'health_urls': list(health_urls), 'source_run': str(source)}
    for number in range(1, groups + 1):
        root = target / f'group{number:02d}'
        for name in ['configs/models', 'configs/datasets', 'setup', 'api-evidence', 'results', 'eval', 'dataset/gpqa']:
            (root / name).mkdir(parents=True, exist_ok=True)
        copied_data = root / 'dataset/gpqa' / data.name
        shutil.copyfile(data, copied_data)
        for name in files:
            tree = RunPaths(source, root).visit(ast.parse((source / name).read_text()))
            text = ast.unparse(ast.fix_missing_locations(tree)) + '\n'
            compile(text, name, 'exec')
            (root / name).write_text(text, encoding='utf-8')
        launch = ('#!/bin/bash\nset -o pipefail\n'
            'unset ftp_proxy FTP_PROXY https_proxy HTTPS_PROXY http_proxy HTTP_PROXY all_proxy ALL_PROXY\n'
            'root=' + shlex.quote(str(root)) + '\n'
            'export PYTHONPATH="$root/setup${PYTHONPATH:+:$PYTHONPATH}"\ncd "$root"\n'
            'ais_bench --config-dir "$root/configs" --models kimi_gpqa --datasets gpqa_diamond '
            '--mode all --work-dir "$root/eval" --num-warmups 0 --dump-eval-details --dump-extract-rate\n'
            'rc=$?\nprintf \'{"exit_code": %d}\\n\' "$rc" > "$root/setup/exit.json"\nexit "$rc"\n')
        (root / 'run_eval.sh').write_text(launch, encoding='utf-8')
        # Do not relabel the previous service/client snapshot as current evidence.
        current = {k: manifest[k] for k in ['samples', 'settings', 'dataset_sha256', 'api_url'] if k in manifest}
        current.update(group=number, source_run=str(source), run_root=str(root), dataset=str(copied_data),
                       prepared_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                       source_manifest_sha256=hashlib.sha256((source / 'setup/eval-manifest.json').read_bytes()).hexdigest(),
                       runtime_evidence_scope='Source config only; verify current service/client before starting')
        current['config_hashes'] = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                  for name in files + ['run_eval.sh']}
        (root / 'setup/eval-manifest.json').write_text(json.dumps(current, indent=2), encoding='utf-8')
        plan['groups'].append({'id': f'group{number:02d}', 'root': str(root), 'command': ['bash', str(root / 'run_eval.sh')],
            'collect': [sys.executable, str(collector), '--root', str(root), '--expected-samples', str(manifest['samples'])],
            'result': 'results/eval-summary.json', 'expected_result': {'samples': manifest['samples'],
                'prediction_successes': manifest['samples'], 'settings': manifest['settings']}})
    path = target / 'batch-plan.json'
    path.write_text(json.dumps(plan, indent=2), encoding='utf-8')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run', required=True, type=Path)
    parser.add_argument('--output-root', required=True, type=Path)
    parser.add_argument('--groups', required=True, type=int)
    parser.add_argument('--collector', type=Path, default=Path(__file__).with_name('gpqa_collect_run.py'))
    parser.add_argument('--health-url', action='append', default=[])
    args = parser.parse_args()
    print(json.dumps({'status': 'prepared_only', 'plan': str(prepare(args.source_run, args.output_root,
            args.groups, args.collector, args.health_url)), 'groups': args.groups}))


if __name__ == '__main__':
    main()
