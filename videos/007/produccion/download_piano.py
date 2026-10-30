#!/usr/bin/env python3
"""Restore pinned Salamander source files; normal HTTPS with size/SHA256 checks.

No credentials or network-policy changes. The JSON manifest is part of the
instrument attribution package. Bulk isolated FLAC samples are not film audio.
"""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,urllib.request,fnmatch

def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--dest',type=Path,required=True);p.add_argument('--workers',type=int,default=5);p.add_argument('--include',action='append',default=[]);a=p.parse_args()
 m=json.loads(a.manifest.read_text());rows=[r for r in m['files'] if not a.include or any(fnmatch.fnmatchcase(r['path'],pattern) for pattern in a.include)]
 a.dest.mkdir(parents=True,exist_ok=True)
 def restore(row):
  rel=Path(row['path'])
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe source path')
  out=a.dest/rel;out.parent.mkdir(parents=True,exist_ok=True)
  if out.exists():data=out.read_bytes()
  else:
   with urllib.request.urlopen(row['url'],timeout=45) as response:data=response.read()
  if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Source integrity failure: '+str(rel))
  out.write_bytes(data)
  return len(data)
 total=0
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
  for i,size in enumerate(pool.map(restore,rows),1):
   total+=size
   if i%50==0:print(f'{i}/{len(rows)} files SHA256 verified',flush=True)
 print(f'Restored and verified {len(rows)} pinned files / {total} bytes in {a.dest}')
if __name__=='__main__':main()
