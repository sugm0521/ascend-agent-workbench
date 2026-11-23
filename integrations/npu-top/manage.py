#!/usr/bin/env python3
"""Install the locked upstream wheels and the workbench's small UI customization.

Only Python's standard library is required here. Installation never contacts
servers: inventories are empty unless supplied explicitly. Local process control
uses an instance-scoped stop request, never kills an arbitrary port owner.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import socket
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import venv
import zipfile

COMPONENT = Path(__file__).resolve().parent
ROOT = COMPONENT.parents[1]
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024


class IntegrationError(RuntimeError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
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


def checked(path, expected):
    if not path.is_file() or digest(path.read_bytes()) != expected:
        raise IntegrationError('Artifact SHA256 mismatch: ' + path.name)
    return path


def contained(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise IntegrationError('Path escapes its declared directory')
    return path


def declarations(component=COMPONENT):
    manifest = read_json(component / 'manifest.json')
    if manifest.get('schema_version') != 1 or manifest.get('component') != 'npu-top':
        raise IntegrationError('Unsupported component manifest')
    lock_path = (component / manifest['upstream_lock']).resolve()
    if not lock_path.is_relative_to(component.parents[1] / 'upstream'):
        raise IntegrationError('The version lock must be owned by upstream/')
    lock = read_json(lock_path)
    if lock.get('schema_version') != 1 or lock.get('component') != 'npu-top':
        raise IntegrationError('Unsupported upstream lock')
    for key in ('patch', 'frontend', 'service'):
        item = manifest[key]
        checked(contained(component, item['path']), item['sha256'])
    names = set()
    for item in lock['wheels']:
        if (Path(item['filename']).name != item['filename'] or
                not item['filename'].endswith('.whl') or item['name'] in names):
            raise IntegrationError('Invalid or duplicate wheel declaration')
        if not item['url'].startswith('https://github.com/mindie-agent/'):
            raise IntegrationError('Unexpected upstream artifact origin')
        names.add(item['name'])
    if names != {'npu-top', 'remote-dev', 'mindie-diagnostics'}:
        raise IntegrationError('Incomplete dependency closure')
    return manifest, lock, lock_path


def archive_members(data):
    archive = zipfile.ZipFile(io.BytesIO(data))
    names = set()
    total = 0
    for info in archive.infolist():
        name = info.orig_filename
        path = PurePosixPath(name)
        if (not name or '\\' in name or ':' in name or path.is_absolute() or
                '..' in path.parts or name in names or stat.S_ISLNK(info.external_attr >> 16)):
            archive.close()
            raise IntegrationError('Unsafe archive member')
        total += info.file_size
        if total > MAX_ARCHIVE_BYTES:
            archive.close()
            raise IntegrationError('Archive exceeds the extraction limit')
        names.add(name)
    return archive


def deterministic_zip(files, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + '.tmp')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    os.replace(temporary, output)


def runtime_root(path):
    path = path.expanduser().resolve()
    if path == Path(path.anchor) or path == ROOT:
        raise IntegrationError('Use a dedicated runtime directory')
    marker = path / '.npu-top-managed.json'
    if path.exists() and any(path.iterdir()) and not marker.is_file():
        raise IntegrationError('Runtime directory is nonempty and is not owned by this integration')
    path.mkdir(parents=True, exist_ok=True)
    if marker.exists():
        if read_json(marker) != {'component': 'npu-top', 'schema_version': 1}:
            raise IntegrationError('Unrecognized runtime owner')
    else:
        write_json(marker, {'component': 'npu-top', 'schema_version': 1})
    return path


def obtain(item, cache, offline=False, bundle=None):
    target = cache / item['filename']
    if target.exists():
        return checked(target, item['sha256'])
    cache.mkdir(parents=True, exist_ok=True)
    if bundle is not None:
        name = 'wheels/' + item['filename']
        try:
            data = bundle.read(name)
        except KeyError as exc:
            raise IntegrationError('Offline bundle is missing ' + item['filename']) from exc
        if digest(data) != item['sha256']:
            raise IntegrationError('Offline wheel SHA256 mismatch: ' + item['filename'])
    elif offline:
        raise IntegrationError('Wheel unavailable offline: ' + item['filename'])
    else:
        with urllib.request.urlopen(item['url'], timeout=45) as response:
            data = response.read(MAX_ARCHIVE_BYTES + 1)
        if len(data) > MAX_ARCHIVE_BYTES or digest(data) != item['sha256']:
            raise IntegrationError('Downloaded wheel SHA256 mismatch: ' + item['filename'])
    temporary = target.with_name(target.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_bytes(data)
    os.replace(temporary, target)
    return target


def python_at(release):
    return release / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def run(command, log):
    environment = os.environ.copy()
    for key in ('PYTHONPATH', 'PYTHONHOME'):
        environment.pop(key, None)
    environment.update(PYTHONUTF8='1', PIP_NO_INDEX='1', PIP_DISABLE_PIP_VERSION_CHECK='1')
    with log.open('a', encoding='utf-8') as stream:
        result = subprocess.run(command, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise IntegrationError('Dependency operation failed; inspect ' + str(log))


def installed_packages(release):
    command = [str(python_at(release)), '-I', '-X', 'utf8', '-c',
               "import importlib.metadata as m,json; print(json.dumps({n:m.version(n) for n in ('npu-top','remote-dev','mindie-diagnostics')}))"]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=15)
    if result.returncode:
        raise IntegrationError('Installed package verification failed')
    return json.loads(result.stdout)


def validate_release(release):
    record = read_json(release / 'installed.json')
    for name, expected in record['static_hashes'].items():
        checked(contained(release, name), expected)
    checked(release / 'service.py', record['service_sha256'])
    if installed_packages(release) != record['packages']:
        raise IntegrationError('Installed versions differ from the receipt')
    return record


def configure(runtime, args):
    config_file = runtime / 'config.json'
    config = read_json(config_file) if config_file.exists() else {
        'state_dir': str(runtime / 'state'), 'port': 8788, 'inventory': []}
    if args.port is not None:
        config['port'] = args.port
    if not 1 <= config['port'] <= 65535:
        raise IntegrationError('Port must be between 1 and 65535')
    if args.state_dir is not None:
        config['state_dir'] = str(args.state_dir.expanduser().resolve())
    if args.inventory is not None:
        entries = []
        for path in args.inventory:
            path = path.expanduser().resolve()
            data = read_json(path)
            if not isinstance(data, dict) or not isinstance(data.get('machines'), list):
                raise IntegrationError('Inventory must contain a machines array')
            entries.append(str(path))
        config['inventory'] = entries
    if config_file.exists() and status(runtime)['running'] and config != read_json(config_file):
        raise IntegrationError('Stop the owned service before changing its configuration')
    write_json(config_file, config)
    return config


def install(args, runtime):
    manifest, lock, lock_path = declarations()
    if tuple(sys.version_info[:2]) < tuple(lock['python_min']):
        raise IntegrationError('Python version does not satisfy the lock')
    fingerprint = digest((json.dumps(manifest, sort_keys=True) + lock_path.read_text() +
                          str(sys.version_info[:2]) + platform.system() + platform.machine()).encode())
    current_file = runtime / 'current.json'
    if current_file.exists():
        current = read_json(current_file)
        release = contained(runtime, current['release'])
        if current['fingerprint'] == fingerprint:
            validate_release(release)
            configure(runtime, args)
            return {'installed': True, 'reused': True, 'release': current['release'], 'runtime': str(runtime)}
    instance = status(runtime)
    if instance['running']:
        raise IntegrationError('Stop the owned service before switching versions')
    bundle = archive_members(args.bundle.read_bytes()) if args.bundle else None
    try:
        if bundle is not None:
            metadata = json.loads(bundle.read('bundle.json'))
            if metadata.get('lock_sha256') != digest(lock_path.read_bytes()):
                raise IntegrationError('Offline bundle uses a different version lock')
            if (metadata.get('frontend_sha256') != manifest['frontend']['sha256'] or
                    digest(bundle.read('frontend.zip')) != manifest['frontend']['sha256']):
                raise IntegrationError('Offline bundle uses a different frontend')
        wheels = [obtain(item, runtime / 'cache', args.offline, bundle) for item in lock['wheels']]
    finally:
        if bundle is not None:
            bundle.close()
    release = runtime / 'releases' / (fingerprint[:12] + '-' + uuid.uuid4().hex[:8])
    release.mkdir(parents=True)
    # A venv must be created at its final path: moving it breaks Windows launchers.
    venv.EnvBuilder(with_pip=True).create(release / 'venv')
    log = release / 'install.log'
    run([str(python_at(release)), '-I', '-X', 'utf8', '-m', 'pip', 'install', '--no-index', '--no-deps',
         '--no-cache-dir', '--no-compile', *map(str, wheels)], log)
    run([str(python_at(release)), '-I', '-X', 'utf8', '-m', 'pip', 'check'], log)
    expected_packages = {item['name']: item['version'] for item in lock['wheels']}
    if installed_packages(release) != expected_packages:
        raise IntegrationError('Package versions do not match the lock')
    result = subprocess.run([str(python_at(release)), '-I', '-X', 'utf8', '-c',
                             'from npu_top.static_files import static_dir; print(static_dir())'],
                            capture_output=True, text=True, encoding='utf-8', check=True)
    static_root = Path(result.stdout.strip()).resolve()
    if not static_root.is_relative_to(release):
        raise IntegrationError('Installed frontend is outside the owned release')
    hashes = {}
    ui_path = contained(COMPONENT, manifest['frontend']['path'])
    with archive_members(ui_path.read_bytes()) as archive:
        if 'index.html' not in archive.namelist():
            raise IntegrationError('Frontend archive has no index.html')
        for info in archive.infolist():
            if info.is_dir():
                continue
            target = contained(static_root, info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            data = archive.read(info)
            target.write_bytes(data)
            hashes[str(target.relative_to(release))] = digest(data)
    shutil.copy2(contained(COMPONENT, manifest['service']['path']), release / 'service.py')
    record = {'fingerprint': fingerprint, 'packages': expected_packages,
              'customization': manifest['customization'], 'static_hashes': hashes,
              'service_sha256': manifest['service']['sha256']}
    write_json(release / 'installed.json', record)
    validate_release(release)
    configure(runtime, args)
    pointer = {'fingerprint': fingerprint, 'release': str(release.relative_to(runtime))}
    if current_file.exists():
        write_json(runtime / 'previous.json', read_json(current_file))
    write_json(current_file, pointer)
    return {'installed': True, 'reused': False, **pointer, 'runtime': str(runtime)}


def health(port):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open('http://127.0.0.1:' + str(port) + '/api/health', timeout=1) as response:
            return json.load(response)
    except (OSError, ValueError, urllib.error.URLError):
        return None


def port_free(port):
    with socket.socket() as connection:
        try:
            connection.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def status(runtime):
    path = runtime / 'instance.json'
    instance = read_json(path) if path.exists() else {}
    running = instance.get('state') == 'running' and time.time() - instance.get('heartbeat', 0) < 5
    config = read_json(runtime / 'config.json') if (runtime / 'config.json').exists() else {}
    observation = health(config['port']) if running and 'port' in config else None
    return {'running': running, 'pid': instance.get('pid'), 'instance': instance.get('instance'),
            'port': config.get('port'), 'health': observation}


def start(runtime):
    current = read_json(runtime / 'current.json')
    release = contained(runtime, current['release'])
    validate_release(release)
    current_status = status(runtime)
    if current_status['running']:
        if not current_status['health']:
            raise IntegrationError('Owned service is running but unhealthy; inspect its log')
        return {'reused': True, **current_status}
    config = read_json(runtime / 'config.json')
    if not port_free(config['port']):
        raise IntegrationError('Port is occupied; no existing process will be stopped')
    token = uuid.uuid4().hex
    logs = runtime / 'logs'
    logs.mkdir(exist_ok=True)
    options = {'creationflags': subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
    command = [str(python_at(release)), '-I', '-X', 'utf8', str(release / 'service.py'), '--runtime', str(runtime), '--instance', token]
    with (logs / (token + '.log')).open('wb') as stream:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stream,
                                   stderr=subprocess.STDOUT, close_fds=True, **options)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise IntegrationError('Service exited during startup; inspect its log')
        observed = status(runtime)
        if observed['instance'] == token and observed['health']:
            return {'reused': False, **observed}
        time.sleep(0.2)
    write_json(runtime / 'stop.json', {'instance': token})
    raise IntegrationError('Startup deadline exceeded; graceful stop requested')


def stop(runtime, timeout=60):
    observed = status(runtime)
    instance_path = runtime / 'instance.json'
    last = read_json(instance_path) if instance_path.exists() else {}
    if observed['running'] or (last.get('state') == 'running' and observed['instance']):
        # The instance token is safe even with a stale heartbeat. Never kill a PID.
        write_json(runtime / 'stop.json', {'instance': observed['instance']})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            instance = read_json(runtime / 'instance.json')
            if instance.get('instance') == observed['instance'] and instance.get('state') in ('stopped', 'failed'):
                return {'stopped': True, 'port_released': port_free(observed['port'])}
            time.sleep(0.2)
        raise IntegrationError('Shutdown not confirmed; inspect the owned instance')
    released = port_free(observed['port']) if observed['port'] else True
    if not released:
        raise IntegrationError('No live owned heartbeat and port is occupied; inspect before stopping anything')
    return {'stopped': True, 'port_released': True}


def bundle(args, runtime):
    manifest, lock, lock_path = declarations()
    files = {}
    for item in lock['wheels']:
        files['wheels/' + item['filename']] = obtain(item, runtime / 'cache', args.offline).read_bytes()
    files['frontend.zip'] = contained(COMPONENT, manifest['frontend']['path']).read_bytes()
    files['bundle.json'] = json.dumps({'schema_version': 1, 'lock_sha256': digest(lock_path.read_bytes()),
                                      'frontend_sha256': manifest['frontend']['sha256']}, sort_keys=True).encode()
    deterministic_zip(files, args.output.resolve())
    return {'bundle': str(args.output.resolve()), 'sha256': digest(args.output.read_bytes()), 'bytes': args.output.stat().st_size}


def rollback(runtime):
    if status(runtime)['running']:
        raise IntegrationError('Stop the owned service before rollback')
    previous = read_json(runtime / 'previous.json')
    release = contained(runtime, previous['release'])
    previous_record = validate_release(release)
    current = read_json(runtime / 'current.json')
    current_record = validate_release(contained(runtime, current['release']))
    if previous_record['packages'] != current_record['packages']:
        raise IntegrationError('Backend version rollback requires a separate state migration plan')
    write_json(runtime / 'current.json', previous)
    write_json(runtime / 'previous.json', current)
    return {'rolled_back': True, **previous}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root', type=Path, default=ROOT / '.workbench-local/npu-top-managed')
    commands = parser.add_subparsers(dest='command', required=True)
    install_parser = commands.add_parser('install')
    install_parser.add_argument('--bundle', type=Path)
    install_parser.add_argument('--offline', action='store_true')
    install_parser.add_argument('--port', type=int)
    install_parser.add_argument('--state-dir', type=Path)
    install_parser.add_argument('--inventory', type=Path, action='append')
    bundle_parser = commands.add_parser('bundle')
    bundle_parser.add_argument('--output', type=Path, required=True)
    bundle_parser.add_argument('--offline', action='store_true')
    for name in ('start', 'status', 'stop', 'rollback', 'check'):
        commands.add_parser(name)
    args = parser.parse_args(argv)
    try:
        runtime = runtime_root(args.runtime_root)
        if args.command == 'install': result = install(args, runtime)
        elif args.command == 'bundle': result = bundle(args, runtime)
        elif args.command == 'start': result = start(runtime)
        elif args.command == 'stop': result = stop(runtime)
        elif args.command == 'status': result = status(runtime)
        elif args.command == 'rollback': result = rollback(runtime)
        else:
            pointer = read_json(runtime / 'current.json')
            result = {'valid': True, **validate_release(contained(runtime, pointer['release']))}
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except (IntegrationError, OSError, ValueError, KeyError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
        print(json.dumps({'error': str(exc), 'type': type(exc).__name__}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
