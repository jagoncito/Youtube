import datetime as dt
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'ejecutar.py'
SPEC = importlib.util.spec_from_file_location('scheduled_jagoncito', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def result(code=0, stdout='', stderr=''):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class FakeGitHub(MODULE.Runner):
    """Git remains real against a temporary bare repository; only GitHub is mocked."""
    def __init__(self, root):
        super().__init__(root)
        self.releases = {}
        self.calls = []
        self.fail_upload = False
        self.fail_auth = False

    def gh(self, *args, check=True):
        self.calls.append(args)
        if self.fail_auth:
            response = result(1, stderr='gh: Resource not accessible (HTTP 403)')
        elif args[0] == 'api':
            endpoint = args[1]
            if '/releases/tags/' in endpoint:
                release = self.releases.get(endpoint.rsplit('/', 1)[1])
                response = result(stdout=json.dumps(release)) if release else result(1, stderr='gh: Not Found (HTTP 404)')
            else:
                response = result(stdout='jagoncito/Youtube\n')
        elif args[:2] == ('release', 'create'):
            tag = args[2]
            self.releases[tag] = dict(draft=True, name=args[args.index('--title') + 1],
                                      html_url=f'https://github.com/jagoncito/Youtube/releases/tag/{tag}', assets=[])
            response = result()
        elif args[:2] == ('release', 'edit'):
            release = self.releases[args[2]]
            if '--draft=false' in args:
                release['draft'] = False
            if '--title' in args:
                release['name'] = args[args.index('--title') + 1]
            response = result()
        elif args[:2] == ('release', 'upload'):
            if self.fail_upload:
                response = result(1, stderr='Transient storage failure (HTTP 500)')
            else:
                paths = [Path(p) for p in args[3:args.index('--repo')]]
                self.releases[args[2]]['assets'] = [dict(name=p.name, size=p.stat().st_size,
                    browser_download_url=f'https://github.com/example/{p.name}') for p in paths]
                response = result()
        elif args[:2] == ('release', 'download'):
            directory = Path(args[args.index('--dir') + 1])
            (directory / 'publicacion.txt').write_text('Publication recovered from the release')
            (directory / 'manifest.json').write_text('{}')
            response = result()
        else:
            raise AssertionError(f'Unexpected GitHub call: {args}')
        if check and response.returncode:
            raise MODULE.CommandError('mock GitHub', response)
        return response


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = base / 'repo'
        self.root.mkdir()
        self.remote = base / 'remote.git'
        subprocess.run(['git', 'init', '--bare', str(self.remote)], check=True, capture_output=True)
        subprocess.run(['git', 'init', '-b', 'main', str(self.root)], check=True, capture_output=True)
        self.runner = FakeGitHub(self.root)
        self.runner.git('config', 'user.name', 'Test')
        self.runner.git('config', 'user.email', 'test@example.invalid')
        self.runner.git('remote', 'add', 'origin', str(self.remote))
        (self.root / 'README.md').write_text('# Existing creator guidance\n\nDo not overwrite this.\n')
        initial = self.root / 'automatizacion' / 'entregas' / '0001-existente.json'
        MODULE.json_write(initial, dict(number=1, status='success', title='Existing film',
            slot='2026-10-15T12:00:00Z', url='https://github.com/existing',
            card_path='videos/video-0001/README.md'))
        self.commit()
        self.publisher = MODULE.Publisher(self.root, 'jagoncito/Youtube', self.runner)
        self.date = MODULE.utc_slot('2026-10-27T12:00:00Z')
        self.productions = 0

    def commit(self):
        self.runner.git('add', '.')
        self.runner.git('commit', '-m', 'Fixture update')
        self.runner.git('push', '-u', 'origin', 'main')

    def produce(self, date, folder, cache):
        self.productions += 1
        folder.mkdir()
        for name in MODULE.REQUIRED - {'manifest.json'}:
            (folder / name).write_text(f'Fixture asset {name}')
        (folder / 'fuentes').mkdir()
        (folder / 'fuentes' / 'license.txt').write_text('CC0 fixture source')
        manifest = dict(slot=MODULE.iso(date), title='Quiet Piano for Reading', plan_id='reading-2-1',
            audio={'clipped_samples': 0}, video_checks={
                'bucle-6min.mp4': {'duration_seconds': 360, 'complete_decode_exit_code': 0},
                'video-30min.mp4': {'duration_seconds': 1800, 'complete_decode_exit_code': 0}}, files={})
        for path in folder.rglob('*'):
            if path.is_file():
                manifest['files'][str(path.relative_to(folder))] = {
                    'bytes': path.stat().st_size, 'sha256': MODULE.file_hash(path)}
        MODULE.json_write(folder / 'manifest.json', manifest)

    def test_publish_is_complete_numbered_and_idempotent(self):
        entry = self.publisher.execute(self.date, Path('/tmp/cache'), self.produce)
        self.assertEqual(entry['number'], 2)
        self.assertEqual(self.productions, 1)
        self.assertFalse(self.runner.releases[entry['tag']]['draft'])
        self.assertTrue(MODULE.REQUIRED.issubset(entry['assets']))
        self.assertEqual(json.loads((self.root / 'automatizacion/estado.json').read_text())['status'], 'success')
        card = self.root / 'videos/video-0002'
        self.assertTrue((card / 'manifest.json').is_file())
        self.assertTrue((card / 'publicacion.txt').is_file())
        self.assertIn('Vídeo 002', (card / 'README.md').read_text())
        self.assertIn('Do not overwrite this.', (self.root / 'README.md').read_text())
        before = self.runner.git('rev-parse', 'HEAD').stdout
        self.publisher.execute(self.date, Path('/tmp/cache'), self.produce)
        self.assertEqual(self.runner.git('rev-parse', 'HEAD').stdout, before)
        self.assertEqual(self.productions, 1)
        self.assertEqual(self.runner.git('rev-parse', 'origin/main').stdout, before)

    def test_upload_failure_keeps_draft_and_reservation_retry_reuses_number(self):
        self.runner.fail_upload = True
        with self.assertRaises(MODULE.CommandError):
            self.publisher.execute(self.date, Path('/tmp/cache'), self.produce)
        tag = MODULE.tag_for(self.date)
        self.assertTrue(self.runner.releases[tag]['draft'])
        record = json.loads((self.root / 'automatizacion/entregas' / f'{tag}.json').read_text())
        self.assertEqual((record['status'], record['number']), ('failure', 2))
        self.assertFalse((self.root / 'videos/video-0002').exists())
        self.runner.fail_upload = False
        recovered = self.publisher.execute(self.date, Path('/tmp/cache'), self.produce)
        self.assertEqual(recovered['number'], 2)
        creates = [call for call in self.runner.calls if call[:2] == ('release', 'create')]
        self.assertEqual(len(creates), 1)

    def test_next_slot_allocates_next_number_without_reusing_old_id(self):
        one = self.publisher.execute(self.date, Path('/tmp/cache'), self.produce)
        two = self.publisher.execute(self.date + dt.timedelta(hours=4), Path('/tmp/cache'), self.produce)
        self.assertEqual((one['number'], two['number']), (2, 3))
        self.assertTrue((self.root / 'videos/video-0002/README.md').exists())
        self.assertTrue((self.root / 'videos/video-0003/README.md').exists())

    def test_auth_failure_is_not_treated_as_absent_release(self):
        self.runner.fail_auth = True
        with self.assertRaises(MODULE.CommandError):
            self.publisher.execute(self.date, Path('/tmp/cache'), self.produce)
        self.assertEqual(self.productions, 0)
        self.assertFalse(any(call[:2] == ('release', 'create') for call in self.runner.calls))

    def test_failed_checksum_does_not_create_a_release(self):
        def tampered(date, folder, cache):
            self.produce(date, folder, cache)
            (folder / 'audio-bucle-6min.wav').write_text('tampered audio')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.publisher.execute(self.date, Path('/tmp/cache'), tampered)
        self.assertFalse(self.runner.releases)
        status = json.loads((self.root / 'automatizacion/estado.json').read_text())
        self.assertEqual(status['status'], 'failure')

    def test_published_but_unindexed_release_recovers_without_new_production(self):
        first = self.publisher.execute(self.date, Path('/tmp/cache'), self.produce)
        record = self.root / 'automatizacion/entregas' / f'{first["tag"]}.json'
        item = json.loads(record.read_text())
        item['status'] = 'failure'
        MODULE.json_write(record, item)
        self.commit()
        recovered = self.publisher.execute(self.date, Path('/tmp/cache'), self.produce)
        self.assertEqual(recovered['number'], 2)
        self.assertEqual(self.productions, 1)
        self.assertEqual((self.root / 'videos/video-0002/publicacion.txt').read_text(),
                         'Publication recovered from the release')


class SlotTests(unittest.TestCase):
    def test_floor_uses_utc_and_four_hour_boundary(self):
        now = dt.datetime(2026, 10, 27, 15, 49, tzinfo=dt.timezone(dt.timedelta(hours=1)))
        self.assertEqual(MODULE.iso(MODULE.utc_slot(now=now)), '2026-10-27T12:00:00Z')
        self.assertEqual(MODULE.tag_for(MODULE.utc_slot('2026-10-27T04:00:00Z')), 'jagoncito-20261027-0400Z')

    def test_rejects_naive_or_partial_slots(self):
        for slot in ['2026-10-27T12:00:00', '2026-10-27T13:00:00Z', '2026-10-27T12:01:00Z']:
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                MODULE.utc_slot(slot)


if __name__ == '__main__':
    unittest.main()
