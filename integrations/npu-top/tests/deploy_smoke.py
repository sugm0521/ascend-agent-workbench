"""Offline clean-install exercise with an empty inventory, no Git/Node or SSH."""
import argparse
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import urllib.request

COMPONENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(COMPONENT))
import manage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--runtime-root', type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime_root.resolve()
    if runtime.exists():
        raise RuntimeError('Smoke requires a nonexistent runtime directory')
    runtime.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update(PATH=os.path.join(os.environ['SystemRoot'], 'System32') if os.name == 'nt' else '/usr/bin:/bin',
                       PIP_NO_INDEX='1', PYTHONUTF8='1')
    for key in ('PYTHONHOME', 'PYTHONPATH'):
        environment.pop(key, None)

    def command(*arguments, success=True):
        result = subprocess.run([sys.executable, '-I', '-X', 'utf8', str(COMPONENT / 'manage.py'),
                                 '--runtime-root', str(runtime), *arguments],
                                env=environment, cwd=runtime.parent, capture_output=True,
                                text=True, encoding='utf-8', timeout=90)
        if success and result.returncode:
            raise RuntimeError(result.stderr)
        if not success:
            assert result.returncode, 'Expected command rejection'
            return result.stderr
        return json.loads(result.stdout)

    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    receipt = command('install', '--offline', '--bundle', str(args.bundle.resolve()), '--port', str(port))
    assert not receipt['reused']
    assert manage.read_json(runtime / 'config.json')['inventory'] == []
    repeated = command('install', '--offline')
    assert repeated['reused'] and repeated['release'] == receipt['release']
    command('check')
    started = False
    try:
        with socket.socket() as foreign:
            foreign.bind(('127.0.0.1', port))
            foreign.listen()
            assert 'Port is occupied' in command('start', success=False)
            assert foreign.getsockname()[1] == port
        first = command('start')
        started = True
        second = command('start')
        assert second['reused'] and first['pid'] == second['pid']
        assert 'Stop the owned service' in command('install', '--port', str(port % 65535 + 1), success=False)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/') as response:
            assert b'<html' in response.read()
        with opener.open(f'http://127.0.0.1:{port}/workbench-build.json') as response:
            assert json.load(response)['customization'] == manage.read_json(COMPONENT / 'manifest.json')['customization']
        with sqlite3.connect(runtime / 'state/monitor.sqlite3') as database:
            assert database.execute('SELECT COUNT(*) FROM servers').fetchone()[0] == 0
        checked = command('check')
        assert checked['valid']
    finally:
        if started:
            stopped = command('stop')
            assert stopped['stopped'] and stopped['port_released']
    # Corruption fails closed and does not silently reinstall over a current release.
    pointer = (runtime / 'current.json').read_bytes()
    asset_name = next(name for name in checked['static_hashes'] if name.endswith('index.html'))
    asset = runtime / receipt['release'] / asset_name
    original = asset.read_bytes()
    try:
        asset.write_bytes(b'corrupt')
        assert 'SHA256 mismatch' in command('install', '--offline', success=False)
        assert pointer == (runtime / 'current.json').read_bytes()
    finally:
        asset.write_bytes(original)
    command('check')
    print(json.dumps({'passed': True, 'path': str(COMPONENT.parents[1]), 'runtime': str(runtime),
                      'port': port, 'pid': first['pid'], 'offline': True, 'inventory_count': 0,
                      'checks': ['fresh-install', 'idempotent-install', 'port-conflict', 'start',
                                 'idempotent-start', 'running-config-rejection', 'http-assets',
                                 'empty-database', 'integrity', 'graceful-stop', 'corruption-rejection']}))


if __name__ == '__main__':
    main()
