import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ssh_capture', ROOT / 'tasks/1014/scripts/ssh_output_capture.py')
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


class Channel:
    def __init__(self, out=b'', err=b'', code=0, wait_forever=False):
        self.out, self.err = bytearray(out), bytearray(err)
        self.code, self.wait_forever, self.closed = code, wait_forever, False
        self.stdout_reads, self.stderr_reads = 0, 0

    def recv_ready(self):
        return bool(self.out)

    def recv_stderr_ready(self):
        return bool(self.err)

    def recv(self, n):
        self.stdout_reads += 1
        data = bytes(self.out[:n])
        del self.out[:n]
        return data

    def recv_stderr(self, n):
        self.stderr_reads += 1
        data = bytes(self.err[:n])
        del self.err[:n]
        return data

    def exit_status_ready(self):
        return not self.wait_forever and not self.out and not self.err

    def recv_exit_status(self):
        return self.code

    def close(self):
        self.closed = True


class ChannelCaptureTests(unittest.TestCase):
    def test_complete_small_json_and_separate_business_status(self):
        row = capture.capture_channel(Channel(b'{"status":"running"}\n'), 1)
        self.assertTrue(row['output_complete'])
        self.assertEqual(row['command_exit_code'], 0)
        self.assertEqual(row['business_completion'], 'not_checked')

    def test_large_dual_stream_is_fully_drained_with_bounded_tails(self):
        out, err = b'a' * 1_048_576, b'e' * 700_000
        channel = Channel(out, err)
        row = capture.capture_channel(channel, 2, 262144, 65536)
        self.assertEqual(len(channel.out) + len(channel.err), 0)
        for key, data, limit in [('stdout', out, 262144), ('stderr', err, 65536)]:
            meta = row[key + '_capture']
            self.assertEqual(meta['observed_bytes'], len(data))
            self.assertEqual(meta['retained_bytes'], limit)
            self.assertEqual(meta['observed_sha256'], hashlib.sha256(data).hexdigest())
            self.assertTrue(meta['truncated'])
        self.assertFalse(row['output_complete'])
        self.assertGreater(channel.stdout_reads, 1)
        self.assertGreater(channel.stderr_reads, 1)

    def test_nonzero_exit_is_preserved(self):
        row = capture.capture_channel(Channel(b'failed', code=7), 1)
        self.assertEqual(row['command_exit_code'], 7)
        self.assertTrue(row['output_complete'])

    def test_timeout_marks_remote_process_unknown_and_closes_channel(self):
        channel = Channel(wait_forever=True)
        row = capture.capture_channel(channel, 0.025)
        self.assertEqual(row['command_status'], 'timed_out')
        self.assertIsNone(row['command_exit_code'])
        self.assertEqual(row['remote_process_state'], 'unknown')
        self.assertFalse(row['output_complete'])
        self.assertTrue(channel.closed)

    def test_missing_exit_status_is_not_success(self):
        row = capture.capture_channel(Channel(code=-1), 1)
        self.assertEqual(row['command_status'], 'missing_exit_status')
        self.assertFalse(row['output_complete'])

    def test_invalid_utf8_and_zero_retention_are_visible(self):
        row = capture.capture_channel(Channel(b'\xff'), 1)
        self.assertTrue(row['stdout_capture']['retained_utf8_decode_error'])
        self.assertFalse(row['output_complete'])
        row = capture.capture_channel(Channel(b'abc'), 1, 0, 0)
        self.assertEqual(row['stdout_capture']['observed_bytes'], 3)
        self.assertTrue(row['stdout_capture']['truncated'])

    def test_upload_limit_includes_node_prefix_and_utf8_bytes(self):
        with self.assertRaises(ValueError):
            capture.command_payload('x' * 999999, 21)
        self.assertLess(len(capture.command_payload('λ' * 100, 21)), 1_000_000)


if __name__ == '__main__':
    unittest.main()
