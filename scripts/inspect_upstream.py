#!/usr/bin/env python3
"""Inspect selected fixed sources and actual consumers; never fetch or switch them."""
import argparse
from collections import Counter, deque
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import urlsplit

try:
    import yaml
except ImportError:
    yaml = None


RELATIONSHIPS = {
    'skill_call', 'tool_call', 'rule_reference', 'method_reference',
    'template_reference', 'provenance',
}


def load_yaml(path):
    if yaml is None:
        raise ValueError('PyYAML is required for this optional tool; see scripts/requirements-upstream.txt. Nothing was installed.')
    try:
        value = yaml.safe_load(path.read_text(encoding='utf-8-sig'))
    except OSError as exc:
        raise ValueError(f'Cannot read YAML {path.name}: {type(exc).__name__}') from exc
    except yaml.YAMLError as exc:
        mark = getattr(exc, 'problem_mark', None)
        where = f' at line {mark.line + 1}, column {mark.column + 1}' if mark else ''
        raise ValueError(f'Invalid YAML {path.name}{where}') from exc
    if not isinstance(value, dict) or type(value.get('schema_version')) is not int or value['schema_version'] != 1:
        raise ValueError(f'Unsupported configuration schema: {path.name}')
    return value


def git(root, *args, check=True):
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    result = subprocess.run(
        ['git', '-C', str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, timeout=40, check=False,
    )
    if check and result.returncode:
        # Do not echo remote URLs/credentials or arbitrary Git stderr into reports.
        raise ValueError(f'Git {args[0]} failed (exit {result.returncode})')
    return result


def output(root, *args):
    return git(root, *args).stdout.decode('utf-8', errors='replace').strip()


def safe_resource(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise ValueError('Resource must be a source-relative POSIX path')
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {'.', '..'} for part in value.split('/')):
        raise ValueError(f'Resource escapes source: {value}')
    return value


def located(root, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Configured path must be a nonempty string')
    path = Path(value)
    return (path if path.is_absolute() else root / path).resolve()


def normalize_url(value):
    value = value.strip().rstrip('/')
    if '://' in value:
        parsed = urlsplit(value)
        return (parsed.hostname or '').lower() + '/' + parsed.path.lstrip('/').removesuffix('.git')
    match = re.fullmatch(r'(?:[^@/]+@)?([^/:]+):(.+)', value)
    if match:
        return match[1].lower() + '/' + match[2].removesuffix('.git')
    return value.removesuffix('.git')


def revision(root, ref):
    if not isinstance(ref, str) or not ref or '\x00' in ref:
        return None
    result = git(root, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}', check=False)
    return result.stdout.decode().strip() if result.returncode == 0 else None


def changes(root, before, after):
    raw = git(root, 'diff', '--name-status', '-z', '-M', before, after, '--').stdout
    parts = raw.decode('utf-8', errors='replace').rstrip('\x00').split('\x00') if raw else []
    result, index = [], 0
    while index < len(parts):
        status, index = parts[index], index + 1
        count = 2 if status.startswith(('R', 'C')) else 1
        paths = parts[index:index + count]
        if len(paths) != count:
            raise ValueError('Incomplete Git change record')
        index += count
        result.append({'status': status, 'paths': paths})
    return result


def load_consumers(root, source_ids):
    consumers = {}
    tracked = git(root, 'ls-files', '-z', '--', '.agents/skills/*/references/upstream-usage.json').stdout
    paths = set((root / '.agents/skills').glob('*/references/upstream-usage.json'))
    paths.update(root / name for name in tracked.decode('utf-8').split('\x00') if name)
    declared_modules = {path.parent.parent for path in paths}
    for skill in sorted((root / '.agents/skills').glob('*/SKILL.md')):
        if skill.parent not in declared_modules:
            raise ValueError(f'Missing consumer declaration for skill: {skill.parent.name}')
    for path in sorted(paths):
        if not path.is_file():
            raise ValueError(f'Missing tracked consumer declaration: {path.parent.parent.name}')
        if not (path.parent.parent / 'SKILL.md').is_file():
            raise ValueError(f'Consumer has no SKILL.md: {path.parent.parent.name}')
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            raise ValueError(f'Invalid consumer declaration: {path.parent.parent.name}') from exc
        consumer = path.parent.parent.name
        if (not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1 or data.get('consumer') != consumer
                or not isinstance(data.get('uses'), list)):
            raise ValueError(f'Consumer identity/schema mismatch: {consumer}')
        for use in data['uses']:
            if (not isinstance(use, dict) or not isinstance(use.get('source_id'), str)
                    or use['source_id'] not in {*source_ids, 'workbench'}):
                raise ValueError(f'Unknown source in consumer {consumer}')
            if not isinstance(use.get('relationship'), str) or use['relationship'] not in RELATIONSHIPS:
                raise ValueError(f'Unknown relationship in consumer {consumer}')
            resources = use.get('resources')
            if not isinstance(resources, list) or not resources:
                raise ValueError(f'Missing resources in consumer {consumer}')
            for item in resources:
                safe_resource(item)
                if use['source_id'] == 'workbench' and use['relationship'] != 'provenance':
                    target = (root / item).resolve()
                    if not target.is_relative_to(root) or not target.is_file():
                        raise ValueError(f'Missing/escaping project resource in consumer {consumer}')
            if not isinstance(use.get('when'), str) or not use['when'].strip():
                raise ValueError(f'Missing use condition in consumer {consumer}')
            basis = use.get('upstream_basis_revision')
            if basis is not None and (not isinstance(basis, str) or not re.fullmatch(r'[a-fA-F0-9]{40}|[a-fA-F0-9]{64}', basis)):
                raise ValueError(f'Noncanonical historical basis in consumer {consumer}')
        consumers[consumer] = data
    return consumers


def parent_identity(root, relative):
    config = root / '.gitmodules'
    if not config.is_file():
        raise ValueError('Parent .gitmodules is missing')
    names = output(root, 'config', '--file', str(config), '--get-regexp', r'^submodule\..*\.path$')
    matching = []
    for line in names.splitlines():
        key, path = line.split(None, 1)
        if PurePosixPath(path).as_posix() == relative:
            matching.append(key[:-5])
    if len(matching) != 1:
        raise ValueError('Lock path has no unique parent submodule identity')
    urls = output(root, 'config', '--file', str(config), '--get-all', matching[0] + '.url').splitlines()
    if len(urls) != 1:
        raise ValueError('Parent submodule has ambiguous URL declarations')
    url = urls[0]
    rows = output(root, 'ls-files', '--stage', '--', relative).splitlines()
    if len(rows) != 1:
        raise ValueError('Parent has no unique staged gitlink')
    metadata, _ = rows[0].split('\t', 1)
    mode, sha, stage = metadata.split()
    if mode != '160000' or stage != '0':
        raise ValueError('Parent path is not an unconflicted gitlink')
    return url, sha


def remote_head(root, remote):
    try:
        result = git(root, 'ls-remote', '--symref', remote, 'HEAD', check=False)
    except subprocess.TimeoutExpired:
        return {'status': 'unavailable', 'reason': 'timeout'}
    if result.returncode:
        return {'status': 'unavailable', 'exit_code': result.returncode}
    text = result.stdout.decode('utf-8', errors='replace')
    ref = re.search(r'^ref: (\S+)\s+HEAD$', text, re.M)
    sha = re.search(r'^([a-f0-9]{40,64})\s+HEAD$', text, re.M)
    if not (ref and sha):
        return {'status': 'unresolved'}
    return {'status': 'discovered', 'ref': ref[1], 'revision': sha[1]}


def inspect_source(root, source_id, spec, local, candidate, check_remote, consumers):
    relative = safe_resource(spec.get('path'))
    adopted = spec.get('commit')
    if not isinstance(adopted, str) or not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', adopted):
        raise ValueError(f'Invalid locked revision: {source_id}')
    if not isinstance(spec.get('url'), str):
        raise ValueError(f'Missing locked URL: {source_id}')
    if not isinstance(local, dict):
        raise ValueError(f'Invalid source configuration: {source_id}')
    enabled = local.get('enabled')
    if enabled is not None and type(enabled) is not bool:
        raise ValueError(f'Invalid enabled flag: {source_id}')
    selection = 'enabled' if enabled is True else 'not_enabled' if enabled is False else 'pending_decision'
    value = {'source_id': source_id, 'selection_state': selection, 'adopted_revision': adopted,
             'status': 'unchecked', 'changes': [], 'basis_checks': [], 'consumers': [],
             'remote': {'status': 'not_requested'}}
    if enabled is False:
        value['status'] = 'not_enabled'
        return value
    source = located(root, local.get('path', relative))
    value['path'] = str(source)
    if not source.is_dir():
        value['status'] = 'missing_source'
        return value
    try:
        probe = git(source, 'rev-parse', '--show-toplevel', check=False)
        actual_root = Path(probe.stdout.decode('utf-8', errors='replace').strip()).resolve() if probe.returncode == 0 else None
        if actual_root is None or (actual_root == root and source == (root / relative).resolve()):
            value['status'] = 'missing_source'
            value['error'] = 'Source directory has no initialized Git checkout'
            return value
        if actual_root != source:
            raise ValueError('Configured directory is not the actual source Git root')
        parent_url, gitlink = parent_identity(root, relative)
        matches = [name for name in output(source, 'remote').splitlines()
                   if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*', name)
                   and normalize_url(output(source, 'remote', 'get-url', name)) == normalize_url(spec['url'])]
        canonical_remote = 'origin' if 'origin' in matches else matches[0] if matches else None
        head = output(source, 'rev-parse', 'HEAD')
        value.update(head_revision=head, gitlink_revision=gitlink)
        if (normalize_url(parent_url) != normalize_url(spec['url'])
                or canonical_remote is None
                or gitlink != adopted or head != adopted):
            raise ValueError('Lock, parent gitlink, source HEAD or origin disagree')
        value['dirty'] = bool(output(source, 'status', '--porcelain', '--untracked-files=normal'))
        target = adopted
        if check_remote and enabled is True:
            value['remote'] = remote_head(source, canonical_remote)
            if candidate is None and value['remote']['status'] == 'discovered':
                candidate = value['remote']['revision']
        elif check_remote:
            value['remote'] = {'status': 'pending_decision'}
        if candidate is not None:
            target = revision(source, candidate)
            value['candidate_requested'] = candidate
            if target is None:
                value['status'] = 'needs_fetch'
                return value
        value['evaluated_revision'] = target
        value['changes'] = changes(source, adopted, target)
        value['status'] = 'changed' if value['changes'] else 'no_source_delta'
        missing = []
        for name, declaration in consumers.items():
            for use in declaration['uses']:
                if use['source_id'] != source_id:
                    continue
                value['consumers'].append({'consumer': name, 'relationship': use['relationship'],
                                           'resources': use['resources'], 'when': use['when']})
                if use['relationship'] != 'provenance':
                    for resource in use['resources']:
                        found = git(source, 'cat-file', '-e', target + ':' + resource, check=False)
                        if found.returncode:
                            missing.append({'consumer': name, 'resource': resource})
                basis = use.get('upstream_basis_revision')
                item = {'consumer': name, 'relationship': use['relationship'],
                        'resources': use['resources'], 'basis_revision': basis}
                if basis is None:
                    item['status'] = 'unknown_basis'
                elif revision(source, basis) is None:
                    item['status'] = 'needs_fetch'
                else:
                    item['adopted_delta'] = changes(source, basis, adopted)
                    item['candidate_delta'] = changes(source, basis, target)
                    item['status'] = 'basis_matches_target' if basis == target else 'review_delta'
                value['basis_checks'].append(item)
        if missing:
            value['missing_resources'] = missing
            value['status'] = 'missing_resource'
        if value['dirty']:
            value['checkout_state'] = 'modified_source_requires_review'
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        value['status'] = 'identity_mismatch'
        value['error'] = str(exc)
    return value


def affected_consumers(reports, consumers):
    reasons = {}
    for report in reports:
        changed = {p for item in report['changes'] for p in item['paths']}
        if changed or report.get('missing_resources'):
            for use in report['consumers']:
                if use['relationship'] == 'provenance':
                    continue
                direct = any(p == r or p.startswith(str(PurePosixPath(r).parent) + '/')
                             for p in changed for r in use['resources'])
                reasons.setdefault(use['consumer'], []).append({
                    'source_id': report['source_id'], 'relationship': use['relationship'],
                    'reason': 'resource_or_subtree_changed' if direct else 'source_changed_indirect_scope_requires_review',
                })
        for basis in report['basis_checks']:
            if basis['relationship'] != 'provenance' and basis.get('candidate_delta'):
                reasons.setdefault(basis['consumer'], []).append({
                    'source_id': report['source_id'], 'relationship': basis['relationship'],
                    'reason': 'historical_basis_delta_requires_review',
                })
    queue = deque(reasons)
    visited = set()
    while queue:
        callee = queue.popleft()
        if callee in visited:
            continue
        visited.add(callee)
        for caller, declaration in consumers.items():
            for use in declaration['uses']:
                if use['source_id'] != 'workbench' or use['relationship'] == 'provenance':
                    continue
                if any(r.startswith('.agents/skills/' + callee + '/') for r in use['resources']):
                    item = {'via': callee, 'relationship': use['relationship'], 'reason': 'project_consumer_requires_review'}
                    if item not in reasons.setdefault(caller, []):
                        reasons[caller].append(item)
                        queue.append(caller)
    return [{'consumer': name, 'reasons': reasons[name]} for name in sorted(reasons)]


def inspection_state(source):
    """Separate collection completeness from source changes and absorption review."""
    basis = Counter(item['status'] for item in source['basis_checks'])
    incomplete = (source['status'] in {'identity_mismatch', 'missing_resource', 'missing_source', 'needs_fetch'}
                  or source.get('dirty') or source['remote']['status'] in {'unavailable', 'unresolved'}
                  or basis['needs_fetch'])
    review = bool(source['changes'] or basis['unknown_basis'] or basis['review_delta'])
    return {'inspection_status': 'incomplete' if incomplete else 'review_required' if review else 'complete',
            'basis_summary': dict(sorted(basis.items()))}


def inspect(root, selected, candidates=None, config_path=None, check_remote=False):
    root = root.resolve()
    if Path(output(root, 'rev-parse', '--show-toplevel')).resolve() != root:
        raise ValueError('Explicit root must be the workbench Git root')
    if config_path is not None:
        config_path = Path(config_path)
        if not config_path.is_file():
            raise ValueError('Explicit --config must name an existing YAML file')
        config = load_yaml(config_path)
    else:
        config_path = root / 'config/workbench.local.yaml'
        config = load_yaml(config_path) if config_path.exists() or config_path.is_symlink() else {'schema_version': 1}
    paths = config.get('paths', {})
    if not isinstance(paths, dict):
        raise ValueError('paths must be a mapping')
    lock_path = located(root, paths.get('sources_lock', 'upstream/sources.lock.yaml'))
    lock = load_yaml(lock_path)
    sources = lock.get('sources')
    if not isinstance(sources, dict) or not sources:
        raise ValueError('Source lock must contain a nonempty sources mapping')
    if any(not isinstance(sid, str) or not re.fullmatch(r'[a-z][a-z0-9_]*', sid) for sid in sources):
        raise ValueError('Invalid locked source id')
    if any(not isinstance(spec, dict) for spec in sources.values()):
        raise ValueError('Each source declaration must be a mapping')
    selected = sorted(sources) if selected is None else list(dict.fromkeys(selected))
    if any(sid not in sources for sid in selected):
        raise ValueError('Requested source id is not in the authoritative lock')
    candidates = candidates or {}
    if set(candidates) - set(selected):
        raise ValueError('Candidate specified outside the requested source scope')
    consumers = load_consumers(root, sources)
    local = config.get('dependencies', {})
    if not isinstance(local, dict):
        raise ValueError('dependencies must be a mapping')
    if set(local) - set(sources):
        raise ValueError('Configured dependency id is not in the authoritative lock')
    reports = [inspect_source(root, sid, sources[sid], local.get(sid, {}),
                              candidates.get(sid), check_remote, consumers) for sid in selected]
    for source in reports:
        source.update(inspection_state(source))
    states = {source['inspection_status'] for source in reports}
    overall = 'incomplete' if 'incomplete' in states else 'review_required' if 'review_required' in states else 'complete'
    source_roots = []
    for sid, spec in sources.items():
        configured = local.get(sid, {})
        if isinstance(configured, dict):
            value = configured.get('path', spec.get('path'))
            if isinstance(value, str) and value.strip():
                source_roots.append(str(located(root, value)))
    snapshot_paths = set((root / '.agents/skills').glob('*/SKILL.md'))
    snapshot_paths.update((root / '.agents/skills').glob('*/references/upstream-usage.json'))
    for declaration in consumers.values():
        for use in declaration['uses']:
            if use['source_id'] == 'workbench' and use['relationship'] != 'provenance':
                snapshot_paths.update(root / resource for resource in use['resources'])
    snapshot_paths.update(p for p in [root / 'AGENTS.md', root / 'docs/guides/skill-routing.md'] if p.is_file())
    return {
        'schema_version': 1, 'checked_at': datetime.now(timezone.utc).isoformat(),
        'workbench_revision': output(root, 'rev-parse', 'HEAD'),
        'consumer_snapshot': {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(snapshot_paths)},
        'lock_sha256': hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        'source_roots': source_roots,
        'network_requested': check_remote, 'sources': reports,
        'inspection_status': overall,
        'affected_consumers': affected_consumers(reports, consumers),
        'limitations': ['Candidate changes and basis deltas require semantic review; no tool/NPU validation was run.',
                        'Indirect or dynamic resource dependencies are conservative review candidates, not proven unaffected.'],
    }


def save_reports(report, directory):
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination = directory / ('upstream-check-' + stamp)
    destination.with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# 上游检查', '', '检查状态：' + report['inspection_status'], '',
             '| 来源 | 源版本差量 | 检查状态 | 历史依据统计 | 采用版本 | 评估版本 |', '|---|---|---|---|---|---|']
    for source in report['sources']:
        basis = ', '.join(f'{state}={count}' for state, count in source['basis_summary'].items()) or '不适用/未评估'
        lines.append('| ' + ' | '.join([source['source_id'], source['status'], source['inspection_status'], basis, source['adopted_revision'],
                                        source.get('evaluated_revision', '未评估')]) + ' |')
    lines += ['', '变化、选择状态、历史依据、影响及错误见同名JSON；本报告不代表已采用或运行验证。', '']
    destination.with_suffix('.md').write_text('\n'.join(lines), encoding='utf-8')
    return str(destination.with_suffix('.json'))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--config', type=Path)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument('--source', action='append')
    scope.add_argument('--all', action='store_true')
    parser.add_argument('--candidate', action='append', default=[], metavar='SOURCE=LOCAL_REF')
    parser.add_argument('--check-remote', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        candidates = {}
        for item in args.candidate:
            source_id, separator, ref = item.partition('=')
            if not separator or not ref or source_id in candidates:
                raise ValueError('Candidates require one unique SOURCE=LOCAL_REF each')
            candidates[source_id] = ref
        report = inspect(args.root, None if args.all else args.source, candidates,
                         args.config, args.check_remote)
        if args.output:
            destination = args.output.resolve()
            for source_root in report['source_roots']:
                if destination.is_relative_to(Path(source_root)):
                    raise ValueError('Report output cannot be inside a dependency source')
            root = args.root.resolve()
            if destination.is_relative_to(root):
                relative = destination.relative_to(root)
                if not relative.parts or relative.parts[0] not in {'tasks', '.workbench-local'}:
                    raise ValueError('In-workbench reports belong in tasks or .workbench-local')
            filename = save_reports(report, destination)
            print(json.dumps({'report_path': filename,
                              'inspection_status': report['inspection_status'],
                              'sources': [{key: s[key] for key in ('source_id', 'status', 'inspection_status', 'basis_summary')}
                                          for s in report['sources']],
                              'affected_consumers': [c['consumer'] for c in report['affected_consumers']]}, ensure_ascii=False))
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report['inspection_status'] == 'incomplete' else 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status': 'inspection_error', 'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
