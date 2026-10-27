"""Real Git/LFS publication tests; no network or media rendering is required."""
import datetime as dt
import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'ejecutar.py'
SPEC = importlib.util.spec_from_file_location('scheduled_jagoncito', SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)



def artwork(label,compression=6):
    """Deterministic textured PNG, encoded with only the standard library."""
    import struct,zlib
    label=label.encode() if isinstance(label,str) else label
    cells={(x,y):hashlib.sha256(label+f':{x}:{y}'.encode()).digest()[:3]
           for y in range(8) for x in range(12)}
    raw=b''.join(b'\0'+b''.join(cells[x//8,y//8] for x in range(96)) for y in range(64))
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',96,64,8,2,0,0,0))
            +chunk(b'IDAT',zlib.compress(raw,compression))+chunk(b'IEND',b''))

class FailingPushRunner(MODULE.Runner):
    def __init__(self, root):
        super().__init__(root)
        self.fail_success_push = False
        self.fail_pending_push = False
        self.fail_success_commit = False
        self.pushes = 0

    def git(self, *args, check=True):
        if 'commit' in args and self.fail_success_commit:
            state = self.root / 'automatizacion/estado.json'
            if state.exists() and json.loads(state.read_text()).get('status') == 'success':
                self.fail_success_commit = False
                response = subprocess.CompletedProcess(args, 1, '', 'Commit hook transient failure')
                if check:
                    raise MODULE.CommandError('Git commit', response)
                return response
        if args[0] == 'push':
            self.pushes += 1
            state = self.root / 'automatizacion/estado.json'
            status = json.loads(state.read_text()).get('status') if state.exists() else None
            should_fail = ((status == 'success' and self.fail_success_push) or
                           (status == 'running' and self.fail_pending_push))
            if should_fail:
                self.fail_success_push = False
                self.fail_pending_push = False
                response = subprocess.CompletedProcess(args, 1, '',
                    'Authorization: secret must never appear in status documents (HTTP 503)')
                if check:
                    raise MODULE.CommandError('Git push', response)
                return response
        return super().git(*args, check=check)


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'repo'
        self.root.mkdir()
        self.remote = self.base / 'remote.git'
        subprocess.run(['git', 'init', '--bare', str(self.remote)], check=True, capture_output=True)
        subprocess.run(['git', 'init', '-b', 'main', str(self.root)], check=True, capture_output=True)
        self.runner = FailingPushRunner(self.root)
        self.runner.git('config', 'user.name', 'Test')
        self.runner.git('config', 'user.email', 'test@example.invalid')
        self.runner.git('remote', 'add', 'origin', str(self.remote))
        self.runner.git('lfs', 'install', '--local')
        (self.root / '.gitattributes').write_text(
            'videos/**/*.mp4 filter=lfs diff=lfs merge=lfs -text\n'
            'videos/**/*.wav filter=lfs diff=lfs merge=lfs -text\n')
        (self.root / 'README.md').write_text('# Existing creator guidance\n\nKeep this paragraph.\n')
        self.date = MODULE.utc_slot('2026-10-27T16:00:00Z')
        self.plan = {'id': 'new-boathouse-23', 'creative_identity': {
            'scene_sha256': self.hash_bytes(artwork(b'new boathouse')), 'program': [2, 3], 'scene_id': 'boathouse'}}
        self.productions = 0
        # Preserve the historical duplicate scene in 001 and 002. Both it and
        # the Atelier are already used; their existence must block future reuse.
        for number, art, works, scene in [(1, b'rainy room', [1, 3], 'rainy'),
                                          (2, b'rainy room', [1, 2], 'rainy'),
                                          (3, b'atelier', [2, 1], 'atelier')]:
            art = artwork(art)
            date = self.date - dt.timedelta(hours=(4 - number) * 4)
            folder = self.root / f'videos/{number:03d}'
            plan = {'id': f'old-{number}', 'creative_identity': {
                'scene_sha256': self.hash_bytes(art), 'program': works, 'scene_id': scene}}
            self.write_bundle(date, folder, plan, art, f'historical-{number}')
            MODULE.json_write(self.root / f'automatizacion/entregas/old-{number}.json', {
                'number': number, 'status': 'success', 'slot': MODULE.iso(date),
                'tag': MODULE.tag_for(date), 'title': f'Existing film {number}',
                'folder': f'videos/{number:03d}', 'creative_identity': plan['creative_identity']})
        self.commit()
        self.publisher = MODULE.Publisher(self.root, 'jagoncito/Youtube', self.runner, self.planner)

    @staticmethod
    def hash_bytes(data):
        import hashlib
        return hashlib.sha256(data).hexdigest()

    def planner(self, date, root, *, exclude_tag=None):
        # Exercise the real catalogue history gate with a minimal local bank.
        production = SCRIPT.parent / 'produccion'
        import sys
        if str(production) not in sys.path:
            sys.path.insert(0, str(production))
        import crear_entrega
        scene = {'id': self.plan['creative_identity']['scene_id'], 'image': 'assets/new.png'}
        catalog = {'version': 3, 'plans': [{'id': self.plan['id'], 'works': [2, 3],
                    'title': 'A new scene and programme', 'intent': 'reading', 'scene': scene}]}
        try:
            return crear_entrega.select_new_plan(date, catalog, root=root, exclude_tag=exclude_tag)
        except crear_entrega.NeedsNewAssets as error:
            raise MODULE.NeedsNewAssets(str(error)) from error

    def prepare_asset(self, data=b'new boathouse'):
        path = self.root / 'assets/new.png'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(artwork(data))
        self.commit()

    def commit(self):
        self.runner.git('add', '.')
        self.runner.git('commit', '-m', 'Fixture update')
        self.runner.git('push', '-u', 'origin', 'main')

    def write_bundle(self, date, folder, plan, art, content):
        folder.mkdir(parents=True)
        for name in MODULE.REQUIRED - {'manifest.json', 'imagen.png'}:
            (folder / name).write_text(f'{content}: {name}')
        (folder / 'imagen.png').write_bytes(art)
        (folder / 'fuentes').mkdir()
        (folder / 'fuentes/license.txt').write_text('CC0 fixture source')
        manifest = dict(slot=MODULE.iso(date), title='Quiet Piano for Reading', plan_id=plan['id'],
            creative_identity=plan['creative_identity'], works=plan['creative_identity']['program'],
            audio={'clipped_samples': 0, 'chapters': [{'number': n} for n in plan['creative_identity']['program']]}, video_checks={
                'bucle-6min.mp4': {'duration_seconds': 360, 'complete_decode_exit_code': 0},
                'video-30min.mp4': {'duration_seconds': 1800, 'complete_decode_exit_code': 0}}, files={})
        for path in folder.rglob('*'):
            if path.is_file():
                manifest['files'][str(path.relative_to(folder))] = {
                    'bytes': path.stat().st_size, 'sha256': MODULE.file_hash(path)}
        MODULE.json_write(folder / 'manifest.json', manifest)

    def produce(self, date, folder, cache, plan):
        self.productions += 1
        self.write_bundle(date, folder, plan, artwork(b'new boathouse'), 'new original media')

    def execute(self, date=None, produce=None):
        return self.publisher.execute(date or self.date, self.base / 'cache', produce or self.produce)

    def test_direct_files_use_lfs_and_slot_is_idempotent(self):
        self.prepare_asset()
        entry = self.execute()
        self.assertEqual((entry['number'], entry['folder'], self.productions), (4, 'videos/004', 1))
        folder = self.root / entry['folder']
        self.assertTrue(MODULE.REQUIRED.issubset({path.name for path in folder.iterdir()}))
        self.assertTrue((folder / 'fuentes/license.txt').is_file())
        self.assertFalse(any((self.root / 'videos').glob('video-*')))
        self.assertTrue(MODULE.REQUIRED.issubset(entry['assets']))
        for name, meta in entry['assets'].items():
            self.assertEqual(meta['path'], name)
            self.assertNotIn('url', meta)
            self.assertEqual(MODULE.file_hash(folder / name), meta['sha256'])
        for name in ['video-30min.mp4', 'bucle-6min.mp4', 'audio-bucle-6min.wav']:
            pointer = self.runner.git('show', f'HEAD:videos/004/{name}').stdout
            self.assertTrue(pointer.startswith('version https://git-lfs.github.com/spec/v1\n'))
        self.assertIn('Keep this paragraph.', (self.root / 'README.md').read_text())
        before = self.runner.git('rev-parse', 'HEAD').stdout
        self.assertEqual(self.execute(), entry)
        self.assertEqual(self.productions, 1)
        self.assertEqual(self.runner.git('rev-parse', 'HEAD').stdout, before)
        self.assertEqual(self.runner.git('rev-parse', 'origin/main').stdout, before)
        # Check a fresh checkout actually receives the original bytes via LFS.
        fresh = self.base / 'fresh'
        subprocess.run(['git', 'clone', str(self.remote), str(fresh), '--branch', 'main'],
                       check=True, capture_output=True)
        replacement = MODULE.Publisher(fresh, 'jagoncito/Youtube', MODULE.Runner(fresh), self.planner)
        self.assertEqual(replacement.execute(self.date, self.base / 'cache', self.produce), entry)
        self.assertEqual(self.productions, 1)
        self.assertEqual((fresh / 'videos/004/video-30min.mp4').read_bytes(),
                         (folder / 'video-30min.mp4').read_bytes())

    def test_exhausted_bank_does_not_render_or_allocate_another_number(self):
        self.prepare_asset()
        self.execute()
        result = self.execute(self.date + dt.timedelta(hours=4))
        self.assertEqual(result['status'], 'needs_new_assets')
        self.assertNotIn('number', result)
        self.assertEqual(self.productions, 1)
        self.assertEqual(len(self.publisher.entries()), 4)
        self.assertFalse((self.root / 'videos/005').exists())

    def test_reused_image_from_any_existing_folder_is_blocked_before_production(self):
        self.prepare_asset(b'rainy room')
        result = self.execute()
        self.assertEqual(result['status'], 'needs_new_assets')
        self.assertEqual((self.productions, len(self.publisher.entries())), (0, 3))

    def test_reordered_programme_with_new_seed_is_blocked(self):
        self.prepare_asset()
        original = self.planner
        def reused(date, root, *, exclude_tag=None):
            import crear_entrega
            catalog = {'version': 99, 'plans': [{'id': 'new-seed-old-works', 'works': [3, 1],
                'title': 'Same programme', 'intent': 'reading',
                'scene': {'id': 'boathouse', 'image': 'assets/new.png'}}]}
            try:
                return crear_entrega.select_new_plan(date, catalog, root=root, exclude_tag=exclude_tag)
            except crear_entrega.NeedsNewAssets as error:
                raise MODULE.NeedsNewAssets(str(error)) from error
        # Load the producer module once through the normal planner first.
        original(self.date, self.root)
        self.publisher.planner = reused
        result = self.execute()
        self.assertEqual((result['status'], self.productions), ('needs_new_assets', 0))

    def test_successful_local_commit_recovers_after_partial_push_without_rerender(self):
        self.prepare_asset()
        self.runner.fail_success_push = True
        with self.assertRaises(MODULE.CommandError):
            self.execute()
        record = self.publisher.entry_for(MODULE.tag_for(self.date))
        self.assertEqual((record['status'], record['number'], self.productions), ('success', 4, 1))
        self.assertNotEqual(self.runner.git('rev-parse', 'HEAD').stdout,
                            self.runner.git('rev-parse', 'origin/main').stdout)
        recovered = self.execute()
        self.assertEqual((recovered['number'], self.productions), (4, 1))
        self.assertEqual(self.runner.git('rev-parse', 'HEAD').stdout,
                         self.runner.git('rev-parse', 'origin/main').stdout)

    def test_failed_commit_recovers_the_verified_staged_bundle(self):
        self.prepare_asset()
        self.runner.fail_success_commit = True
        with self.assertRaises(MODULE.CommandError):
            self.execute()
        self.assertTrue(self.runner.git('status', '--porcelain').stdout)
        recovered = self.execute()
        self.assertEqual((recovered['number'], self.productions), (4, 1))
        self.assertFalse(self.runner.git('status', '--porcelain').stdout)

    def test_staged_recovery_refuses_unrelated_dirty_work(self):
        self.prepare_asset()
        self.runner.fail_success_commit = True
        with self.assertRaises(MODULE.CommandError):
            self.execute()
        unrelated = self.root / 'user-notes.txt'
        unrelated.write_text('Preserve my work')
        with self.assertRaisesRegex(ValueError, 'dirty checkout'):
            self.execute()
        self.assertEqual(unrelated.read_text(), 'Preserve my work')
        self.assertEqual(self.productions, 1)

    def test_fresh_runner_recovers_remote_reservation_before_new_slot(self):
        self.prepare_asset()
        self.runner.fail_success_push = True
        with self.assertRaises(MODULE.CommandError):
            self.execute()
        fresh = self.base / 'replacement-runner'
        subprocess.run(['git', 'clone', '--branch', 'main', str(self.remote), str(fresh)],
                       check=True, capture_output=True)
        runner = MODULE.Runner(fresh)
        runner.git('lfs', 'install', '--local')
        runner.git('lfs', 'pull')
        replacement = MODULE.Publisher(fresh, 'jagoncito/Youtube', runner, self.planner)
        self.assertFalse((fresh / 'videos/004').exists())
        next_slot = self.date + dt.timedelta(hours=4)
        recovered = MODULE.recover_prior_completed_delivery(replacement, next_slot,
            self.base / 'cache', self.produce)
        self.assertEqual((recovered['number'], self.productions), (4, 2))
        self.assertTrue((fresh / 'videos/004/video-30min.mp4').is_file())
        blocked = replacement.execute(next_slot, self.base / 'cache', self.produce)
        self.assertEqual(blocked['status'], 'needs_new_assets')
        self.assertFalse((fresh / 'videos/005').exists())

    def test_pending_push_failure_retry_reuses_reserved_number(self):
        self.prepare_asset()
        self.runner.fail_pending_push = True
        with self.assertRaises(MODULE.CommandError):
            self.execute()
        record = self.publisher.entry_for(MODULE.tag_for(self.date))
        self.assertEqual((record['status'], record['number'], self.productions), ('failure', 4, 0))
        self.assertNotIn('secret', (self.root / 'automatizacion/estado.json').read_text())
        recovered = self.execute()
        self.assertEqual((recovered['number'], self.productions), (4, 1))

    def test_missing_lfs_tracking_stops_before_rendering(self):
        self.prepare_asset()
        (self.root / '.gitattributes').write_text('*.wav filter=lfs diff=lfs merge=lfs -text\n')
        self.commit()
        with self.assertRaisesRegex(ValueError, 'Git LFS tracking'):
            self.execute()
        self.assertEqual(self.productions, 0)
        self.assertFalse((self.root / 'videos/004').exists())

    def test_tampered_media_is_not_committed_as_a_delivery(self):
        self.prepare_asset()
        def tampered(date, folder, cache, plan):
            self.produce(date, folder, cache, plan)
            (folder / 'audio-bucle-6min.wav').write_text('tampered audio')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.execute(produce=tampered)
        self.assertFalse((self.root / 'videos/004').exists())
        self.assertEqual(self.publisher.entry_for(MODULE.tag_for(self.date))['status'], 'failure')

    def test_exact_old_video_is_rejected_even_with_unused_scene_and_programme(self):
        self.prepare_asset()
        def copied(date, folder, cache, plan):
            self.produce(date, folder, cache, plan)
            shutil = __import__('shutil')
            target = folder / 'video-30min.mp4'
            shutil.copyfile(self.root / 'videos/001/video-30min.mp4', target)
            manifest = json.loads((folder / 'manifest.json').read_text())
            manifest['files']['video-30min.mp4'] = {
                'bytes': target.stat().st_size, 'sha256': MODULE.file_hash(target)}
            MODULE.json_write(folder / 'manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'already appeared'):
            self.execute(produce=copied)
        self.assertFalse((self.root / 'videos/004').exists())

    def test_claimed_new_programme_cannot_hide_old_audio_chapters(self):
        self.prepare_asset()
        def mislabeled(date, folder, cache, plan):
            self.produce(date, folder, cache, plan)
            manifest = json.loads((folder / 'manifest.json').read_text())
            manifest['audio']['chapters'] = [{'number': 3}, {'number': 1}]
            MODULE.json_write(folder / 'manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'music does not match'):
            self.execute(produce=mislabeled)
        self.assertFalse((self.root / 'videos/004').exists())

    def test_head_only_fetch_config_still_refreshes_main(self):
        peer = self.base / 'peer'
        subprocess.run(['git', 'clone', '--branch', 'main', str(self.remote), str(peer)],
                       check=True, capture_output=True)
        runner = MODULE.Runner(peer)
        runner.git('config', 'user.name', 'Peer')
        runner.git('config', 'user.email', 'peer@example.invalid')
        (peer / 'upstream.txt').write_text('A newer remote commit')
        runner.git('add', 'upstream.txt')
        runner.git('commit', '-m', 'Upstream change')
        runner.git('push', 'origin', 'main')
        self.runner.git('config', 'remote.origin.fetch', '+HEAD:refs/remotes/origin/HEAD')
        self.publisher.sync()
        self.assertEqual((self.root / 'upstream.txt').read_text(), 'A newer remote commit')

    def test_prior_failed_push_can_recover_before_next_slot(self):
        self.prepare_asset()
        self.runner.fail_success_push = True
        with self.assertRaises(MODULE.CommandError):
            self.execute()
        recovered = MODULE.recover_prior_completed_delivery(self.publisher,
            self.date + dt.timedelta(hours=4), self.base / 'cache', self.produce)
        self.assertEqual((recovered['number'], self.productions), (4, 1))


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
