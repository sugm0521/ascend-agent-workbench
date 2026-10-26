"""Task-local sequential evaluation driver, explicit plans and conservative resume.

Manages only its own client commands; never controls the model service or cards.
Failed/unknown groups require a new explicit attempt, not automatic resubmission.
"""
import argparse
from contextlib import contextmanager
import ctypes
import datetime as dt
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
import urllib.request


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.partial')
    try:
        with temporary.open('w', encoding='utf-8') as handle:
            json.dump(value, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def identity(pid):
    """PID plus process creation identity, not PID existence alone."""
    if sys.platform.startswith('linux'):
        try:
            stat = Path(f'/proc/{pid}/stat').read_text()
            fields = stat[stat.rfind(')') + 2:].split()
            return {'pid': pid, 'starttime': fields[19],
                    'state': 'gone' if fields[0] == 'Z' else 'running'}
        except FileNotFoundError:
            return {'pid': pid, 'state': 'gone'}
        except (OSError, IndexError):
            return {'pid': pid, 'state': 'unknown'}
    if os.name == 'nt':
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return {'pid': pid, 'state': 'gone' if ctypes.get_last_error() == 87 else 'unknown'}
        try:
            exit_code = wintypes.DWORD()
            times = [wintypes.FILETIME() for _ in range(4)]
            if not kernel.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]) or not kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return {'pid': pid, 'state': 'unknown'}
            return {'pid': pid, 'starttime': str((times[0].dwHighDateTime << 32) + times[0].dwLowDateTime),
                    'state': 'running' if exit_code.value == 259 else 'gone'}
        finally:
            kernel.CloseHandle(handle)
    return {'pid': pid, 'state': 'unknown'}


def same_live(saved):
    current = identity(saved['pid'])
    if current['state'] == 'unknown':
        raise ValueError('process identity is unknown; do not resubmit')
    return current['state'] == 'running' and current.get('starttime') == saved.get('starttime')


def result_path(group):
    root = Path(group['root']).resolve()
    path = (root / group['result']).resolve()
    if not path.is_relative_to(root):
        raise ValueError('group result must stay within its root')
    return path


def validate_result(group):
    path = result_path(group)
    value = json.loads(path.read_text())
    for key, expected in group.get('expected_result', {}).items():
        if value.get(key) != expected:
            raise ValueError('result does not meet declared field: ' + key)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_plan(plan):
    groups = plan['groups']
    if not isinstance(groups, list) or not groups:
        raise ValueError('plan needs explicit groups')
    ids, roots = [], []
    for group in groups:
        ids.append(group['id'])
        roots.append(str(Path(group['root']).resolve()))
        if not Path(group['root']).is_dir():
            raise ValueError('prepare each group root before starting')
        if not isinstance(group['command'], list) or not group['command'] or any(not isinstance(a, str) for a in group['command']):
            raise ValueError('command must be an explicit argv list')
        if group.get('collect') and (not isinstance(group['collect'], list) or any(not isinstance(a, str) for a in group['collect'])):
            raise ValueError('collect must be argv')
        if not group.get('expected_result'):
            raise ValueError('declare result validation, not merely a process exit')
        result_path(group)
    if len(set(ids)) != len(ids) or len(set(roots)) != len(roots):
        raise ValueError('groups require unique IDs and independent roots')


