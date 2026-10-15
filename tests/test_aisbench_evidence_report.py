import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('evidence_report', ROOT / 'scripts/aisbench_evidence_report.py')
reporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reporter)


def sample(i=0, content='Answer: A', finish='stop', reasoning='', gold='A'):
    return {'id': i, 'uuid': 'u' + str(i), 'prediction': content, 'gold': gold, 'success': True,
        'request': {'max_tokens': 100, 'temperature': 1},
        'response': {'choices': [{'message': {'content': content, 'reasoning_content': reasoning},
                                 'finish_reason': finish}], 'usage': {'completion_tokens': 12}}}


class EvidenceReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.sequence = 0

    def tearDown(self):
        self.temp.cleanup()

    def run_report(self, rows, changes=None, flags=None):
        self.sequence += 1
        source = self.root / f'samples{self.sequence}.jsonl'
        with source.open('w', encoding='utf-8') as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + '\n')
        run = {'id': 'round1', 'samples': str(source), 'format': 'samples', 'expected_count': len(rows),
            'parser': {'type': 'choice', 'pattern': r'Answer:\s*([A-Z])\b', 'choices': ['A', 'B', 'C', 'D'],
                       'source': 'final_content'}, 'expected_request': {'max_tokens': 100, 'temperature': 1}}
        run.update(changes or {})
        manifest = self.root / f'spec{self.sequence}.json'
        manifest.write_text(json.dumps({'runs': [run]}), encoding='utf-8')
        destination = self.root / f'out{self.sequence}'
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            rc = reporter.main(['--spec', str(manifest), '--output-dir', str(destination), *(flags or [])])
        result = json.loads((destination / 'report.json').read_text()) if (destination / 'report.json').exists() else None
        return rc, result, destination, stdout.getvalue(), stderr.getvalue()

    def test_normal_and_official_metrics_preserved(self):
        official = self.root / 'official.json'
        original = b'{"accuracy":100.0,"extract_rate":100.0,"api_key":"NEVER_EXPORT"}'
        official.write_bytes(original)
        rc, report, _, stdout, _ = self.run_report([sample()], {'official_result': str(official)})
        self.assertEqual(rc, 0)
        self.assertEqual(report['aggregate']['valid_answer'], 1)
        self.assertEqual(report['groups'][0]['official']['metrics'], {'accuracy': 100.0, 'extract_rate': 100.0})
        self.assertEqual(official.read_bytes(), original)
        self.assertNotIn('NEVER_EXPORT', json.dumps(report) + stdout)

    def test_stop_without_answer_is_candidate_not_truncation(self):
        rc, report, _, _, _ = self.run_report([sample(content='Let us compute (x =')])
        self.assertEqual(rc, 0)  # Report complete; model quality is not an automatic pass.
        self.assertEqual(report['aggregate']['flag:stop_without_valid_answer_candidate'], 1)
        self.assertNotIn('flag:reported_length_limit', report['aggregate'])
        self.assertNotIn('abnormal_truncation', json.dumps(report))

    def test_length_is_distinct_from_stop(self):
        _, report, _, _, _ = self.run_report([sample(finish='length')])
        self.assertEqual(report['aggregate']['flag:reported_length_limit'], 1)
        self.assertNotIn('flag:stop_without_valid_answer_candidate', report['aggregate'])

    def test_reasoning_only_has_empty_final_content(self):
        _, report, _, _, _ = self.run_report([sample(content='', reasoning='Still deriving v4=(0,0,-')])
        self.assertEqual(report['aggregate']['flag:empty_final_content'], 1)
        self.assertEqual(report['aggregate']['valid_answer'], 0)

    def test_bad_characters_and_legitimate_unicode(self):
        rc, report, path, _, _ = self.run_report([sample(reasoning='stereoc\ufffdenter\x1f')], flags=['--audit-output'])
        self.assertEqual(rc, 0)
        row = json.loads((path / 'round1.samples.jsonl').read_text())
        self.assertEqual(row['phases']['reasoning']['bad_characters'], {'U+FFFD': 1, 'U+001F': 1})
        _, good, _, _, _ = self.run_report([sample(reasoning='中文解释 αβγ ΔE')], flags=['--audit-output'])
        self.assertNotIn('flag:reasoning:bad_characters', good['aggregate'])

    def test_surrogate_in_json_is_reportable_without_encode_failure(self):
        row = sample(reasoning='bad\ud800')
        # The JSON on disk legitimately escapes the invalid surrogate.
        path = self.root / 'surrogate.json'
        path.write_text(json.dumps([row]), encoding='utf-8')
        rc, report, _, _, _ = self.run_report([], {'samples': str(path), 'expected_count': 1}, ['--audit-output'])
        self.assertEqual(rc, 0)
        self.assertEqual(report['aggregate']['flag:reasoning:bad_characters'], 1)

    def test_known_token_is_separate_from_math_lookalike(self):
        _, report, path, _, _ = self.run_report([sample(reasoning='<|media_content|> and <|v_i - v_j|>')],
            {'known_special_tokens': ['<|media_content|>']}, ['--audit-output'])
        row = json.loads((path / 'round1.samples.jsonl').read_text())
        self.assertEqual(row['phases']['reasoning']['known_special_token_text'], {'<|media_content|>': 1})
        self.assertEqual(row['phases']['reasoning']['unclassified_token_like_text'], {'<|v_i - v_j|>': 1})

    def test_repeated_sequence_is_only_candidate(self):
        sentence = 'MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPPVAPAPAA' * 2
        _, report, _, _, _ = self.run_report([sample(reasoning='\n'.join([sentence] * 3))], flags=['--audit-output'])
        self.assertEqual(report['aggregate']['flag:reasoning:repetition_candidate'], 1)
        self.assertNotIn('dead_loop', json.dumps(report))

    def test_bounded_examples_and_stdout(self):
        rows = [sample(i, content='No final answer ' + 'λ' * 10000) for i in range(12)]
        rc, report, _, stdout, _ = self.run_report(rows, flags=['--example-budget-bytes', '200', '--stdout-budget-bytes', '2048'])
        self.assertEqual(rc, 0)
        self.assertLessEqual(report['groups'][0]['examples']['bytes'], 200)
        self.assertLessEqual(len(stdout.encode()), 2048)

    def test_expected_count_and_duplicates_are_incomplete(self):
        rc, report, _, _, _ = self.run_report([sample()], {'expected_count': 2})
        self.assertEqual(rc, 1)
        self.assertFalse(report['all_reports_complete'])
        rc, report, _, _, _ = self.run_report([sample(), sample()])
        self.assertEqual(rc, 1)
        self.assertEqual(report['aggregate']['flag:duplicate_id'], 1)
        self.assertEqual(report['aggregate']['flag:duplicate_uuid'], 1)

    def test_missing_or_mismatched_request_is_incomplete(self):
        row = sample()
        row['request']['temperature'] = 0
        rc, report, _, _, _ = self.run_report([row])
        self.assertEqual(rc, 1)
        self.assertEqual(report['aggregate']['flag:request_parameter_mismatch'], 1)
        row.pop('request')
        rc, report, _, _, _ = self.run_report([row])
        self.assertEqual(rc, 1)
        self.assertEqual(report['aggregate']['flag:missing_request_evidence'], 1)

    def test_unicode_line_separator_does_not_split_jsonl(self):
        rc, report, _, _, _ = self.run_report([sample(reasoning='a\u2028b'), sample(1)])
        self.assertEqual(rc, 0)
        self.assertEqual(report['aggregate']['samples'], 2)

    def test_explicit_regex_parser_for_non_choice_dataset(self):
        row = sample(content='Result: 42', gold='42')
        rc, report, _, _, _ = self.run_report([row], {'parser': {'type': 'regex', 'pattern': r'Result:\s*(\d+)', 'source': 'final_content'}})
        self.assertEqual(rc, 0)
        self.assertEqual(report['aggregate_independent_format_score_percent'], 100)

    def test_nonempty_parser_does_not_invent_accuracy(self):
        rc, report, _, _, _ = self.run_report([sample()], {'parser': {'type': 'nonempty', 'source': 'final_content'}})
        self.assertEqual(rc, 0)
        self.assertIsNone(report['aggregate_independent_format_score_percent'])

    def test_aisbench_nested_jsonl_and_ambiguous_retries(self):
        path = self.root / 'nested.jsonl'
        row = sample()
        path.write_text(json.dumps({'0': {k: row[k] for k in ['id', 'uuid', 'prediction', 'gold', 'success']}}) + '\n', encoding='utf-8')
        evidence = self.root / 'api'
        evidence.mkdir()
        for suffix in ['first', 'retry']:
            (evidence / (suffix + '.request.json')).write_text(json.dumps({'output_uuid': 'u0', **row['request']}))
            (evidence / (suffix + '.response.json')).write_text(json.dumps(row['response']))
        rc, report, _, _, _ = self.run_report([], {'format': 'aisbench', 'samples': str(path), 'expected_count': 1, 'evidence_dir': str(evidence)})
        self.assertEqual(rc, 1)
        self.assertEqual(report['aggregate']['flag:ambiguous_successful_responses'], 1)
        self.assertEqual(report['groups'][0]['request_attempts'], 2)

    def test_missing_response_evidence(self):
        evidence = self.root / 'api'
        evidence.mkdir()
        (evidence / 'first.request.json').write_text(json.dumps({'output_uuid': 'u0'}))
        rc, report, _, _, _ = self.run_report([sample()], {'evidence_dir': str(evidence)})
        self.assertEqual(rc, 1)
        self.assertEqual(report['aggregate']['flag:missing_response_evidence'], 1)

    def test_aisbench_mapping_preserves_outer_id_in_json_and_jsonl(self):
        row = {'id': 0, 'prediction': 'A', 'gold': 'A', 'success': True}
        without_id = {k: v for k, v in row.items() if k != 'id'}
        for suffix, obj in [('.json', {'0': without_id, '1': {**row, 'id': 1}}),
                            ('.jsonl', {'0': without_id, '1': {**row, 'id': '1'}}),
                            ('.json', [row, {**row, 'id': 1}])]:
            with self.subTest(suffix=suffix, obj=obj):
                path = self.root / ('mapping' + suffix)
                original = json.dumps(obj).encode() + b'\n'
                path.write_bytes(original)
                rc, report, output, _, _ = self.run_report([], {
                    'format': 'aisbench', 'samples': str(path), 'expected_count': 2,
                    'expected_request': {}, 'parser': {'type': 'choice', 'choices': ['A', 'B'],
                                                       'source': 'prediction'}})
                self.assertEqual(rc, 0, report)
                self.assertEqual(report['groups'][0]['unique_ids'], 2)
                rows = [json.loads(line) for line in (output / 'round1.samples.jsonl').read_text().splitlines()]
                self.assertEqual([str(item['id']) for item in rows], ['0', '1'])
                self.assertEqual(report['aggregate_independent_format_score_percent'], 100)
                self.assertEqual(path.read_bytes(), original)

    def test_aisbench_invalid_or_conflicting_ids_are_visible_incomplete_inputs(self):
        row = {'prediction': 'A', 'gold': 'A', 'success': True}
        invalid = [{'0': {**row, 'id': 1}}, {'': row}, {'0': None},
                   *[{**row, 'id': key} for key in [None, '', '  ', True, [], {}, 0.5]],
                   *[{'0': {**row, 'id': key}} for key in [None, '', True, [], {}, 0.0]]]
        for suffix in ['.json', '.jsonl']:
            for obj in invalid:
                with self.subTest(suffix=suffix, obj=obj):
                    path = self.root / ('invalid' + suffix)
                    path.write_text(json.dumps(obj) + '\n', encoding='utf-8')
                    rc, report, _, _, _ = self.run_report([], {
                        'format': 'aisbench', 'samples': str(path), 'expected_count': 1,
                        'expected_request': {}, 'parser': {'type': 'choice', 'choices': ['A', 'B']}})
                    self.assertEqual(rc, 1)
                    self.assertFalse(report['all_reports_complete'])
                    self.assertTrue(report['groups'][0]['issues'])
                    self.assertEqual(report['groups'][0]['unique_ids'], 0)

    def test_mapping_key_can_be_the_string_id(self):
        path = self.root / 'named-id.jsonl'
        path.write_text('{"id":{"prediction":"A","gold":"A"}}\n')
        rc, report, output, _, _ = self.run_report([], {
            'format': 'aisbench', 'samples': str(path), 'expected_count': 1,
            'expected_request': {}, 'parser': {'type': 'choice', 'choices': ['A', 'B']}})
        self.assertEqual(rc, 0, report)
        self.assertEqual(json.loads((output / 'round1.samples.jsonl').read_text())['id'], 'id')
        for fmt in ['samples', 'answer-index']:
            rows = list(reporter.records(path, fmt))
            self.assertEqual(rows, [{'id': {'prediction': 'A', 'gold': 'A'}}])

    def test_aisbench_duplicate_json_keys_do_not_silently_select_a_record(self):
        for suffix in ['.json', '.jsonl']:
            path = self.root / ('duplicates' + suffix)
            path.write_text('{"0":{"prediction":"A"},"0":{"prediction":"B"}}\n')
            rc, report, _, _, _ = self.run_report([], {
                'format': 'aisbench', 'samples': str(path), 'expected_count': 1})
            self.assertEqual(rc, 1)
            self.assertIn('duplicate AISBench JSON key', str(report['groups'][0]['issues']))

    def test_aisbench_mapping_cli_exit_codes(self):
        for inner_id, expected_rc in [(None, 0), (1, 1)]:
            row = {'prediction': 'A', 'gold': 'A', 'success': True}
            if inner_id is not None:
                row['id'] = inner_id
            source = self.root / 'cli-mapping.jsonl'
            source.write_text(json.dumps({'0': row}) + '\n')
            spec = self.root / 'cli-spec.json'
            spec.write_text(json.dumps({'runs': [{
                'id': 'round1', 'format': 'aisbench', 'samples': str(source), 'expected_count': 1,
                'parser': {'type': 'choice', 'choices': ['A', 'B']}}]}))
            output = self.root / f'cli-output-{expected_rc}'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/aisbench_evidence_report.py'),
                                     '--spec', str(spec), '--output-dir', str(output)],
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, expected_rc, result.stderr)
            report = json.loads((output / 'report.json').read_text())
            self.assertEqual(report['all_reports_complete'], expected_rc == 0)

    def test_malformed_input_is_not_reported_as_empty_success(self):
        path = self.root / 'bad.jsonl'
        path.write_bytes(b'{"broken":\xff}\n')
        rc, report, _, _, _ = self.run_report([], {'samples': str(path), 'expected_count': 1})
        self.assertEqual(rc, 1)
        self.assertTrue(report['groups'][0]['issues'])

    def test_answer_index_marks_scope_as_recorded_not_raw(self):
        rows = [{'id': 0, 'predicted': 'A', 'gold': 'A', 'success': True, 'finish_reason': 'stop', 'completion_tokens': 7}]
        rc, report, path, _, _ = self.run_report(rows, {'format': 'answer-index', 'expected_request': {},
            'parser': {'type': 'choice', 'choices': ['A', 'B'], 'source': 'prediction'}})
        self.assertEqual(rc, 0)
        row = json.loads((path / 'round1.samples.jsonl').read_text())
        self.assertEqual(row['evidence_kind'], 'prediction_or_recorded_index')
        self.assertEqual(report['aggregate_independent_format_score_percent'], 100)

    def test_multiple_groups_are_reported_before_weighted_aggregate(self):
        paths = []
        for i, rows in enumerate([[sample()], [sample(), sample(1, gold='B')]]):
            path = self.root / f'g{i}.jsonl'
            path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
            paths.append(path)
        runs = [{'id': f'g{i}', 'samples': str(path), 'expected_count': i + 1,
                 'parser': {'type': 'choice', 'choices': ['A', 'B'], 'pattern': r'Answer:\s*([AB])',
                            'source': 'final_content'}} for i, path in enumerate(paths)]
        spec = self.root / 'multi.json'
        spec.write_text(json.dumps({'runs': runs}))
        destination = self.root / 'multi-output'
        with contextlib.redirect_stdout(io.StringIO()):
            rc = reporter.main(['--spec', str(spec), '--output-dir', str(destination)])
        report = json.loads((destination / 'report.json').read_text())
        self.assertEqual(rc, 0)
        self.assertEqual([g['independent_format_score_percent'] for g in report['groups']], [100, 50])
        self.assertAlmostEqual(report['aggregate_independent_format_score_percent'], 200 / 3)

    def test_non_string_final_content_is_invalid_schema_not_empty_text(self):
        row = sample()
        row['response']['choices'][0]['message']['content'] = 0
        rc, report, _, _, _ = self.run_report([row])
        self.assertEqual(rc, 1)
        self.assertEqual(report['aggregate']['flag:invalid_response_schema'], 1)

    def test_missing_parameter_is_not_the_same_as_explicit_null(self):
        rc, report, _, _, _ = self.run_report([sample()], {'expected_request': {'seed': None}})
        self.assertEqual(rc, 1)
        self.assertEqual(report['aggregate']['flag:request_parameter_mismatch'], 1)


if __name__ == '__main__':
    unittest.main()
