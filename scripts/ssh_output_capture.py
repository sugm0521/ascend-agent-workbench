"""Bounded output capture for the task's existing SSH channel, no connections."""
import hashlib
import math
import time


class Tail:
    def __init__(self, limit):
        self.limit, self.total = limit, 0
        self.data = bytearray()
        self.digest = hashlib.sha256()

    def add(self, data):
        self.total += len(data)
        self.digest.update(data)
        self.data.extend(data)
        if len(self.data) > self.limit:
            del self.data[:len(self.data) - self.limit]

    def result(self):
        raw = bytes(self.data)
        try:
            text, decoding_error = raw.decode('utf-8'), False
        except UnicodeDecodeError:
            text, decoding_error = raw.decode('utf-8', errors='replace'), True
        return text, {'observed_bytes': self.total, 'retained_bytes': len(raw),
            'truncated': self.total > len(raw), 'retained_utf8_decode_error': decoding_error,
            'observed_sha256': self.digest.hexdigest()}


def command_payload(command, node):
    payload = ('export TASK_NODE=' + str(node) + '\n' + command).encode('utf-8')
    if len(payload) >= 1_000_000:
        raise ValueError('complete upload payload must be smaller than 1MB')
    return payload


def capture_channel(channel, timeout, stdout_limit=262144, stderr_limit=65536):
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be positive and finite')
    if any(not isinstance(n, int) or not 0 <= n <= 786432 for n in (stdout_limit, stderr_limit)):
        raise ValueError('retention limit must be 0..786432 bytes')
    out, err = Tail(stdout_limit), Tail(stderr_limit)
    deadline = time.monotonic() + timeout
    code, status, error = None, 'running', None
    try:
        while True:
            if time.monotonic() >= deadline:
                status = 'timed_out'
                break
            progressed = False
            for _ in range(32):
                ready = False
                if channel.recv_ready():
                    data = channel.recv(8192)
                    if data:
                        out.add(data)
                        ready = progressed = True
                if channel.recv_stderr_ready():
                    data = channel.recv_stderr(8192)
                    if data:
                        err.add(data)
                        ready = progressed = True
                if not ready or time.monotonic() >= deadline:
                    break
            if channel.exit_status_ready() and not channel.recv_ready() and not channel.recv_stderr_ready():
                code = channel.recv_exit_status()
                status = 'exited' if code >= 0 else 'missing_exit_status'
                break
            if getattr(channel, 'closed', False):
                status = 'missing_exit_status'
                break
            if not progressed:
                time.sleep(min(0.02, max(0, deadline - time.monotonic())))
    except Exception as exc:
        status, error = 'transport_error', type(exc).__name__ + ': ' + str(exc)
    if status != 'exited':
        channel.close()
    stdout, out_meta = out.result()
    stderr, err_meta = err.result()
    result = {'stdout': stdout, 'stderr': stderr, 'stdout_capture': out_meta,
        'stderr_capture': err_meta, 'command_status': status, 'command_exit_code': code,
        'exit_code': code if code is not None else -1, 'business_completion': 'not_checked',
        'output_complete': status == 'exited' and not any(
            m['truncated'] or m['retained_utf8_decode_error'] for m in (out_meta, err_meta))}
    if error:
        result['error'] = error
    if status != 'exited':
        result['remote_process_state'] = 'unknown'
    return result
