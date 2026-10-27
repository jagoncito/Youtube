from pathlib import Path
from fractions import Fraction
import json,collections
ROOT=Path(__file__).resolve().parent
out=[]
for line in (ROOT/'events.stdout.log').read_text().splitlines():
 if not line.startswith('EV|'):continue
 v=line.split('|');kind,staff,voice=v[1:4]
 e=dict(kind=kind,staff=staff,voice=voice,quarter=float(Fraction(int(v[4])*4,int(v[5]))),grace_quarter=float(Fraction(int(v[6])*4,int(v[7]))),bar=int(v[8]))
 if kind=='NOTE':e.update(pitch=int(v[9]),duration_quarters=float(Fraction(int(v[10])*4,int(v[11]))))
 elif kind=='DYNAMIC':e['dynamic']=json.loads(v[9])
 elif kind in ('SLUR','PHRASE','PEDAL'):e['direction']=int(v[9])
 elif kind=='ART':e['articulation']=v[9]
 elif kind in ('CRESCENDO','DECRESCENDO'):e.update(direction=int(v[9]),text='|'.join(v[10:]))
 elif kind=='TEXT':e['text']='|'.join(v[9:])
 out.append(e)
(ROOT/'source-events.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
print(collections.Counter(x['kind'] for x in out));print('Notes bystaff',collections.Counter(e['staff'] for e in out if e['kind']=='NOTE'))
print('Grace notes',sum(x['kind']=='NOTE' and x['grace_quarter']!=0 for x in out))
