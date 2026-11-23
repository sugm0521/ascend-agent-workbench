#!/usr/bin/env python3
"""Rebuild the frontend from the locked official source and the tracked patch."""
import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import urllib.request
import uuid

import manage


def rebuild(work_root, check=False):
    component = Path(__file__).resolve().parent
    manifest = manage.read_json(component / 'manifest.json')
    lock = manage.read_json(component / manifest['upstream_lock'])
    work_root.mkdir(parents=True, exist_ok=True)
    source_tar = work_root / 'source.tar.gz'
    if not source_tar.exists():
        with urllib.request.urlopen(lock['source']['url'], timeout=45) as response:
            data = response.read(manage.MAX_ARCHIVE_BYTES + 1)
        if manage.digest(data) != lock['source']['sha256']:
            raise manage.IntegrationError('Source archive SHA256 mismatch')
        source_tar.write_bytes(data)
    manage.checked(source_tar, lock['source']['sha256'])
    candidate = work_root / ('build-' + uuid.uuid4().hex[:8])
    candidate.mkdir()
    with tarfile.open(source_tar) as archive:
        total = 0
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            total += member.size
            if (name.is_absolute() or '..' in name.parts or '\\' in member.name or
                    ':' in member.name or not (member.isfile() or member.isdir()) or
                    total > manage.MAX_ARCHIVE_BYTES):
                raise manage.IntegrationError('Unsafe source archive member')
        archive.extractall(candidate, filter='data')
    roots = list(candidate.iterdir())
    if len(roots) != 1 or not (roots[0] / 'package-lock.json').is_file():
        raise manage.IntegrationError('Unexpected source archive layout')
    source = roots[0]
    git = shutil.which('git')
    npm = shutil.which('npm.cmd') or shutil.which('npm')
    if not git or not npm:
        raise manage.IntegrationError('Developer rebuild requires Git and Node/npm')
    log = candidate / 'build.log'

    def run(command):
        with log.open('a', encoding='utf-8') as stream:
            result = subprocess.run(command, cwd=source, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            raise manage.IntegrationError('Frontend build failed; inspect ' + str(log))

    patch = manage.contained(component, manifest['patch']['path'])
    run([git, '-C', str(source), 'init', '--quiet'])
    run([git, '-C', str(source), 'apply', '--check', str(patch)])
    run([git, '-C', str(source), 'apply', str(patch)])
    for args in (['ci', '--no-audit', '--no-fund'], ['test'], ['run', 'lint'],
                 ['exec', '--', 'tsc', '--noEmit'], ['run', 'build']):
        run([npm, *args])
    static = source / 'npu_top/static'
    files = {p.relative_to(static).as_posix(): p.read_bytes() for p in static.rglob('*') if p.is_file()}
    files['workbench-build.json'] = json.dumps({
        'component': 'npu-top', 'customization': manifest['customization'],
        'source_sha256': lock['source']['sha256'], 'patch_sha256': manage.digest(patch.read_bytes())
    }, sort_keys=True).encode()
    licenses = [('npu-top', source / 'LICENSE')]
    for name in ('react', 'react-dom', 'scheduler'):
        licenses.append((name, source / 'node_modules' / name / 'LICENSE'))
    files['THIRD-PARTY.txt'] = b'\n\n'.join(
        name.encode() + b'\n' + path.read_bytes() for name, path in licenses)
    output = candidate / 'frontend.zip'
    manage.deterministic_zip(files, output)
    hashes = {'patch': manage.digest(patch.read_bytes()), 'frontend': manage.digest(output.read_bytes()),
              'service': manage.digest((component / manifest['service']['path']).read_bytes())}
    if check:
        if any(manifest[key]['sha256'] != value for key, value in hashes.items()):
            raise manage.IntegrationError('Rebuilt artifacts differ from the tracked manifest')
    else:
        target = component / manifest['frontend']['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output, target)
        for key, value in hashes.items():
            manifest[key]['sha256'] = value
        manage.write_json(component / 'manifest.json', manifest)
    return {'verified': check, 'sha256': hashes, 'log': str(log), 'bytes': output.stat().st_size}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', type=Path, default=manage.ROOT / '.workbench-local/npu-top-build')
    parser.add_argument('--check', action='store_true')
    options = parser.parse_args()
    print(json.dumps(rebuild(options.work_root.resolve(), options.check)))
