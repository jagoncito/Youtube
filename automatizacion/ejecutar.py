#!/usr/bin/env python3
"""Run one four-hour production slot and publish its validated bundle to Releases."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile
from zoneinfo import ZoneInfo

BOT_EMAIL = '41898282+github-actions[bot]@users.noreply.github.com'
REQUIRED = {'video-30min.mp4', 'bucle-6min.mp4', 'audio-bucle-6min.wav',
            'imagen.png', 'miniatura.jpg', 'publicacion.txt', 'README.md', 'manifest.json'}

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
            # Avoid writing credentials, request headers or raw external stderr
            # into the public status document.
            raise CommandError(str(args[0]), result)
        return result

    def git(self, *args, check=True):
        return self.call(['git', *args], check=check)

    def gh(self, *args, check=True):
        return self.call(['gh', *args], check=check)


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


def verify_bundle(folder, slot):
    if not REQUIRED.issubset({p.name for p in folder.iterdir() if p.is_file()}):
        raise ValueError('Incomplete production bundle')
    manifest = json.loads((folder / 'manifest.json').read_text())
    if manifest['slot'] != slot:
        raise ValueError('Bundle slot mismatch')
    if not (REQUIRED - {'manifest.json'}).issubset(manifest['files']):
        raise ValueError('Required assets are missing from the checksum manifest')
    for name, meta in manifest['files'].items():
        path = (folder / name).resolve()
        if not path.is_relative_to(folder.resolve()) or not path.is_file():
            raise ValueError('Unsafe or missing manifest file')
        if path.stat().st_size != meta['bytes'] or file_hash(path) != meta['sha256']:
            raise ValueError('Bundle checksum mismatch')
    for name, duration in [('bucle-6min.mp4', 360), ('video-30min.mp4', 1800)]:
        result = manifest['video_checks'][name]
        if result['complete_decode_exit_code'] != 0 or result['duration_seconds'] != duration:
            raise ValueError('Production validation did not pass')
    if manifest['audio']['clipped_samples'] != 0:
        raise ValueError('Audio validation did not pass')
    return manifest


class Publisher:
    def __init__(self, root, repository, runner=None):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ValueError('Invalid repository identity')
        self.root = Path(root)
        self.repository = repository
        self.runner = runner or Runner(root)
        self.directory = self.root / 'automatizacion'

    def release(self, tag):
        response = self.runner.gh('api', f'repos/{self.repository}/releases/tags/{tag}', check=False)
        if response.returncode == 0:
            return json.loads(response.stdout)
        if re.search(r'\bHTTP 404\b', response.stderr):
            # A missing release is only accepted after the repository itself is
            # readable. This avoids treating an auth failure as a missing tag.
            self.runner.gh('api', f'repos/{self.repository}', '--jq', '.full_name')
            return None
        raise CommandError('GitHub release lookup', response)

    def sync(self):
        if self.runner.git('status', '--porcelain').stdout.strip():
            raise ValueError('Refusing to update status over a dirty checkout')
        self.runner.git('fetch', 'origin', 'main')
        self.runner.git('merge', '--ff-only', 'origin/main')

    def entries(self):
        return [json.loads(path.read_text()) for path in
                (self.directory / 'entregas').glob('*.json')]

    def entry_for(self, tag):
        path = self.directory / 'entregas' / f'{tag}.json'
        return json.loads(path.read_text()) if path.exists() else None

    def reserve(self, date):
        tag = tag_for(date)
        current = self.entry_for(tag)
        if current is not None:
            return current
        number = max([1] + [int(x['number']) for x in self.entries()
                            if isinstance(x.get('number'), int)]) + 1
        return dict(number=number, status='pending', slot=iso(date), tag=tag,
                    title='Producción pendiente', published_to_youtube=False)

    def card_text(self, entry):
        stamp = dt.datetime.fromisoformat(entry.get('published_at', entry['slot']).replace('Z', '+00:00'))
        local = stamp.astimezone(ZoneInfo('Europe/Madrid')).strftime('%d/%m/%Y %H:%M %Z')
        assets = entry.get('assets', {})
        rows = [('video-30min.mp4', 'Vídeo completo — 30:00'),
                ('bucle-6min.mp4', 'Vídeo para bucle — 6:00'),
                ('audio-bucle-6min.wav', 'Único audio WAV — 6:00'),
                ('imagen.png', 'Imagen principal'), ('miniatura.jpg', 'Miniatura'),
                ('publicacion.txt', 'Título, descripción, capítulos y etiquetas'),
                ('fuentes-y-validacion.zip', 'Fuentes, licencias y comprobaciones')]
        text = f'# Vídeo {entry["number"]:03d} — {entry["title"]}\n\n'
        text += f'Publicado en GitHub: **{local}**. Los dos MP4 ya llevan el audio incorporado.\n\n'
        text += f'[Abrir todos los archivos en GitHub Releases]({entry["url"]})\n\n'
        for name, label in rows:
            if name in assets:
                text += f'- [{label}]({assets[name]["url"]})\n'
        if 'miniatura.jpg' in assets:
            text += f'\n![Miniatura]({assets["miniatura.jpg"]["url"]})\n'
        text += '\nLa sesión repite cinco veces el programa de seis minutos. '
        text += 'Consulta las obras y tiempos reales en [manifest.json](manifest.json). '
        text += 'Esta entrega está en GitHub; no se ha publicado automáticamente en YouTube.\n'
        return text

    def commit_status(self, state, *, entry=None, card_files=None):
        self.sync()
        json_write(self.directory / 'estado.json', state)
        staged = ['automatizacion/estado.json', 'automatizacion/ENTREGAS.md', 'README.md']
        if entry is not None:
            json_write(self.directory / 'entregas' / f'{entry["tag"]}.json', entry)
            staged.append(f'automatizacion/entregas/{entry["tag"]}.json')
            if entry['status'] == 'success':
                card = self.root / entry['card_path']
                card.parent.mkdir(parents=True, exist_ok=True)
                card.write_text(self.card_text(entry))
                if not card_files:
                    raise ValueError('Successful delivery needs its publication and manifest files')
                for name in ['publicacion.txt', 'manifest.json']:
                    (card.parent / name).write_text(card_files[name])
                staged.append(str(card.parent.relative_to(self.root)))
        records = [item for item in self.entries() if item.get('status') == 'success']
        records.sort(key=lambda x: x.get('number', 0))
        table = '# Entregas automáticas\n\nCada fila corresponde a un paquete completo subido a GitHub Releases.\n\n'
        table += '| Número | Vídeo | Carpeta | Archivos |\n| --- | --- | --- | --- |\n'
        root_links = []
        for item in records:
            title = item['title'].replace('|', '\\|').replace('\n', ' ')
            card_path = item.get('card_path', f'videos/video-{item["number"]:04d}/README.md')
            table += (f'| {item["number"]:03d} | {title} | [Abrir carpeta](../{card_path}) '
                      f'| [Descargar]({item["url"]}) |\n')
            root_links.append(f'- [Vídeo {item["number"]:03d} — {title}]({card_path})')
        (self.directory / 'ENTREGAS.md').write_text(table)
        readme = self.root / 'README.md'
        current = readme.read_text() if readme.exists() else '# Jagoncito\n'
        start, end = '<!-- JAGONCITO:ENTREGAS:START -->', '<!-- JAGONCITO:ENTREGAS:END -->'
        managed = start + '\n\n' + '\n'.join(root_links) + '\n\n' + end
        if start in current and end in current:
            current = current[:current.index(start)] + managed + current[current.index(end) + len(end):]
        else:
            current += '\n\n## Vídeos por orden\n\n' + managed + '\n'
        readme.write_text(current)
        self.runner.git('add', *staged)
        diff = self.runner.git('diff', '--cached', '--quiet', check=False)
        if diff.returncode == 0:
            return
        if diff.returncode != 1:
            raise CommandError('Git status diff', diff)
        self.runner.git('-c', 'user.name=github-actions[bot]', '-c', f'user.email={BOT_EMAIL}',
                        'commit', '-m', f'Production {state["status"]}: {state["tag"]}')
        self.runner.git('push', 'origin', 'HEAD:main')

    def published_entry(self, date, release, number, manifest=None):
        assets = {x['name']: {'bytes': x['size'], 'url': x['browser_download_url']}
                  for x in release.get('assets', [])}
        if not REQUIRED.issubset(assets):
            raise ValueError('Published release is incomplete; do not silently skip it')
        title = (manifest or {}).get('title') or re.sub(
            r'^Vídeo\s+\d+\s+—\s+', '', release.get('name') or tag_for(date))
        return dict(status='success', number=number, slot=iso(date), tag=tag_for(date),
                    title=title, url=release['html_url'], assets=assets,
                    published_at=release.get('published_at') or iso(dt.datetime.now(dt.timezone.utc)),
                    card_path=f'videos/video-{number:04d}/README.md',
                    plan_id=(manifest or {}).get('plan_id'),
                    validation=(manifest or {}).get('video_checks'),
                    published_to_youtube=False)

    def recover_card_files(self, tag):
        with tempfile.TemporaryDirectory(prefix='jagoncito-card-') as folder:
            self.runner.gh('release', 'download', tag, '--repo', self.repository,
                           '--pattern', 'manifest.json', '--pattern', 'publicacion.txt', '--dir', folder)
            return {name: (Path(folder) / name).read_text()
                    for name in ['manifest.json', 'publicacion.txt']}

    def persist_failure(self, base, reservation, error):
        failure = dict(base, status='failure', failed_at=iso(dt.datetime.now(dt.timezone.utc)),
                       error_type=type(error).__name__,
                       error='The scheduled production failed; inspect the Actions run log.')
        try:
            self.commit_status(failure, entry=dict(reservation, status='failure'))
        except Exception:
            print('Unable to persist failure status; inspect the Actions run.', file=sys.stderr)

    def execute(self, date, cache, produce):
        tag = tag_for(date)
        self.sync()
        reservation = self.reserve(date)
        number = reservation['number']
        run_id = os.environ.get('GITHUB_RUN_ID')
        run_url = f'https://github.com/{self.repository}/actions/runs/{run_id}' if run_id else None
        base = dict(slot=iso(date), tag=tag, number=number, run_url=run_url, schedule_utc='0 */4 * * *',
                    interval_hours=4, published_to_youtube=False)
        try:
            release = self.release(tag)
        except Exception as error:
            self.persist_failure(base, reservation, error)
            raise
        if release and not release['draft']:
            entry = self.published_entry(date, release, number)
            record = self.directory / 'entregas' / f'{tag}.json'
            if record.is_file() and json.loads(record.read_text()).get('status') == 'success':
                print(f'Already published: {tag}')
                return entry
            self.commit_status(dict(base, status='success', recovered=True), entry=entry,
                               card_files=self.recover_card_files(tag))
            return entry
        self.commit_status(dict(base, status='running', started_at=iso(dt.datetime.now(dt.timezone.utc))),
                           entry=reservation)
        try:
            with tempfile.TemporaryDirectory(prefix='jagoncito-publish-') as temporary:
                folder = Path(temporary) / 'bundle'
                produce(date, folder, cache)
                manifest = verify_bundle(folder, iso(date))
                # Sources and checks travel with the media, with no private studies.
                archive = folder / 'fuentes-y-validacion.zip'
                with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as output:
                    for item in sorted((folder / 'fuentes').rglob('*')):
                        if item.is_file():
                            output.write(item, item.relative_to(folder))
                    output.write(folder / 'manifest.json', 'manifest.json')
                notes = folder / '.release-notes.md'
                notes.write_text((folder / 'README.md').read_text() + '\n\n' +
                                 (folder / 'publicacion.txt').read_text())
                title = f'Vídeo {number:03d} — {manifest["title"]}'
                if release is None:
                    self.runner.gh('release', 'create', tag, '--repo', self.repository, '--draft',
                                   '--target', 'main', '--title', title, '--notes-file', notes)
                else:
                    self.runner.gh('release', 'edit', tag, '--repo', self.repository,
                                   '--title', title, '--notes-file', notes)
                upload = [str(folder / name) for name in sorted(REQUIRED)] + [str(archive)]
                self.runner.gh('release', 'upload', tag, *upload, '--repo', self.repository, '--clobber')
                uploaded = self.release(tag)
                remote = {x['name']: x for x in uploaded.get('assets', [])}
                for item in upload:
                    path = Path(item)
                    stored = remote.get(path.name, {})
                    if stored.get('size') != path.stat().st_size:
                        raise ValueError('Release asset verification failed')
                    if stored.get('digest') and stored['digest'] != 'sha256:' + file_hash(path):
                        raise ValueError('Release asset checksum verification failed')
                self.runner.gh('release', 'edit', tag, '--repo', self.repository, '--draft=false')
                published = self.release(tag)
                if published['draft']:
                    raise ValueError('Release is still a draft')
                entry = self.published_entry(date, published, number, manifest)
                card_files = {name: (folder / name).read_text()
                              for name in ['manifest.json', 'publicacion.txt']}
                self.commit_status(dict(base, status='success', completed_at=iso(dt.datetime.now(dt.timezone.utc)),
                                        release_url=entry['url']), entry=entry, card_files=card_files)
                print(entry['url'])
                return entry
        except Exception as error:
            self.persist_failure(base, reservation, error)
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--slot')
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY'))
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if not args.repository:
        raise ValueError('GITHUB_REPOSITORY is required')
    def produce(date, folder, cache):
        subprocess.run([sys.executable, str(root / 'automatizacion/produccion/crear_entrega.py'),
                        '--slot', iso(date), '--output', str(folder), '--cache', str(cache)], check=True, cwd=root)
    Publisher(root, args.repository).execute(utc_slot(args.slot), args.cache, produce)

if __name__ == '__main__':
    main()
