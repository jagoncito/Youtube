#!/usr/bin/env python3
"""Audit chosen digital notation against compiled MIDI, including grace and ties."""
from pathlib import Path
from collections import defaultdict,Counter
import json,hashlib,math
import mido
R=Path(__file__).resolve().parent
src=json.loads((R/'source-events.json').read_text())
notes=[dict(e,source_index=i) for i,e in enumerate(src) if e['kind']=='NOTE']
mid=mido.MidiFile(R/'partitura.midi'); out=[]
for tr in mid.tracks:
 name=next((e.name for e in tr if e.type=='track_name'),'')
 if name.startswith('lower:'):staff='lower'
 elif name.startswith('upper:'):staff='upper'
 else:continue
 tick=0;active=defaultdict(list);idx=0
 for e in tr:
  tick+=e.time
  if e.type=='note_on' and e.velocity:
   active[e.channel,e.note].append((tick,e.velocity))
  elif e.type=='note_off' or e.type=='note_on' and not e.velocity:
   assert active[e.channel,e.note],(staff,tick,e)
   begin,v=active[e.channel,e.note].pop(0)
   out.append(dict(id=f'{staff}:{idx}',staff=staff,pitch=e.note,onset_quarter=begin/mid.ticks_per_beat,gate_quarters=(tick-begin)/mid.ticks_per_beat,velocity=v));idx+=1
 assert not any(active.values())
 assert tick==324*mid.ticks_per_beat
used=set();pending=[]
for e in sorted(out,key=lambda x:x['onset_quarter']):
 candidates=[n for n in notes if n['source_index'] not in used and n['staff']==e['staff'] and n['pitch']==e['pitch'] and n['grace_quarter']==0 and abs(n['quarter']-e['onset_quarter'])<=1/mid.ticks_per_beat+.000001]
 if not candidates:pending.append(e);continue
 n=min(candidates,key=lambda x:abs(x['quarter']-e['onset_quarter']));used.add(n['source_index']);e.update(main_quarter=n['quarter'],grace_quarter=n['grace_quarter'],voice=n['voice'],bar=n['bar'],source_index=n['source_index'],notated_duration_quarters=n['duration_quarters'])
for e in pending:
 candidates=[n for n in notes if n['source_index'] not in used and n['staff']==e['staff'] and n['pitch']==e['pitch'] and n['grace_quarter']!=0 and -.01<=n['quarter']-e['onset_quarter']<1.01]
 assert candidates,('unmatched MIDI',e)
 n=min(candidates,key=lambda x:abs(x['quarter']-e['onset_quarter']));used.add(n['source_index']);e.update(main_quarter=n['quarter'],grace_quarter=n['grace_quarter'],voice=n['voice'],bar=n['bar'],source_index=n['source_index'],notated_duration_quarters=n['duration_quarters'])
missing=[n for n in notes if n['source_index'] not in used]
ties={(e['staff'],e['voice'],e['quarter']) for e in src if e['kind']=='TIE'}
explained=[];bad=[]
for n in missing:
 prev=[p for p in notes if p['pitch']==n['pitch'] and p['voice']==n['voice'] and abs(p['quarter']+p['duration_quarters']-n['quarter'])<1e-7 and (p['staff'],p['voice'],p['quarter']) in ties]
 unisons=[p for p in notes if p['source_index'] in used and p['staff']==n['staff'] and p['pitch']==n['pitch'] and p['quarter']==n['quarter'] and p['grace_quarter']==n['grace_quarter']]
 if prev:explained.append(dict(n,reason='tied continuation',previous_source_index=prev[0]['source_index']))
 elif unisons:explained.append(dict(n,reason='simultaneous unison consolidated',matching_source_index=unisons[0]['source_index']))
 else:bad.append(n)
print('MIDI',len(out),'notation',len(notes),'grace mapped',sum(e['grace_quarter']!=0 for e in out),'omissions',Counter(e['reason'] for e in explained),'unexplained',len(bad))
if bad:print(json.dumps(bad,indent=2))
assert not bad,'Unexplained omissions in MIDI'
out.sort(key=lambda e:(e['onset_quarter'],e['staff'],e['pitch']))
(R/'mapped-midi-notes.json').write_text(json.dumps(out,indent=2)+'\n')
report={'source_repository':'https://github.com/MutopiaProject/MutopiaProject','source_commit':'2144afd6f52d56c5b6995b8b589ef1268b3139f0','source_path':'ftp/DebussyC/L75/debussy_Ste_Bergamesq_Clair/debussy_Ste_Bergamesq_Clair.ly','source_transcription':'Keith OHara / Mutopia-2010/12/21-1778','source_declared_edition':'E. Fromont, 1905','source_license':'Public Domain declaration by typesetter','status':'passed','bars':72,'meter':[9,8],'quarter_beats':324,'midi_onsets':len(out),'printed_notes':len(notes),'mapped_grace_notes':sum(e['grace_quarter']!=0 for e in out),'no_hanging_notes':True,'staff_end_alignment_quarters':324,'omitted_written_attacks':dict(Counter(e['reason'] for e in explained)),'explained_omissions':explained,'event_counts':dict(Counter(e['kind'] for e in src)),'scope':'Fidelity to chosen digital transcription; not an independent historical facsimile collation or subjective listening assessment.','files':{}}
for p in [R/'original/clair-de-lune.ly',R/'adapted/clair-de-lune.ly',R/'partitura.pdf',R/'partitura.midi',R/'source-events.json',R/'mapped-midi-notes.json']:
 report['files'][str(p.relative_to(R))]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
original=(R/'original/clair-de-lune.ly').read_bytes()
blob=hashlib.sha1(f'blob {len(original)}\0'.encode()+original).hexdigest()
assert blob=='16d44595b18ad819016f3948a9b666f95e45aadd'
report['source_git_blob']=blob
report['typesetter_public_domain_declaration']='Original header license=Public Domain; tagline explicitly places this sheet music in the public domain.'
report['numeric_midi_tempo_is_not_authored']=True
(R/'score-validation.json').write_text(json.dumps(report,indent=2)+'\n')
