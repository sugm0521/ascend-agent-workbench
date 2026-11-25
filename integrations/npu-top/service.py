"""Run the original collector with local configuration and a graceful stop file."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import threading
import time
import uuid


UPSTREAM_LIBRARY_LINE = 'export LD_LIBRARY_PATH=/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/driver/lib64:${LD_LIBRARY_PATH:-}'
WORKBENCH_LIBRARY_LINE = 'export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+${LD_LIBRARY_PATH}:}/usr/lib64:/lib64:/usr/lib:/lib:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/driver/lib64"'
UPSTREAM_RESULT_LINE = '''printf '__NFM_SECTION__npu_info_rc\\n%s\\n' "$nfm_rc"'''
WORKBENCH_RESULT_LINE = '''if [ "$nfm_rc" -eq 124 ]; then
    printf 'npu-smi info 超时（退出码 124）\\n'
elif [ "$nfm_rc" -ne 0 ]; then
    printf 'npu-smi info 失败（退出码 %s）\\n' "$nfm_rc"
fi
''' + UPSTREAM_RESULT_LINE


def customize_fast_script(script):
    """Adapt the locked probe without changing the upstream installation.

    Preserve an explicit host environment, then system library precedence,
    with Ascend directories as fallback. Refuse an unexpected upstream layout.
    """
    if script.count(WORKBENCH_LIBRARY_LINE) == 1 and script.count(WORKBENCH_RESULT_LINE) == 1:
        return script
    if script.count(UPSTREAM_LIBRARY_LINE) != 1 or script.count(UPSTREAM_RESULT_LINE) != 1:
        raise RuntimeError('The locked npu-top probe layout changed; review the collector customization')
    return script.replace(UPSTREAM_LIBRARY_LINE, WORKBENCH_LIBRARY_LINE).replace(
        UPSTREAM_RESULT_LINE, WORKBENCH_RESULT_LINE)


def configure_collector():
    from npu_top import probe
    probe.FAST_SCRIPT = customize_fast_script(probe.FAST_SCRIPT)


def write_json(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    try:
        for attempt in range(20):
            try:
                os.replace(temporary, path)
                return
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(0.025)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def supervise(instance_path, stop_path, record, finished):
    while not finished.is_set():
        try:
            write_json(instance_path, {**record, 'heartbeat': time.time()})
        except OSError as exc:
            # A transient Windows reader/AV lock must not disable stop handling.
            print('npu-top: heartbeat write deferred (' + type(exc).__name__ + ')', file=sys.stderr, flush=True)
        if stop_path.is_file():
            try:
                request = json.loads(stop_path.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                request = {}
            handler = signal.getsignal(signal.SIGTERM)
            if request.get('instance') == record['instance'] and callable(handler):
                handler(signal.SIGTERM, None)
                return
        finished.wait(0.5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--instance', required=True)
    args = parser.parse_args()
    config = json.loads((args.runtime / 'config.json').read_text(encoding='utf-8'))
    environment = {
        'MINDIE_TOP_STATE_DIR': config['state_dir'],
        'MINDIE_TOP_BIND': '127.0.0.1',
        'MINDIE_TOP_PORT': str(config['port']),
        'MINDIE_TOP_INVENTORY_FILES': os.pathsep.join(config['inventory']),
        'MINDIE_TOP_HOST_POOL_FILES': '',
        'MINDIE_TOP_RETENTION_DAYS': '90',
        'MINDIE_TOP_SQLITE_MAX_MB': '1024',
        'MINDIE_TOP_MAX_WORKERS': '4',
        'REMOTE_DEV_SSH_MUX': '0',
    }
    os.environ.update(environment)
    # Inventory discovery must not inherit another client's coordinator binding.
    os.environ.pop('MINDIE_COORDINATOR_STATE_DIR', None)
    configure_collector()
    instance_path = args.runtime / 'instance.json'
    stop_path = args.runtime / 'stop.json'
    finished = threading.Event()
    record = {'instance': args.instance, 'pid': os.getpid(),
              'state': 'running', 'started_at': time.time()}

    watcher = threading.Thread(target=supervise, args=(instance_path, stop_path, record, finished),
                               name='npu-top-local-control', daemon=True)
    watcher.start()
    try:
        from npu_top.serve import main as serve
        serve()
    except BaseException:
        record['state'] = 'failed'
        raise
    finally:
        finished.set()
        watcher.join(timeout=2)
        record['state'] = 'stopped' if record['state'] != 'failed' else 'failed'
        write_json(instance_path, {**record, 'heartbeat': time.time()})


if __name__ == '__main__':
    main()
