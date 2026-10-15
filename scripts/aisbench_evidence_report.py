#!/usr/bin/env python3
"""Read explicit evaluation runs; report metrics, format validity and audit candidates.

Standard library only. No remote execution, scoring-policy changes or model imports.
The output is evidence, not a correctness pass or a diagnosis of an engine failure.
"""
from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
import unicodedata

REQUEST_FIELDS = {'model', 'max_tokens', 'temperature', 'top_p', 'reasoning_effort',
                  'stream', 'seed', 'ignore_eos'}
TOKEN_LIKE = re.compile(r'<\|[^\n<>]{1,60}\|>|</?(?:think|analysis|final)>')


def read_json(path):
    with Path(path).open(encoding='utf-8') as handle:
        return json.load(handle)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while data := handle.read(786432):
            value.update(data)
    return value.hexdigest()


def encoded(value):
    # ASCII escaping also preserves malformed surrogate code points for review.
    return json.dumps(value, ensure_ascii=True, separators=(',', ':')).encode('utf-8')


def file_info(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest(path)}


def aisbench_object(pairs):
    """Reject ambiguous JSON objects instead of silently keeping the last ID."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate AISBench JSON key: {key!r}')
        result[key] = value
    return result


def aisbench_records(obj):
    def valid_id(value):
        return type(value) is int or (isinstance(value, str) and bool(value.strip()))

    if not isinstance(obj, dict):
        raise ValueError('AISBench sample or ID mapping must be an object')
    if 'id' in obj and not all(isinstance(value, dict) for value in obj.values()):
        if not valid_id(obj['id']):
            raise ValueError('invalid AISBench sample ID: expected a nonempty string or integer')
        yield obj
        return
    for key, row in obj.items():
        if not valid_id(key) or not isinstance(row, dict):
            raise ValueError('invalid AISBench ID mapping: expected nonempty IDs and object records')
        if 'id' in row and (not valid_id(row['id']) or str(row['id']) != key):
            raise ValueError(f'AISBench mapping ID conflicts with inner ID or is invalid: {key!r}')
        yield {**row, 'id': row.get('id', key)}


def records(path, fmt):
    """JSONL is split on actual LF only, never Unicode str.splitlines()."""
    if fmt not in {'aisbench', 'samples', 'answer-index'}:
        raise ValueError('format must be aisbench, samples or answer-index')
    if path.suffix == '.jsonl':
        with path.open(encoding='utf-8') as handle:
            for line in handle:
                if line.strip():
                    obj = json.loads(line, object_pairs_hook=aisbench_object if fmt == 'aisbench' else None)
                    if fmt == 'aisbench':
                        yield from aisbench_records(obj)
                    else:
                        yield obj
    else:
        if fmt == 'aisbench':
            with path.open(encoding='utf-8') as handle:
                obj = json.load(handle, object_pairs_hook=aisbench_object)
            for item in obj if isinstance(obj, list) else [obj]:
                yield from aisbench_records(item)
        else:
            obj = read_json(path)
            if isinstance(obj, dict) and 'id' in obj:
                yield obj
            else:
                yield from obj if isinstance(obj, list) else obj.values()


def parse_answer(text, parser):
    kind = parser.get('type')
    if kind == 'nonempty':
        return None, bool(text.strip()), []
    if kind not in {'choice', 'regex'}:
        raise ValueError('parser.type must be choice, regex or nonempty')
    if parser.get('pattern'):
        pattern = re.compile(parser['pattern'])
        if pattern.groups != 1:
            raise ValueError('answer pattern must contain exactly one capture group')
        matches = pattern.findall(text)
    else:
        matches = [text.strip()] if text.strip() else []
    if parser.get('normalize') == 'upper':
        matches = [x.strip().upper() for x in matches]
    else:
        matches = [x.strip() for x in matches]
    if kind == 'choice':
        choices = parser.get('choices')
        if not isinstance(choices, list) or not choices or any(not isinstance(x, str) for x in choices):
            raise ValueError('choice parser requires explicit choices')
        valid = bool(matches) and matches[-1] in choices
    else:
        valid = bool(matches) and bool(matches[-1])
    return matches[-1] if valid else None, valid, matches


def audit_text(text, known_tokens):
    bad = Counter('U+%04X' % ord(c) for c in text if c == '\ufffd'
        or unicodedata.category(c) in {'Cs', 'Co'}
        or (unicodedata.category(c) == 'Cc' and c not in '\r\n\t'))
    invisible = Counter('U+%04X' % ord(c) for c in text
        if ord(c) in {0x200b, 0x200c, 0x200d, 0x200e, 0x200f, 0x202a, 0x202b,
                      0x202c, 0x202d, 0x202e, 0x2066, 0x2067, 0x2068, 0x2069, 0xfeff})
    candidates = TOKEN_LIKE.findall(text)
    # Only explicit caller-supplied tokens count as known special-token text.
    known = Counter({token: text.count(token) for token in known_tokens if token in text})
    sentences = Counter(re.sub(r'\s+', ' ', s).strip() for s in
        re.split(r'(?<=[.!?])\s+|\n+', text) if len(s.strip()) >= 80)
    repeated = [(s, n) for s, n in sentences.items() if n >= 3]
    words = text.split()
    windows = Counter(' '.join(words[i:i + 32]) for i in range(max(0, len(words) - 31)))
    repeat_max = windows.most_common(1)[0][1] if windows else 0
    return {'chars': len(text), 'bad_characters': dict(bad), 'invisible_characters': dict(invisible),
        'known_special_token_text': dict(known),
        'unclassified_token_like_text': dict(Counter(x for x in candidates if x not in known_tokens)),
        'repetition_candidate': bool(repeated) or repeat_max >= 4,
        'max_32word_repeat': repeat_max,
        'repeated_sentence_candidates': [{'count': n, 'excerpt': s[:160]} for s, n in repeated[:2]]}


def load_evidence(directory):
    by_uuid, issues, requests = {}, [], 0
    for path in sorted(directory.glob('*.request.json')):
        requests += 1
        try:
            request = read_json(path)
            key = request['output_uuid']
            if not isinstance(key, str) or not key:
                raise ValueError('invalid output_uuid')
            response_path = path.with_name(path.name.replace('.request.json', '.response.json'))
            response = read_json(response_path) if response_path.exists() else None
            by_uuid.setdefault(key, []).append((request, response, response_path))
        except (ValueError, KeyError, OSError) as exc:
            issues.append({'path': str(path), 'error': str(exc)[:300]})
    return by_uuid, issues, requests


def resolve(base, name):
    path = Path(name)
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def run_report(spec, base, destination, options):
    run_id = spec['id']
    parser = spec['parser']
    parse_answer('', parser)  # Validate before reading a large run.
    path = resolve(base, spec['samples'])
    fmt = spec.get('format', 'samples')
    expected = spec.get('expected_count')
    if expected is not None and (type(expected) is not int or expected <= 0):
        raise ValueError('expected_count must be a positive integer')
    settings = spec.get('expected_request', {})
    if set(settings) - REQUEST_FIELDS:
        raise ValueError('expected_request may contain generation fields only')
    known_tokens = spec.get('known_special_tokens', [])
    if not isinstance(known_tokens, list) or any(not isinstance(t, str) or not t for t in known_tokens):
        raise ValueError('known_special_tokens must be nonempty strings')
    known_tokens = set(known_tokens)
    api, issues, request_count = {}, [], 0
    if spec.get('evidence_dir'):
        api, issues, request_count = load_evidence(resolve(base, spec['evidence_dir']))
    counts, finishes = Counter(), Counter()
    ids, uuids, tokens = set(), set(), []
    examples_bytes = example_count = 0
    samples_path = destination / (run_id + '.samples.jsonl')
    examples_path = destination / (run_id + '.examples.jsonl')
    with samples_path.open('xb') as rows_out, examples_path.open('xb') as examples:
        try:
            for row in records(path, fmt):
                counts['samples'] += 1
                if not isinstance(row, dict):
                    issues.append({'row': counts['samples'], 'error': 'sample is not an object'})
                    continue
                key = row.get('id', row.get('question_number'))
                flags = []
                if key is None or isinstance(key, (list, dict)):
                    flags.append('missing_or_invalid_id')
                elif str(key) in ids:
                    flags.append('duplicate_id')
                else:
                    ids.add(str(key))
                uid = row.get('uuid')
                if uid:
                    if uid in uuids:
                        flags.append('duplicate_uuid')
                    uuids.add(uid)
                request, response = row.get('request'), row.get('response')
                if spec.get('evidence_dir'):
                    attempts = api.get(uid, [])
                    successful = [a for a in attempts if a[1] is not None]
                    counts['attempts_for_samples'] += len(attempts)
                    if len(successful) == 1:
                        request, response, _ = successful[0]
                    elif len(successful) > 1:
                        flags.append('ambiguous_successful_responses')
                        request = response = None  # Do not silently pick a retry.
                    else:
                        flags.append('missing_response_evidence')
                content, reasoning, finish, completion = None, '', None, None
                if response is not None:
                    try:
                        choice = response['choices'][0]
                        message = choice['message']
                        content = message.get('content')
                        content = '' if content is None else content
                        reasoning = message.get('reasoning_content', message.get('reasoning'))
                        reasoning = '' if reasoning is None else reasoning
                        if not isinstance(content, str) or not isinstance(reasoning, str):
                            raise ValueError('response text fields must be strings')
                        finish = choice.get('finish_reason')
                        completion = response.get('usage', {}).get('completion_tokens')
                        counts['response_evidence'] += 1
                    except (KeyError, IndexError, TypeError, ValueError):
                        flags.append('invalid_response_schema')
                        content, reasoning = None, ''
                elif fmt == 'answer-index':
                    finish, completion = row.get('finish_reason'), row.get('completion_tokens')
                prediction = row.get('prediction', row.get('predicted'))
                source = parser.get('source', 'prediction')
                if source == 'final_content':
                    text = content if content is not None else ''
                elif source == 'prediction':
                    text = prediction if isinstance(prediction, str) else ''
                else:
                    raise ValueError('parser.source must be prediction or final_content')
                answer, valid, matches = parse_answer(text, parser)
                counts['valid_answer'] += valid
                if not valid:
                    flags.append('missing_valid_final_answer')
                if len(set(matches)) > 1:
                    flags.append('conflicting_answer_candidates')
                gold = row.get('gold')
                if answer is not None and gold is not None:
                    gold = str(gold).strip()
                    if parser.get('normalize') == 'upper':
                        gold = gold.upper()
                    counts['independent_scored'] += 1
                    counts['independent_correct'] += answer == gold
                elif gold is not None and parser['type'] != 'nonempty':
                    counts['independent_scored'] += 1
                if row.get('success') is True:
                    counts['prediction_success'] += 1
                elif row.get('success') is False:
                    flags.append('prediction_failure')
                if content is not None:
                    counts['final_content_observed'] += 1
                    if not content.strip():
                        flags.append('empty_final_content')
                    counts['final_content_nonempty'] += bool(content.strip())
                if finish is not None:
                    finishes[str(finish)] += 1
                if finish == 'length':
                    flags.append('reported_length_limit')
                if finish == 'stop' and not valid:
                    flags.append('stop_without_valid_answer_candidate')
                if type(completion) is int and completion >= 0:
                    tokens.append(completion)
                mismatches = {}
                if settings:
                    if not isinstance(request, dict):
                        flags.append('missing_request_evidence')
                    else:
                        mismatches = {k: {'expected': v, 'actual': request.get(k)}
                                      for k, v in settings.items() if k not in request or request[k] != v}
                        if mismatches:
                            flags.append('request_parameter_mismatch')
                        else:
                            counts['request_parameters_verified'] += 1
                phases = {}
                if options.audit_output:
                    if content is None:
                        flags.append('raw_output_audit_unavailable')
                    else:
                        for name, value in [('content', content), ('reasoning', reasoning)]:
                            check = audit_text(value, known_tokens)
                            phases[name] = check
                            for field in ['bad_characters', 'invisible_characters', 'known_special_token_text',
                                          'unclassified_token_like_text', 'repetition_candidate']:
                                if check[field]:
                                    flags.append(name + ':' + field)
                counts.update('flag:' + f for f in set(flags))
                result = {'id': key, 'uuid': uid, 'answer': answer, 'valid_answer': valid,
                    'finish_reason': finish, 'completion_tokens': completion,
                    'evidence_kind': 'raw_response' if content is not None else 'prediction_or_recorded_index',
                    'flags': flags, 'parameter_mismatches': mismatches, 'phases': phases}
                rows_out.write(encoded(result) + b'\n')
                if flags and example_count < options.max_examples:
                    # No request body, headers, credentials or full long response.
                    example = {'id': key, 'flags': flags, 'content_tail': (content or text)[-600:],
                               'reasoning_tail': reasoning[-600:]}
                    data = encoded(example) + b'\n'
                    if examples_bytes + len(data) <= options.example_budget_bytes:
                        examples.write(data)
                        examples_bytes += len(data)
                        example_count += 1
        except (ValueError, OSError) as exc:
            issues.append({'path': str(path), 'error': str(exc)[:300]})
    if spec.get('evidence_dir'):
        unlinked = sorted(set(api) - uuids)
        if unlinked:
            issues.append({'error': 'request UUIDs not linked to samples', 'count': len(unlinked)})
    fatal_flags = ['missing_or_invalid_id', 'duplicate_id', 'duplicate_uuid',
        'missing_response_evidence', 'ambiguous_successful_responses', 'invalid_response_schema',
        'request_parameter_mismatch', 'missing_request_evidence', 'prediction_failure']
    integrity = not issues and all(not counts['flag:' + f] for f in fatal_flags)
    if expected is not None and (counts['samples'] != expected or len(ids) != expected):
        issues.append({'error': 'sample count/unique ID count differs from expected',
                       'expected': expected, 'samples': counts['samples'], 'unique_ids': len(ids)})
        integrity = False
    official = None
    if spec.get('official_result'):
        official_path = resolve(base, spec['official_result'])
        try:
            raw = read_json(official_path)
            if not isinstance(raw, dict):
                raise ValueError('official result must be an object')
            if any(isinstance(v, float) and not math.isfinite(v) for v in raw.values()):
                raise ValueError('official numeric metrics must be finite')
            official = {'source': file_info(official_path), 'metrics': {
                key: raw[key] for key in spec.get('official_metric_keys', ['accuracy', 'extract_rate',
                    'accuracy_percent', 'correct', 'samples']) if key in raw and isinstance(raw[key], (int, float))}}
        except (ValueError, OSError) as exc:
            issues.append({'error': 'official result unreadable', 'detail': str(exc)[:300]})
            integrity = False
    return {'id': run_id, 'report_integrity': 'complete' if integrity else 'incomplete',
        'samples_source': file_info(path), 'format': fmt, 'expected_count': expected,
        'observed_count': counts['samples'], 'unique_ids': len(ids),
        'counts': dict(counts), 'finish_reasons': dict(finishes), 'official': official,
        'independent_format_score_percent': 100 * counts['independent_correct'] / counts['independent_scored']
            if counts['independent_scored'] else None,
        'completion_tokens': {'observed': len(tokens), 'total': sum(tokens),
            'max': max(tokens, default=None), 'median': statistics.median(tokens) if tokens else None},
        'request_attempts': request_count, 'issues': issues,
        'samples_report': file_info(samples_path), 'examples': file_info(examples_path),
        'examples_count': example_count, 'audit_output': options.audit_output,
        'known_tokens_declared': len(known_tokens),
        'conclusion_scope': 'Measurement and review candidates only; not a precision pass, truncation diagnosis or logic proof'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--audit-output', action='store_true')
    parser.add_argument('--example-budget-bytes', type=int, default=65536)
    parser.add_argument('--max-examples', type=int, default=8)
    parser.add_argument('--stdout-budget-bytes', type=int, default=16384)
    options = parser.parse_args(argv)
    try:
        if not 0 <= options.example_budget_bytes < 1_000_000 or not 0 <= options.max_examples <= 1000:
            raise ValueError('invalid example budget/count')
        if not 512 <= options.stdout_budget_bytes < 1_000_000:
            raise ValueError('stdout budget must be 512..999999')
        spec = read_json(options.spec)
        runs = spec['runs']
        if not isinstance(runs, list) or not runs:
            raise ValueError('spec.runs must be a nonempty list')
        ids = [r['id'] for r in runs]
        if len(set(ids)) != len(ids) or any(not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', i) for i in ids):
            raise ValueError('run IDs must be unique safe identifiers')
        # Never overwrite prior report evidence or evaluate the newest run implicitly.
        options.output_dir.mkdir(parents=True, exist_ok=False)
        summaries = [run_report(r, options.spec.resolve().parent, options.output_dir, options) for r in runs]
        counts = Counter()
        for group in summaries:
            counts.update(group['counts'])
        report = {'schema_version': 1, 'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
            'groups': summaries, 'aggregate': dict(counts),
            'aggregate_independent_format_score_percent': 100 * counts['independent_correct'] / counts['independent_scored']
                if counts['independent_scored'] else None,
            'all_reports_complete': all(g['report_integrity'] == 'complete' for g in summaries),
            'policy': 'Preserve official metrics; anomalies are review candidates; no automatic model-quality pass'}
        report_path = options.output_dir / 'report.json'
        report_path.write_bytes(encoded(report) + b'\n')
        table = ['# Evaluation evidence', '', '| Run | Samples | Valid answers | Official metrics | Integrity |',
                 '|---|---:|---:|---|---|']
        for g in summaries:
            table.append(f"| {g['id']} | {g['observed_count']} | {g['counts'].get('valid_answer', 0)} | "
                         f"{json.dumps(g['official']['metrics']) if g['official'] else 'unavailable'} | {g['report_integrity']} |")
        table += ['', 'Aggregate: ' + json.dumps(dict(counts)), '', report['policy']]
        (options.output_dir / 'report.md').write_text('\n'.join(table) + '\n', encoding='utf-8')
        summary = {'status': 'generated' if report['all_reports_complete'] else 'incomplete',
            'groups': len(summaries), 'samples': counts['samples'], 'report': file_info(report_path),
            'summary_markdown': str(options.output_dir / 'report.md')}
        if len(encoded(summary)) > options.stdout_budget_bytes:
            raise ValueError('control-plane summary exceeds stdout budget; use a shorter output path')
        print(encoded(summary).decode('ascii'))
        return 0 if report['all_reports_complete'] else 1
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({'status': 'configuration_or_input_error', 'error': str(exc)[:300]}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
