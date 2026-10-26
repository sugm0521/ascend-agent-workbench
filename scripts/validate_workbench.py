#!/usr/bin/env python3
"""Run local regression suites and check repository document references; no network."""
import argparse
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'\[([^\]\n]*)\]\(([^)\n]+)\)')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode('utf-8')


def check_links(root, ref=None):
    """Check candidate files or an explicit committed tree, never disk existence alone."""
    paths = (git(root, 'ls-tree', '-r', '--name-only', '-z', ref) if ref else
             git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard'))
    known = set(paths.rstrip('\0').split('\0')) - {''}
    if not ref:
        known = {p for p in known if (root / p).exists() or (root / p).is_symlink()}
    result = {'errors': [], 'dependency_links_unchecked': 0, 'checked': 0}
    for source in sorted(known):
        if not source.endswith('.md') or source.startswith('deps/'):
            continue
        text = (git(root, 'show', ref + ':' + source) if ref else
                (root / source).read_text(encoding='utf-8'))
        for match in LINK.finditer(text):
            label, href = match.groups()
            href = href.split('#', 1)[0]
            if not href or re.match(r'^(?:https?|mailto):', href, re.I):
                continue
            item = {'source': source, 'line': text[:match.start()].count('\n') + 1, 'target': href}
            if re.match(r'^(?:[A-Za-z]:[\\/]|file:)', href, re.I) or 'local-only' in label:
                result['errors'].append(item)
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(href)))
            item['target'] = target
            if target.startswith('.workbench-local/'):
                result['errors'].append(item)
                continue
            if target.startswith('deps/'):
                result['dependency_links_unchecked'] += 1
                continue
            result['checked'] += 1
            if target in known or any(p.startswith(target + '/') for p in known):
                continue
            result['errors'].append(item)
    return result


def run(command, env):
    print('+ ' + ' '.join(map(str, command)), flush=True)
    return subprocess.run(list(map(str, command)), cwd=ROOT, env=env).returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', help='existing Node.js executable; otherwise NODE_BINARY/PATH')
    parser.add_argument('--node-modules', type=Path, help='existing package directory containing marked')
    parser.add_argument('--skill-validator', type=Path, help='existing skill-creator quick_validate.py (optional)')
    parser.add_argument('--links-only', action='store_true', help='only check document references')
    parser.add_argument('--links-ref', help='committed Git ref for document checks; tests still use current files')
    args = parser.parse_args(argv)
    try:
        links = check_links(ROOT, args.links_ref)
        print(json.dumps({'document_links': links}, ensure_ascii=False), flush=True)
        if links['errors']:
            return 1
        if args.links_only:
            return 0
        env = os.environ.copy()
        node = args.node or env.get('NODE_BINARY') or shutil.which('node')
        if not node:
            raise ValueError('Node.js is missing; supply --node. No runtime was installed.')
        env['NODE_BINARY'] = node
        if args.node_modules:
            if not args.node_modules.is_dir():
                raise ValueError('--node-modules must be an existing package directory')
            env['NODE_PATH'] = str(args.node_modules.resolve()) + (os.pathsep + env['NODE_PATH'] if env.get('NODE_PATH') else '')
        probe = "const {Marked,Renderer}=require('marked'); if(typeof Marked!=='function'||typeof Renderer!=='function') process.exit(1)"
        if run([node, '-e', probe], env):
            raise ValueError('marked is unavailable or incompatible; run npm ci --ignore-scripts in the workbench root. Existing installations may use --node-modules or NODE_PATH. No package was installed.')
        if args.skill_validator and not args.skill_validator.is_file():
            raise ValueError('--skill-validator must point to an existing quick_validate.py')
        # Root discovery includes renderer behavior and the synthetic HCCL suite.
        checks = [run([sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], env)]
        if args.skill_validator:
            checks += [run([sys.executable, '-X', 'utf8', args.skill_validator.resolve(), skill.parent], env)
                       for skill in sorted((ROOT / '.agents/skills').glob('*/SKILL.md'))]
        else:
            print('Skill-creator format validation: not requested; supply --skill-validator to include it.', flush=True)
        return 1 if any(checks) else 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print('Validation prerequisite/read error: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
