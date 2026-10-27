#!/usr/bin/env python3
"""Restore pinned CC0 VSCO2 CE sample files and SFZs from the supplied manifest.

Python standard library only. Keeps the normal HTTPS proxy and TLS verification.
Original SFZs are saved separately; POSIX path normalization is deterministic.
"""
import argparse, concurrent.futures, hashlib, json, urllib.request
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,default=Path(__file__).with_name('instrument-sources.json'));p.add_argument('--dest',type=Path,required=True);p.add_argument('--workers',type=int,default=6);a=p.parse_args()
 manifest=json.loads(a.manifest.read_text());a.dest.mkdir(parents=True,exist_ok=True)
 def restore(rec):
  rel=Path(rec['path'])
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe manifest path')
  out_is_sfz=str(rel).endswith('.sfz')
  out=a.dest/('original-sfz' if out_is_sfz else '')/rel
  out.parent.mkdir(parents=True,exist_ok=True)
  if out.exists():data=out.read_bytes()
  else:
   with urllib.request.urlopen(rec['url'],timeout=120) as r:data=r.read()
  if len(data)!=rec['bytes'] or hashlib.sha256(data).hexdigest()!=rec['sha256']:raise ValueError(f'Integrity check failed: {rel}')
  out.write_bytes(data)
  if out_is_sfz:(a.dest/rel).write_text(data.decode().replace('\\','/'))
  return str(rel)
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
  for i,name in enumerate(pool.map(restore,manifest['files']),1):
   if i%50==0:print(f'{i}/{len(manifest["files"])} verified',flush=True)
 print(f'Restored and SHA256-verified {len(manifest["files"])} files into {a.dest}')
if __name__=='__main__':main()
