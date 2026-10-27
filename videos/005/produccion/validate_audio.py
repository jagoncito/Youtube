#!/usr/bin/env python3
"""Full PCM scan and exported-performance integrity checks, not an audition."""
from pathlib import Path
import argparse,collections,json
import numpy as np
import soundfile as sf
import mido

def main():
 p=argparse.ArgumentParser();p.add_argument('--audio',type=Path,required=True)
 p.add_argument('--performance',type=Path,required=True);p.add_argument('--midi',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 info=sf.info(a.audio);x,sr=sf.read(a.audio,dtype='float32')
 spec=json.loads(a.performance.read_text())
 assert info.subtype=='PCM_24' and sr==48000 and x.ndim==2 and x.shape[1]==2
 assert abs(len(x)/sr-spec['duration'])<1/sr
 assert np.isfinite(x).all() and np.max(np.abs(x))<.84
 clipped=int(np.count_nonzero(np.abs(x)>=.99999));assert not clipped
 tail=x[-round(sr*.1):];tail_peak=float(np.max(np.abs(tail)));assert tail_peak<1e-5
 anchors=collections.defaultdict(list)
 for e in spec['events']:anchors[e['source_id']].append(e)
 assert len(anchors)==1806
 mid=mido.MidiFile(a.midi);active=collections.Counter();notes=0;damper=0
 for tr in mid.tracks:
  for e in tr:
   if e.type=='note_on' and e.velocity:active[e.note]+=1;notes+=1
   elif e.type=='note_off' or e.type=='note_on' and not e.velocity:
    assert active[e.note]>0;active[e.note]-=1
   elif e.type=='control_change' and e.control==64:damper=e.value
 assert not any(active.values()) and damper==0
 assert notes==len(spec['events']) and abs(mid.length-spec['duration'])<.0011
 q=np.linspace(0,231,231*2048+1);points=spec['tempo_points_bpm']
 bpm=np.interp(q,[p[0] for p in points],[p[1] for p in points])
 bpm*=1+.009*np.sin(2*np.pi*q/12)+.004*np.sin(2*np.pi*q/3)
 t=np.zeros_like(q);t[1:]=np.cumsum(.5*(60/bpm[:-1]+60/bpm[1:])*np.diff(q))
 at=lambda v:float(np.interp(v,q,t))
 sections=[]
 for label,lo,hi in [('opening',0,27),('first development',27,75),('return',75,99),
   ('modulating section',99,135),('climax',144,183),('dolcissimo/coda',183,228),('final chord',228,231)]:
  start=spec['music_start']+at(lo);end=spec['music_start']+at(hi)
  part=x[round(start*sr):round(end*sr)]
  sections.append({'section':label,'start':start,'end':end,
   'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(part.astype(float)**2)))),
   'peak_dbfs':float(20*np.log10(np.max(np.abs(part))))})
 result={'full_wav_read':'passed','midi_reimport_note_pairing':'passed','midi_final_damper':damper,
  'source_note_anchors':len(anchors),'rendered_note_events':notes,'frames':len(x),
  'sample_rate':sr,'channels':2,'duration':len(x)/sr,'clipped_samples':clipped,
  'sample_peak_dbfs':float(20*np.log10(np.max(np.abs(x)))),'final_100ms_peak':tail_peak,
  'dc_offset':x.astype(float).mean(axis=0).tolist(),'sections':sections,'subjective_audition':False}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
