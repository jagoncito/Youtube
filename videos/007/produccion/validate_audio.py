#!/usr/bin/env python3
"""Complete PCM, MIDI, score-anchor, printed-ornament and pedal measurements.

These checks cannot judge perceived tone, phrasing or listener preference.
No subjective audition is asserted.
"""
from pathlib import Path
import argparse,collections,json
import numpy as np
import soundfile as sf
import mido


def main():
 p=argparse.ArgumentParser();p.add_argument('--audio',type=Path,required=True)
 p.add_argument('--performance',type=Path,required=True);p.add_argument('--midi',type=Path,required=True)
 p.add_argument('--score',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 info=sf.info(a.audio);x,sr=sf.read(a.audio,dtype='float32')
 spec=json.loads(a.performance.read_text());source=json.loads((a.score/'mapped-midi-notes.json').read_text())
 ornaments=json.loads((a.score/'ornament-realization.json').read_text())
 assert info.subtype=='PCM_24' and sr==48000 and x.ndim==2 and x.shape[1]==2
 assert abs(len(x)/sr-spec['duration'])<1/sr
 assert np.isfinite(x).all() and np.max(np.abs(x))<.84
 clipped=int(np.count_nonzero(np.abs(x)>=.99999));assert not clipped
 tail=x[-round(sr*.1):];tail_peak=float(np.max(np.abs(tail)));assert tail_peak<1e-5
 anchors={e['source_id']:e for e in spec['events'] if e['source_id'] is not None}
 assert len(anchors)==len(source)==1629
 assert set(anchors)=={n['id'] for n in source}
 assert all(anchors[n['id']]['pitch']==n['pitch'] for n in source)
 assert sum(anchors[n['id']]['grace'] for n in source)==6
 turnnotes=[e for e in spec['events'] if e['written_turn_realization']]
 assert len(turnnotes)==ornaments['added_attacks']==12
 for turn in ornaments['turns']:
  realized=sorted([e for e in turnnotes if e['bar']==turn['bar']],key=lambda e:e['start'])
  assert [(e['pitch'],e['source_quarter']) for e in realized]==[(e['pitch'],e['quarter']) for e in turn['new_attacks']]
  assert all(e['derived_from_source_id']==turn['principal_midi_id'] for e in realized)
  assert anchors[turn['principal_midi_id']]['pitch']==turn['principal_pitch']
 # Audit all printed anchors and all derived ornament notes after MIDI export.
 mid=mido.MidiFile(a.midi);active=collections.Counter();notes=0;damper=0;reimport=[];controls=[]
 elapsed=0.
 for e in mid:
  elapsed+=e.time
  if e.type=='note_on' and e.velocity:
   active[e.note]+=1;notes+=1;reimport.append((round(elapsed*1000),e.note,e.velocity))
  elif e.type=='note_off' or e.type=='note_on' and not e.velocity:
   assert active[e.note]>0;active[e.note]-=1
  elif e.type=='control_change':
   if e.control==64:damper=e.value;controls.append((round(elapsed*1000),e.control,e.value))
 assert not any(active.values()) and damper==0
 assert notes==len(spec['events'])==1641 and abs(mid.length-spec['duration'])<.0011
 expected=sorted((round(e['start']*1000),e['pitch'],e['velocity']) for e in spec['events'])
 assert sorted(reimport)==expected
 assert sorted(controls)==sorted((round(e['time']*1000),e['cc'],e['value']) for e in spec['cc_events'])
 same=collections.defaultdict(list)
 for e in spec['events']:same[e['pitch']].append(e)
 for es in same.values():
  es.sort(key=lambda e:e['start'])
  assert all(old['start']+old['duration']<=new['start']-.0038 for old,new in zip(es,es[1:]))
 assert spec['notated_quarters']==146 and spec['bars']==73
 assert max(e['start']+e['duration'] for e in spec['events'])>=spec['notated_music_end']-.02
 assert spec['cc_events'][-1]['time']>spec['notated_music_end']
 assert spec['cc_events'][-1]['value']==0
 sections=[]
 for section in spec['source_sections']:
  start=section['start_seconds'];end=section['end_seconds'];part=x[round(start*sr):round(end*sr)]
  sections.append({'editorial_section_label':section['label'],'start':start,'end':end,
   'rms_dbfs':float(20*np.log10(max(np.sqrt(np.mean(part.astype(float)**2)),1e-20))),
   'peak_dbfs':float(20*np.log10(max(np.max(np.abs(part)),1e-20)))})
 result={'full_wav_read':'passed','midi_reimport_all_attacks_and_controls':'passed',
  'midi_final_damper':damper,'no_hanging_notes':True,'no_physical_key_overlap':True,
  'source_note_anchors':len(anchors),'preserved_written_graces':6,
  'written_turns':len(ornaments['turns']),'written_turn_derived_attacks':len(turnnotes),
  'rendered_note_events':notes,'frames':len(x),'sample_rate':sr,'channels':2,
  'duration':len(x)/sr,'clipped_samples':clipped,
  'sample_peak_dbfs':float(20*np.log10(np.max(np.abs(x)))),'final_100ms_peak':tail_peak,
  'dc_offset':x.astype(float).mean(axis=0).tolist(),'score_sections_for_signal_check_only':sections,
  'subjective_audition':False,'technical_limit':'Signal and notation measurements do not establish perceived musical quality.'}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