@contextmanager
def state_lock(state_path):
    """Hold one OS lock across validation, ownership transfer, and all writes.

    Keep the sidecar file: unlinking it lets a later opener lock a different
    inode while another process still holds the old one. The OS releases the
    lock when the supervisor exits, including an unhandled process crash.
    """
    lock_path = state_path.with_name(state_path.name + '.lock')
    with lock_path.open('a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            if handle.seek(0, os.SEEK_END) == 0:
                handle.write(b'\0')
                handle.flush()
            handle.seek(0)
            acquire = lambda: msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            release = lambda: msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            acquire = lambda: fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            release = lambda: fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        try:
            acquire()
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise ValueError('supervisor is already running (state lock busy)') from exc
            raise
        try:
            yield
        finally:
            release()


def supervise(plan_path, state_path, resume=False):
    plan_path, state_path = plan_path.resolve(), state_path.resolve()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_lock(state_path):
        return _supervise_locked(plan_path, state_path, resume)


def _supervise_locked(plan_path, state_path, resume):
    raw = plan_path.read_bytes()
    plan = json.loads(raw)
    validate_plan(plan)
    plan_sha = hashlib.sha256(raw).hexdigest()
    if state_path.exists():
        if not resume:
            raise ValueError('state already exists; inspect or explicitly resume')
        state = json.loads(state_path.read_text())
        if state['plan_sha256'] != plan_sha:
            raise ValueError('plan changed; create a new attempt')
        if len(state['groups']) != len(plan['groups']) or any(
                old['id'] != group['id'] for old, group in zip(state['groups'], plan['groups'])):
            raise ValueError('state group identities do not match plan')
        if state.get('status') == 'running' and same_live(state['owner']):
            raise ValueError('supervisor is already running')
        # Validate every existing group before sending ANY additional requests.
        for group, previous in zip(plan['groups'], state['groups']):
            if previous['status'] == 'completed':
                if validate_result(group) != previous['result_sha256']:
                    raise ValueError('completed result changed; inspect before resume')
            elif previous['status'] != 'pending':
                if previous.get('process') and same_live(previous['process']):
                    raise ValueError('client command is still running; track instead of duplicate')
                raise ValueError('failed or unknown group; preserve it and use a new explicit attempt')
    else:
        if any(result_path(g).exists() or any((Path(g['root']) / p).exists() for p in
                ['setup/aisbench.log', 'setup/start.json', 'setup/exit.json', 'evaluate.client.log', 'collect.client.log'])
                for g in plan['groups']):
            raise ValueError('existing result without matching state; inspect rather than relaunch')
        state = {'plan_sha256': plan_sha, 'started_at': now(), 'status': 'running',
                 'owner': identity(os.getpid()),
                 'groups': [{'id': g['id'], 'status': 'pending'} for g in plan['groups']]}
        # Exclusive creation rejects simultaneous initial launches.
        with state_path.open('x', encoding='utf-8') as handle:
            json.dump(state, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
    state.update(status='running', owner=identity(os.getpid()))
    atomic_json(state_path, state)
    try:
        for group, item in zip(plan['groups'], state['groups']):
            if item['status'] == 'completed':
                continue
            root = Path(group['root']).resolve()
            item.update(status='running', started_at=now())
            atomic_json(state_path, state)
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            for url in plan.get('health_urls', []):
                with opener.open(url, timeout=5) as response:
                    if response.status != 200:
                        raise ValueError('service health check failed')
            for phase, command in [('evaluate', group['command']), ('collect', group.get('collect'))]:
                if not command:
                    continue
                item['phase'] = phase
                with (root / (phase + '.client.log')).open('xb') as log:
                    kwargs = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
                    process = subprocess.Popen(command, cwd=root, stdin=subprocess.DEVNULL,
                                               stdout=log, stderr=subprocess.STDOUT, **kwargs)
                    item['process'] = identity(process.pid)
                    atomic_json(state_path, state)
                    code = process.wait()
                item[phase + '_exit_code'] = code
                atomic_json(state_path, state)
                if code != 0:
                    raise ValueError(f'group {group["id"]} {phase} failed: {code}')
            item.update(status='completed', finished_at=now(), result_sha256=validate_result(group))
            atomic_json(state_path, state)
        state.update(status='completed', finished_at=now())
        atomic_json(state_path, state)
        return state
    except BaseException as exc:
        # Never stop the serving stack or resend an interrupted client command.
        item['status'] = 'failed' if isinstance(exc, Exception) else 'unknown'
        state.update(status=item['status'], error=str(exc), stopped_at=now())
        atomic_json(state_path, state)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--state-file', required=True, type=Path)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    if args.validate_only:
        validate_plan(json.loads(args.plan.read_text()))
        print(json.dumps({'status': 'plan_valid', 'execution': 'not_started'}))
        return
    state = supervise(args.plan, args.state_file, args.resume)
    print(json.dumps({'status': state['status'], 'groups': len(state['groups']), 'state_file': str(args.state_file)}))


if __name__ == '__main__':
    main()
