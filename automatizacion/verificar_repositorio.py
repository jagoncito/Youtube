#!/usr/bin/env python3
"""Validate real numbered deliveries, or their exact Git LFS representations."""
from pathlib import Path
import hashlib,json,re

ROOT=Path(__file__).resolve().parents[1]
REQUIRED={'video-30min.mp4','bucle-6min.mp4','audio-bucle-6min.wav','imagen.png','miniatura.jpg','publicacion.txt','README.md','manifest.json'}

def inspect(path):
    with path.open('rb') as stream:
        prefix=stream.read(200)
        if prefix.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            data=path.read_text()
            oid=re.search(r'^oid sha256:([0-9a-f]{64})$',data,re.M)
            size=re.search(r'^size ([0-9]+)$',data,re.M)
            if not oid or not size:raise ValueError(f'Invalid LFS pointer: {path.name}')
            return int(size.group(1)),oid.group(1),True
        stream.seek(0)
        return path.stat().st_size,hashlib.file_digest(stream,'sha256').hexdigest(),False

def main():
    folders=sorted(p for p in (ROOT/'videos').iterdir() if p.is_dir())
    if not folders or any(not re.fullmatch(r'[0-9]{3}',p.name) for p in folders):
        raise ValueError('Every delivery must have one three-digit folder; no aliases')
    records=[json.loads(p.read_text()) for p in (ROOT/'automatizacion/entregas').glob('*.json')]
    published={item['number']:item for item in records if item.get('status')=='success'}
    if len(published)!=sum(item.get('status')=='success' for item in records):
        raise ValueError('Duplicate delivery number')
    if set(published)!={int(p.name) for p in folders}:
        raise ValueError('Folder and published index disagree')
    total=0
    for folder in folders:
        number=int(folder.name);entry=published[number]
        if entry.get('folder')!=f'videos/{folder.name}' or entry.get('card_path')!=f'videos/{folder.name}/README.md':
            raise ValueError('Index must point directly to the real delivery')
        names={p.name for p in folder.iterdir() if p.is_file()}
        if not REQUIRED.issubset(names):raise ValueError('Delivery is missing actual files')
        manifest=json.loads((folder/'manifest.json').read_text())
        expected=set(manifest['files'])|{'manifest.json'}
        actual={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        if expected!=actual:raise ValueError(f'Incorrect file inventory in {folder.name}')
        for name,meta in manifest['files'].items():
            p=folder/name
            if p.is_symlink() or not p.resolve().is_relative_to(folder.resolve()):raise ValueError('File alias/unsafe path')
            size,sha,pointer=inspect(p)
            if (size,sha)!=(meta['bytes'],meta['sha256']):raise ValueError(f'Corrupt file: {folder.name}/{name}')
            if pointer and p.suffix.lower() not in ('.mp4','.wav'):raise ValueError('Unexpected pointer')
            stored=entry['assets'][name]
            if stored.get('path')!=name or (stored['bytes'],stored['sha256'])!=(size,sha):
                raise ValueError('Asset registry does not describe the actual file')
            if p.suffix.lower() in ('.mp4','.wav'):total+=1
        image_sha=manifest['files']['imagen.png']['sha256']
        if manifest['creative_identity']['scene_sha256']!=image_sha or entry['creative_identity']!=manifest['creative_identity']:
            raise ValueError('Creative identity mismatch')
        for name in ['README.md']:
            text=(folder/name).read_text()
            if 'video-000' in text or '002-jagoncito-satie' in text:raise ValueError('Old bridge reference')
        print(f'{folder.name}: archivos, manifiesto e índice correctos')
    for p in [ROOT/'README.md',ROOT/'automatizacion/ENTREGAS.md']:
        text=p.read_text()
        if re.search(r'videos/(?:video-000[123]|002-jagoncito-satie)',text):raise ValueError('Old index reference')
    print(f'PASS: {len(folders)} carpetas reales y {total} medios MP4/WAV íntegros.')

if __name__=='__main__':main()
