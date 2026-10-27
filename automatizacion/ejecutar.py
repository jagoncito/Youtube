#!/usr/bin/env python3
"""Evaluate a four-hour slot and commit an original bundle under videos/NNN."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

BOT_EMAIL = '41898282+github-actions[bot]@users.noreply.github.com'
REQUIRED = {'video-30min.mp4', 'bucle-6min.mp4', 'audio-bucle-6min.wav',
            'imagen.png', 'miniatura.jpg', 'publicacion.txt', 'README.md', 'manifest.json'}


class NeedsNewAssets(ValueError):
    """No unused scene and music programme remain in the finite catalogue."""


class CommandError(RuntimeError):
    def __init__(self, operation, result):
        self.operation = operation
        self.result = result
        status = re.search(r'\bHTTP (\d{3})\b', result.stderr or '')
        detail = f'; HTTP {status.group(1)}' if status else ''
        super().__init__(f'{operation} failed (exit {result.returncode}{detail})')


class Runner:
    def __init__(self, root):
        self.root = Path(root)

    def call(self, args, *, check=True):
        result = subprocess.run([str(x) for x in args], cwd=self.root, text=True,
                                capture_output=True)
        if check and result.returncode:
            # External stderr can include request headers or credentials.
            raise CommandError(str(args[0]), result)
        return result

    def git(self, *args, check=True):
        return self.call(['git', *args], check=check)


def utc_slot(value=None, now=None):
    if value:
        date = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if date.tzinfo is None:
            raise ValueError('Slot timezone is required')
        date = date.astimezone(dt.timezone.utc)
        if date.minute or date.second or date.microsecond or date.hour % 4:
            raise ValueError('Slot must be 00/04/08/12/16/20:00 UTC')
    else:
        date = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
        date = date.replace(hour=(date.hour // 4) * 4, minute=0, second=0, microsecond=0)
    return date


def tag_for(date):
    return date.strftime('jagoncito-%Y%m%d-%H00Z')


def iso(date):
    return date.isoformat().replace('+00:00', 'Z')


def json_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def file_hash(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_manifest(manifest, slot):
    if not isinstance(manifest, dict) or manifest.get('slot') != slot:
        raise ValueError('Bundle slot mismatch')
    if not (REQUIRED - {'manifest.json'}).issubset(manifest.get('files', {})):
        raise ValueError('Required assets are missing from the checksum manifest')
    for name, duration in [('bucle-6min.mp4', 360), ('video-30min.mp4', 1800)]:
        result = manifest['video_checks'][name]
        if result['complete_decode_exit_code'] != 0 or result['duration_seconds'] != duration:
            raise ValueError('Production validation did not pass')
    if manifest['audio']['clipped_samples'] != 0:
        raise ValueError('Audio validation did not pass')


def verify_bundle(folder, slot):
    folder = Path(folder)
    if not folder.is_dir() or not REQUIRED.issubset({p.name for p in folder.iterdir() if p.is_file()}):
        raise ValueError('Incomplete production bundle')
    manifest = json.loads((folder / 'manifest.json').read_text())
    verify_manifest(manifest, slot)
    expected = set(manifest['files']) | {'manifest.json'}
    actual = {str(path.relative_to(folder)) for path in folder.rglob('*') if path.is_file()}
    if actual != expected or not any(name.startswith('fuentes/') for name in expected):
        raise ValueError('Bundle must include exactly its checksummed media and sources')
    for name, meta in manifest['files'].items():
        path = folder / name
        resolved = path.resolve()
        if path.is_symlink() or not resolved.is_relative_to(folder.resolve()) or not path.is_file():
            raise ValueError('Unsafe or missing manifest file')
        if path.stat().st_size != meta['bytes'] or file_hash(path) != meta['sha256']:
            raise ValueError('Bundle checksum mismatch')
    return manifest


def plan_delivery(date, root, *, exclude_tag=None):
    """Load the same strict planner used by the renderer, without rendering."""
    production = Path(__file__).resolve().parent / 'produccion'
    if str(production) not in sys.path:
        sys.path.insert(0, str(production))
    import crear_entrega
    catalog = json.loads((Path(root) / 'automatizacion/produccion/catalogo.json').read_text())
    try:
        return crear_entrega.select_new_plan(date, catalog, root=Path(root), exclude_tag=exclude_tag)
    except crear_entrega.NeedsNewAssets as error:
        raise NeedsNewAssets(str(error)) from error


def creative_identity(value):
    """A seed or a different order of the same works is never a new programme."""
    identity = value.get('creative_identity', {})
    image_hash = identity.get('scene_sha256')
    works = identity.get('program')
    if not isinstance(image_hash, str) or not re.fullmatch('[0-9a-f]{64}', image_hash):
        raise ValueError('Missing creative scene fingerprint')
    if not isinstance(works, list) or not works or any(type(n) is not int for n in works):
        raise ValueError('Missing creative programme fingerprint')
    return dict(scene_sha256=image_hash, program=sorted(set(works)),
                scene_id=identity.get('scene_id'))


class Publisher:
    def __init__(self, root, repository, runner=None, planner=None):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('Invalid repository identity')
        self.root = Path(root)
        self.repository = repository
        self.runner = runner or Runner(root)
        self.planner = planner or plan_delivery
        self.directory = self.root / 'automatizacion'

    def sync(self):
        if self.runner.git('status', '--porcelain').stdout.strip():
            raise ValueError('Refusing to update status over a dirty checkout')
        self.runner.git('fetch', 'origin', 'refs/heads/main:refs/remotes/origin/main')
        # A locally committed delivery can be ahead after a failed push. Keep it
        # available for the retry; never reset it to the older remote state.
        self.runner.git('merge', '--ff-only', 'origin/main')

    def recover_staged_delivery(self, date):
        """Finish our already-staged bundle after a failed commit, without rendering.

        Refuse recovery if anything is unstaged, untracked or outside the exact
        delivery/status paths. An arbitrary dirty checkout remains an error.
        """
        if not self.runner.git('status', '--porcelain').stdout.strip():
            return False
        tag = tag_for(date)
        entry = self.entry_for(tag)
        if not entry or entry.get('status') != 'success':
            return False
        folder = f'videos/{entry["number"]:03d}'
        record = f'automatizacion/entregas/{tag}.json'
        if entry.get('folder') != folder or entry.get('slot') != iso(date):
            return False
        if self.runner.git('diff', '--name-only').stdout or self.runner.git(
                'ls-files', '--others', '--exclude-standard').stdout:
            return False
        staged = set(filter(None, self.runner.git('diff', '--cached', '--name-only', '-z').stdout.split('\0')))
        required = {record, f'{folder}/manifest.json'}
        allowed = {record, 'automatizacion/estado.json', 'automatizacion/ENTREGAS.md', 'README.md'}
        if not required.issubset(staged) or any(path not in allowed and not path.startswith(folder + '/')
                                              for path in staged):
            return False
        state = json.loads((self.directory / 'estado.json').read_text())
        if state.get('tag') != tag or state.get('status') != 'success':
            return False
        verify_bundle(self.root / folder, iso(date))
        self.ensure_lfs(entry['number'])
        self.runner.git('-c', 'user.name=github-actions[bot]', '-c', f'user.email={BOT_EMAIL}',
                        'commit', '-m', f'Production recovery: {tag}')
        return True

    def entries(self):
        return [json.loads(path.read_text()) for path in
                (self.directory / 'entregas').glob('*.json')]

    def entry_for(self, tag):
        path = self.directory / 'entregas' / f'{tag}.json'
        return json.loads(path.read_text()) if path.exists() else None

    def reserve(self, date):
        current = self.entry_for(tag_for(date))
        if current is not None:
            return current
        numbers = [int(item['number']) for item in self.entries()
                   if isinstance(item.get('number'), int)]
        numbers += [int(path.name) for path in (self.root / 'videos').glob('[0-9][0-9][0-9]')
                    if path.is_dir()]
        return dict(number=max([0] + numbers) + 1, status='pending', slot=iso(date),
                    tag=tag_for(date), title='Producción pendiente', published_to_youtube=False)

    def ensure_lfs(self, number):
        self.runner.git('lfs', 'version')
        paths = [f'videos/{number:03d}/{name}' for name in
                 ['video-30min.mp4', 'bucle-6min.mp4', 'audio-bucle-6min.wav']]
        attributes = self.runner.git('check-attr', 'filter', '--', *paths).stdout.splitlines()
        if len(attributes) != len(paths) or any(not line.endswith(': filter: lfs') for line in attributes):
            raise ValueError('Git LFS tracking is required for all delivery MP4 and WAV files')
        self.runner.git('lfs', 'install', '--local')

    def push(self):
        # The local LFS pre-push hook sends the media before the Git reference.
        self.runner.git('push', 'origin', 'HEAD:main')

    def update_index(self):
        records = sorted((item for item in self.entries() if item.get('status') == 'success'),
                         key=lambda item: item['number'])
        table = '# Entregas automáticas\n\nLos archivos de cada vídeo están dentro de su carpeta.\n\n'
        table += '| Número | Vídeo | Archivos |\n| --- | --- | --- |\n'
        links = []
        for item in records:
            title = item['title'].replace('|', '\\|').replace('\n', ' ')
            folder = item.get('folder', f'videos/{item["number"]:03d}')
            table += f'| {item["number"]:03d} | {title} | [Abrir carpeta](../{folder}/) |\n'
            links.append(f'- [Vídeo {item["number"]:03d} — {title}]({folder}/)')
        (self.directory / 'ENTREGAS.md').write_text(table)
        readme = self.root / 'README.md'
        current = readme.read_text() if readme.exists() else '# Jagoncito\n'
        start, end = '<!-- JAGONCITO:ENTREGAS:START -->', '<!-- JAGONCITO:ENTREGAS:END -->'
        managed = start + '\n\n' + '\n'.join(links) + '\n\n' + end
        if start in current and end in current:
            current = current[:current.index(start)] + managed + current[current.index(end) + len(end):]
        else:
            current += '\n\n## Vídeos por orden\n\n' + managed + '\n'
        readme.write_text(current)

    def commit_status(self, state, *, entry=None, bundle=None):
        # Callers synchronize before writing; syncing here would reject the
        # verified bundle that is about to be included in this same commit.
        staged = ['automatizacion/estado.json']
        if entry is not None:
            if entry['status'] == 'success':
                target = self.root / entry['folder']
                if bundle is not None:
                    if target.exists():
                        raise ValueError('Refusing to overwrite an existing delivery folder')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(bundle, target)
                verify_bundle(target, entry['slot'])
                staged.append(entry['folder'])
            record = f'automatizacion/entregas/{entry["tag"]}.json'
            json_write(self.root / record, entry)
            staged.append(record)
            self.update_index()
            staged += ['automatizacion/ENTREGAS.md', 'README.md']
        json_write(self.directory / 'estado.json', state)
        self.runner.git('add', *staged)
        diff = self.runner.git('diff', '--cached', '--quiet', check=False)
        if diff.returncode not in (0, 1):
            raise CommandError('Git status diff', diff)
        if diff.returncode:
            self.runner.git('-c', 'user.name=github-actions[bot]', '-c', f'user.email={BOT_EMAIL}',
                            'commit', '-m', f'Production {state["status"]}: {state["tag"]}')
        self.push()

    def published_entry(self, date, number, manifest):
        folder = f'videos/{number:03d}'
        files = manifest['files']
        return dict(status='success', number=number, slot=iso(date), tag=tag_for(date),
                    title=manifest['title'], folder=folder, card_path=f'{folder}/README.md',
                    url=f'https://github.com/{self.repository}/tree/main/{folder}',
                    assets={name: dict(path=name, **meta) for name, meta in files.items() if meta is not None},
                    published_at=iso(dt.datetime.now(dt.timezone.utc)),
                    plan_id=manifest.get('plan_id'), creative_identity=creative_identity(manifest),
                    validation=manifest['video_checks'], published_to_youtube=False)

    def reject_repeated_video(self, manifest):
        used = set()
        for item in self.entries():
            for name, meta in item.get('assets', {}).items():
                if name.endswith('.mp4') and isinstance(meta, dict) and meta.get('sha256'):
                    used.add(meta['sha256'])
        for path in (self.root / 'videos').glob('*/manifest.json'):
            previous = json.loads(path.read_text())
            used.update(meta['sha256'] for name, meta in previous.get('files', {}).items()
                        if name.endswith('.mp4') and isinstance(meta, dict) and meta.get('sha256'))
        if any(meta['sha256'] in used for name, meta in manifest['files'].items() if name.endswith('.mp4')):
            raise ValueError('A rendered video has already appeared in the delivery history')

    def persist_failure(self, base, reservation, error):
        message = str(error) if isinstance(error, (CommandError, ValueError)) else type(error).__name__
        message = re.sub(r'[\r\n\t]+', ' ', message)
        message = re.sub(r'(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]+', '[redacted]', message)[:300]
        state = dict(base, status='failure', failed_at=iso(dt.datetime.now(dt.timezone.utc)),
                     error_type=type(error).__name__, error_message=message,
                     error='The scheduled production failed; inspect the Actions run log.')
        # A failed push leaves a complete local success commit. Do not replace
        # its durable record with failure or consume another delivery number.
        current = self.entry_for(base['tag'])
        if current and current.get('status') == 'success':
            record = f'automatizacion/entregas/{base["tag"]}.json'
            committed = self.runner.git('show', f'HEAD:{record}', check=False)
            durable = committed.returncode == 0 and json.loads(committed.stdout).get('status') == 'success'
            print('Delivery committed locally; retry will push the existing files.' if durable else
                  'Validated delivery is staged; retry will finish the existing commit.', file=sys.stderr)
            return
        try:
            self.commit_status(state, entry=dict(reservation, status='failure') if reservation else None)
        except Exception:
            print('Unable to persist failure status; inspect the Actions run.', file=sys.stderr)

    def execute(self, date, cache, produce):
        tag = tag_for(date)
        self.recover_staged_delivery(date)
        self.sync()
        reservation = self.entry_for(tag)
        run_id = os.environ.get('GITHUB_RUN_ID')
        base = dict(slot=iso(date), tag=tag,
                    run_url=f'https://github.com/{self.repository}/actions/runs/{run_id}' if run_id else None,
                    schedule_utc='0 */4 * * *', interval_hours=4, published_to_youtube=False)
        if reservation and reservation.get('status') == 'success':
            self.ensure_lfs(reservation['number'])
            self.runner.git('lfs', 'pull', '--include', reservation['folder'] + '/**', '--exclude', '')
            verify_bundle(self.root / reservation['folder'], iso(date))
            self.push()
            print(f'Already committed: {tag}')
            return reservation
        try:
            plan = self.planner(date, self.root, exclude_tag=tag)
            identity = creative_identity(plan)
        except NeedsNewAssets as error:
            blocked = dict(base, status='needs_new_assets', reason=str(error),
                           checked_at=iso(dt.datetime.now(dt.timezone.utc)),
                           required='An unpublished original scene and an unused music programme.')
            self.commit_status(blocked)
            print('needs_new_assets: no unused original scene and music programme remain.')
            return blocked
        except Exception as error:
            self.persist_failure(base, reservation, error)
            raise
        reservation = self.reserve(date)
        number = reservation['number']
        base['number'] = number
        reservation = dict(reservation, status='pending', creative_identity=identity, plan_id=plan['id'])
        try:
            self.ensure_lfs(number)
            self.commit_status(dict(base, status='running', started_at=iso(dt.datetime.now(dt.timezone.utc))),
                               entry=reservation)
            with tempfile.TemporaryDirectory(prefix='jagoncito-publish-') as temporary:
                folder = Path(temporary) / 'bundle'
                produce(date, folder, cache, plan)
                manifest = verify_bundle(folder, iso(date))
                if creative_identity(manifest) != identity or file_hash(folder / 'imagen.png') != identity['scene_sha256']:
                    raise ValueError('Rendered bundle does not match the unused creative plan')
                chapters = manifest['audio'].get('chapters', [])
                actual_program = sorted({chapter['number'] for chapter in chapters})
                if actual_program != identity['program']:
                    raise ValueError('Rendered music does not match the unused programme')
                if 'works' in manifest and sorted(set(manifest['works'])) != identity['program']:
                    raise ValueError('Manifest works do not match the unused programme')
                self.reject_repeated_video(manifest)
                entry = self.published_entry(date, number, manifest)
                entry['assets']['manifest.json'] = dict(path='manifest.json',
                    bytes=(folder / 'manifest.json').stat().st_size, sha256=file_hash(folder / 'manifest.json'))
                self.commit_status(dict(base, status='success', completed_at=iso(dt.datetime.now(dt.timezone.utc)),
                                        folder=entry['folder']), entry=entry, bundle=folder)
                print(entry['url'])
                return entry
        except Exception as error:
            self.persist_failure(base, reservation, error)
            raise


def recover_prior_completed_delivery(publisher, date, cache, produce):
    """Finish a prior reservation before considering another delivery number.

    A new Actions runner can only see the remote pending reservation after a
    failed final push. Retry that same slot/number; render again only when its
    verified bundle is no longer available in the checkout.
    """
    candidates = sorted(publisher.entries(), key=lambda entry: entry.get('number', 0))
    for item in candidates:
        if item.get('status') == 'success' and item.get('tag'):
            try:
                previous = utc_slot(item['slot'])
            except (KeyError, ValueError, TypeError):
                continue
            if previous < date:
                publisher.recover_staged_delivery(previous)
    publisher.sync()
    ahead = publisher.runner.git('rev-list', '--count', 'origin/main..HEAD').stdout.strip()
    for item in sorted(publisher.entries(), key=lambda entry: entry.get('number', 0), reverse=True):
        if item.get('status') not in ('success', 'pending', 'failure') or not item.get('tag'):
            continue
        try:
            previous = utc_slot(item['slot'])
        except (KeyError, ValueError, TypeError):
            continue
        if previous >= date or item['tag'] != tag_for(previous):
            continue
        if item['status'] == 'success':
            if ahead != '0':
                return publisher.execute(previous, cache, produce)
        elif item.get('creative_identity') and item.get('plan_id'):
            return publisher.execute(previous, cache, produce)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--slot')
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY'))
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if not args.repository:
        raise ValueError('GITHUB_REPOSITORY is required')

    def produce(date, folder, cache, plan):
        subprocess.run([sys.executable, str(root / 'automatizacion/produccion/crear_entrega.py'),
                        '--slot', iso(date), '--output', str(folder), '--cache', str(cache),
                        '--plan-id', plan['id'], '--history-exclude-tag', tag_for(date)], check=True, cwd=root)

    publisher = Publisher(root, args.repository)
    date = utc_slot(args.slot)
    if args.slot is None:
        recover_prior_completed_delivery(publisher, date, args.cache, produce)
    publisher.execute(date, args.cache, produce)


if __name__ == '__main__':
    main()
