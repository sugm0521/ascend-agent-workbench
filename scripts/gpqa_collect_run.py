"""Collect one explicitly selected GPQA run; original AISBench scoring is retained."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics


def collect(root, expected_samples=None):
    # These imports belong to the existing accuracy client's AISBench environment.
    from ais_bench.benchmark.datasets import GPQA_Simple_Eval_postprocess, GPQAEvaluator
    from ais_bench.benchmark.utils.postprocess.model_postprocessors import extract_non_reasoning_content
    manifest = json.loads((root / 'setup/eval-manifest.json').read_text())
    expected = expected_samples if expected_samples is not None else manifest['samples']
    exit_state = json.loads((root / 'setup/exit.json').read_text())
    if exit_state['exit_code'] != 0:
        raise ValueError('evaluation did not exit normally')
    experiments = [p for p in (root / 'eval').iterdir() if p.is_dir() and (p / 'predictions').exists()]
    if len(experiments) != 1:
        raise ValueError('choose a run root with one explicit experiment')
    experiment = experiments[0]
    prediction_files = list((experiment / 'predictions').glob('*/GPQA_diamond.jsonl'))
    result_files = list((experiment / 'results').glob('*/GPQA_diamond.json'))
    if len(prediction_files) != 1 or len(result_files) != 1:
        raise ValueError('prediction/result selection is ambiguous')
    predictions = []
    with prediction_files[0].open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                obj = json.loads(line)
                predictions.extend([obj] if 'id' in obj else obj.values())
    predictions.sort(key=lambda r: r['id'])
    if len(predictions) != expected or len({r['id'] for r in predictions}) != expected:
        raise ValueError('question count/identity mismatch')
    official = json.loads(result_files[0].read_text())
    answers = [GPQA_Simple_Eval_postprocess(extract_non_reasoning_content(r['prediction'])) for r in predictions]
    score = GPQAEvaluator().score(answers, [r['gold'] for r in predictions])
    if abs(score['accuracy'] - official['accuracy']) > 1e-8:
        raise ValueError('official and independently recomputed GPQA scores differ')
    evidence = {}
    for path in sorted((root / 'api-evidence').glob('*.request.json')):
        response_path = path.with_name(path.name.replace('.request.json', '.response.json'))
        if response_path.exists():
            request = json.loads(path.read_text())
            evidence.setdefault(request['output_uuid'], []).append(
                (request, json.loads(response_path.read_text()), str(response_path)))
    settings = manifest['settings']
    expected_fields = {k: settings[k] for k in ['max_tokens', 'temperature', 'top_p', 'reasoning_effort', 'stream'] if k in settings}
    rows, tokens, finishes = [], [], Counter()
    for prediction, answer in zip(predictions, answers):
        responses = evidence.get(prediction['uuid'], [])
        if len(responses) != 1:
            raise ValueError('missing or ambiguous response evidence; inspect retries')
        request, response, path = responses[0]
        if any(request.get(k) != v for k, v in expected_fields.items()):
            raise ValueError('actual request parameters differ from manifest')
        choice = response['choices'][0]
        content = choice['message'].get('content') or ''
        options = re.findall(r'(?i)ANSWER\s*:\s*([A-D])\b', content)
        length = response.get('usage', {}).get('completion_tokens', 0)
        tokens.append(length)
        finishes[choice.get('finish_reason')] += 1
        rows.append({'id': prediction['id'], 'uuid': prediction['uuid'],
            'question_number': prediction['id'] + 1, 'predicted': answer, 'gold': prediction['gold'],
            'correct': answer == prediction['gold'], 'valid_option': answer in ['A', 'B', 'C', 'D'],
            'final_content_option': options[-1] if options else None,
            'success': prediction.get('success', True), 'completion_tokens': length,
            'finish_reason': choice.get('finish_reason'), 'response_path': path})
    if len(evidence) != expected or any(not r['success'] for r in rows):
        raise ValueError('unexpected response IDs or failed predictions')
    summary = {'finished_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'samples': expected,
        'successful_response_evidence': len(rows), 'prediction_successes': sum(r['success'] for r in rows),
        'correct': sum(r['correct'] for r in rows), 'accuracy_percent': score['accuracy'],
        'official_extract_rate': official.get('extract_rate'), 'valid_option_count': sum(r['valid_option'] for r in rows),
        'invalid_question_numbers': [r['question_number'] for r in rows if not r['valid_option']],
        'final_content_missing_option_questions': [r['question_number'] for r in rows if not r['final_content_option']],
        'finish_reasons': dict(finishes), 'completion_tokens': {'min': min(tokens),
            'max': max(tokens), 'median': statistics.median(tokens), 'total': sum(tokens)},
        'settings': settings, 'experiment': str(experiment), 'official_result': str(result_files[0]),
        'official_result_bytes': result_files[0].stat().st_size,
        'official_result_sha256': hashlib.sha256(result_files[0].read_bytes()).hexdigest(),
        'predictions_path': str(prediction_files[0]), 'exit': exit_state,
        'service_url': manifest.get('api_url'), 'services_retained': True,
        'output_quality_scope': 'stop is not text completeness; audit candidates separately'}
    output = root / 'results'
    output.mkdir(exist_ok=True)
    # A collector is invoked once per fresh attempt, never overwrites prior evidence.
    for name, value in [('eval-summary.json', summary), ('answers.json', rows)]:
        with (output / name).open('x', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=True, indent=2)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--expected-samples', type=int)
    args = parser.parse_args()
    summary = collect(args.root.resolve(), args.expected_samples)
    print(json.dumps({'status': 'collected', 'samples': summary['samples'],
                      'accuracy_percent': summary['accuracy_percent'],
                      'summary_path': str(args.root / 'results/eval-summary.json')}))


if __name__ == '__main__':
    main()
