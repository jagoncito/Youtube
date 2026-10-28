#!/usr/bin/env python3
"""Full PCM/MIDI checks; technical measurements are not a subjective audition."""
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
 assert info.subtype=='PCM_24' and sr==48000 and x.ndim==2 and x.shape[1]==2
 assert abs(len(x)/sr-spec['duration'])<1/sr
 assert np.isfinite(x).all() and np.max(np.abs(x))<.84
 clipped=int(np.count_nonzero(np.abs(x)>=.99999));assert not clipped
 tail=x[-round(sr*.1):];tail_peak=float(np.max(np.abs(tail)));assert tail_peak<1e-5
 anchors={e['source_id']:e for e in spec['events']}
 assert len(anchors)==len(source)==1494
 assert all(anchors[n['id']]['pitch']==n['pitch'] for n in source)
 mid=mido.MidiFile(a.midi);active=collections.Counter();notes=0;damper=0
 for tr in mid.tracks:
  for e in tr:
   if e.type=='note_on' and e.velocity:active[e.note]+=1;notes+=1
   elif e.type=='note_off' or e.type=='note_on' and not e.velocity:
    assert active[e.note]>0;active[e.note]-=1
   elif e.type=='control_change' and e.control==64:damper=e.value
 assert not any(active.values()) and damper==0
 assert notes==len(spec['events'])==1494 and abs(mid.length-spec['duration'])<.0011
 q=np.linspace(0,324,324*2048+1);points=spec['tempo_points_bpm']
 bpm=np.interp(q,[p[0] for p in points],[p[1] for p in points])
 bpm*=1+.006*np.sin(2*np.pi*q/18)+.003*np.sin(2*np.pi*q/4.5)
 t=np.zeros_like(q);t[1:]=np.cumsum((60/bpm[:-1]+60/bpm[1:])*.5*np.diff(q))
 at=lambda v:float(np.interp(v,q,t))
 sections=[]
 for label,lo,hi in [('Andante tres expressif',0,63),('Tempo rubato',63,117),
   ('Un poco mosso',117,162),('En animant',162,189),('Calmato',189,225),
   ('A Tempo I',225,292.5),('Morendo',292.5,324)]:
  start=spec['music_start']+at(lo);end=spec['music_start']+at(hi)
  part=x[round(start*sr):round(end*sr)]
  sections.append({'source_text':label,'start':start,'end':end,
   'rms_dbfs':float(20*np.log10(max(np.sqrt(np.mean(part.astype(float)**2)),1e-20))),
   'peak_dbfs':float(20*np.log10(max(np.max(np.abs(part)),1e-20)))})
 result={'full_wav_read':'passed','midi_reimport_note_pairing':'passed','midi_final_damper':damper,
  'source_note_anchors':len(anchors),'rendered_note_events':notes,'frames':len(x),
  'sample_rate':sr,'channels':2,'duration':len(x)/sr,'clipped_samples':clipped,
  'sample_peak_dbfs':float(20*np.log10(np.max(np.abs(x)))),'final_100ms_peak':tail_peak,
  'dc_offset':x.astype(float).mean(axis=0).tolist(),'score_sections_for_signal_check_only':sections,
  'subjective_audition':False}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
