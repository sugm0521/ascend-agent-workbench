"""Artifact and lifecycle boundaries; actual installation is deploy_smoke.py."""
import argparse
import importlib.util
import io
from pathlib import Path
import stat
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import manage

service_spec = importlib.util.spec_from_file_location('npu_top_control_service', manage.COMPONENT / 'service.py')
service = importlib.util.module_from_spec(service_spec)
service_spec.loader.exec_module(service)


class IntegrationTests(unittest.TestCase):
    def test_json_writers_retry_transient_windows_reader_locks(self):
        for writer in (manage.write_json, service.write_json):
            with self.subTest(writer=writer.__module__), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'instance.json'
                target.write_text('{"old": true}', encoding='utf-8')
                original_replace = manage.os.replace
                attempts = []

                def locked_twice(source, destination):
                    attempts.append(1)
                    if len(attempts) < 3:
                        raise PermissionError('synthetic Windows reader lock')
                    original_replace(source, destination)

                with patch.object(manage.os, 'replace', side_effect=locked_twice), patch.object(manage.time, 'sleep'):
                    writer(target, {'state': 'running'})
                self.assertEqual(len(attempts), 3)
                self.assertEqual(manage.read_json(target), {'state': 'running'})
                self.assertEqual(list(Path(directory).glob('*.tmp')), [])
                with patch.object(manage.os, 'replace', side_effect=PermissionError('persistent lock')), patch.object(manage.time, 'sleep'):
                    with self.assertRaises(PermissionError):
                        writer(target, {'state': 'uncommitted'})
                self.assertEqual(manage.read_json(target), {'state': 'running'})
                self.assertEqual(list(Path(directory).glob('*.tmp')), [])

    def test_failed_heartbeat_does_not_disable_scoped_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            manage.write_json(runtime / 'stop.json', {'instance': 'owned-token'})
            with patch.object(service, 'write_json', side_effect=PermissionError('reader lock')), \
                    patch.object(service.signal, 'getsignal') as signal_handler, patch('sys.stderr', io.StringIO()):
                callback = signal_handler.return_value
                service.supervise(runtime / 'instance.json', runtime / 'stop.json',
                                  {'instance': 'owned-token'}, threading.Event())
                callback.assert_called_once_with(service.signal.SIGTERM, None)

    def test_stale_heartbeat_still_requests_only_recorded_instance_token(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            manage.write_json(runtime / 'instance.json', {'state': 'running', 'instance': 'owned-token'})
            original_write = manage.write_json

            def stopped_after_request(path, value):
                self.assertEqual(path, runtime / 'stop.json')
                self.assertEqual(value, {'instance': 'owned-token'})
                original_write(path, value)
                original_write(runtime / 'instance.json', {'state': 'stopped', 'instance': 'owned-token'})

            with patch.object(manage, 'status', return_value={'running': False, 'instance': 'owned-token', 'port': 12345}), \
                    patch.object(manage, 'write_json', side_effect=stopped_after_request), patch.object(manage, 'port_free', return_value=True):
                self.assertTrue(manage.stop(runtime, timeout=1)['port_released'])

    def test_tracked_artifacts_and_dependency_closure(self):
        manifest, lock, _ = manage.declarations()
        self.assertEqual(len(lock['wheels']), 3)
        with manage.archive_members((manage.COMPONENT / manifest['frontend']['path']).read_bytes()) as archive:
            self.assertIn('index.html', archive.namelist())
            self.assertIn('THIRD-PARTY.txt', archive.namelist())
            self.assertIn('workbench-build.json', archive.namelist())

    def test_archive_cannot_escape_or_replace_an_alias(self):
        for name, mode in [('../escape', 0o100644), ('C:/escape', 0o100644),
                           ('a/escape', 0o100644), ('link', stat.S_IFLNK | 0o777)]:
            with self.subTest(name=name), io.BytesIO() as stream:
                with zipfile.ZipFile(stream, 'w') as archive:
                    info = zipfile.ZipInfo(name)
                    info.external_attr = mode << 16
                    archive.writestr(info, b'payload')
                data = stream.getvalue()
                if name == 'a/escape':
                    # ZipInfo normalizes slashes on Windows; exercise incoming raw bytes.
                    data = data.replace(b'a/escape', b'a\\escape')
                with self.assertRaises(manage.IntegrationError):
                    manage.archive_members(data)

    def test_offline_missing_and_corrupted_cache_never_use_network(self):
        with tempfile.TemporaryDirectory() as directory, patch('urllib.request.urlopen') as network:
            cache = Path(directory)
            item = {'filename': 'example.whl', 'sha256': manage.digest(b'valid')}
            with self.assertRaisesRegex(manage.IntegrationError, 'unavailable offline'):
                manage.obtain(item, cache, offline=True)
            (cache / item['filename']).write_bytes(b'corrupt')
            with self.assertRaisesRegex(manage.IntegrationError, 'SHA256 mismatch'):
                manage.obtain(item, cache)
            network.assert_not_called()

    def test_nonempty_unowned_runtime_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            evidence = path / 'unrelated.txt'
            evidence.write_bytes(b'keep')
            with self.assertRaisesRegex(manage.IntegrationError, 'nonempty'):
                manage.runtime_root(path)
            self.assertEqual(evidence.read_bytes(), b'keep')

    def test_running_configuration_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            original = {'port': 8788, 'state_dir': str(runtime / 'state'), 'inventory': []}
            manage.write_json(runtime / 'config.json', original)
            args = argparse.Namespace(port=8789, state_dir=None, inventory=None)
            with patch.object(manage, 'status', return_value={'running': True}):
                with self.assertRaisesRegex(manage.IntegrationError, 'Stop the owned service'):
                    manage.configure(runtime, args)
            self.assertEqual(manage.read_json(runtime / 'config.json'), original)

    def test_rollback_swaps_only_valid_same_backend_releases(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            old = {'release': 'releases/old', 'fingerprint': 'old'}
            new = {'release': 'releases/new', 'fingerprint': 'new'}
            manage.write_json(runtime / 'current.json', new)
            manage.write_json(runtime / 'previous.json', old)
            with patch.object(manage, 'status', return_value={'running': False}), \
                    patch.object(manage, 'validate_release', return_value={'packages': {'same': 'version'}}):
                manage.rollback(runtime)
            self.assertEqual(manage.read_json(runtime / 'current.json'), old)
            self.assertEqual(manage.read_json(runtime / 'previous.json'), new)
            with patch.object(manage, 'status', return_value={'running': False}), \
                    patch.object(manage, 'validate_release', side_effect=manage.IntegrationError('corrupt')):
                with self.assertRaises(manage.IntegrationError):
                    manage.rollback(runtime)
            self.assertEqual(manage.read_json(runtime / 'current.json'), old)


if __name__ == '__main__':
    unittest.main()
