#!/usr/bin/env python3
"""Render a new note/CC performance through the original Salamander SFZ.

All parts share one piano and one damper state. No external performance audio,
per-note expression CC, shortened violin envelopes, or invented sample loops.
Output is an unmastered stereo float WAV. SFZ samples remain separately licensed.
"""
from pathlib import Path
import argparse,ctypes as C,json,time
import numpy as np
from scipy.io import wavfile

class PianoEngine:
 def __init__(self,library):
  self.lib=C.CDLL(str(library));P=C.c_void_p;I=C.c_int;F=C.c_float
  bindings=[('create_synth',P,[]),('free',None,[P]),('load_file',C.c_bool,[P,C.c_char_p]),('set_sample_rate',None,[P,F]),('set_samples_per_block',None,[P,I]),('set_num_voices',None,[P,I]),('enable_freewheeling',None,[P]),('set_sample_quality',None,[P,I,I]),('send_note_on',None,[P,I,I,I]),('send_note_off',None,[P,I,I,I]),('send_cc',None,[P,I,I,I]),('render_block',None,[P,C.POINTER(C.POINTER(F)),I,I]),('get_num_regions',I,[P]),('get_num_preloaded_samples',C.c_size_t,[P])]
  for name,restype,args in bindings:
   f=getattr(self.lib,'sfizz_'+name);f.restype=restype;f.argtypes=args;setattr(self,name,f)

 def render(self,sfz,spec,block=1024):
  sr=int(spec.get('sample_rate',48000));frames=round(float(spec['duration'])*sr)
  events=spec['events'];cc=spec.get('cc_events',[])
  L=self;s=L.create_synth()
  try:
   L.set_sample_rate(s,sr);L.set_samples_per_block(s,block);L.set_num_voices(s,512);L.enable_freewheeling(s);L.set_sample_quality(s,1,8)
   if not L.load_file(s,str(sfz).encode()):raise RuntimeError(f'Unable to load piano: {sfz}')
   regions=L.get_num_regions(s);samples=L.get_num_preloaded_samples(s)
   if regions<500 or samples<400:raise RuntimeError(f'Incomplete piano: {regions} regions and {samples} samples')
   # Select the original retuned mapping (Markus Fiedler) before musical notes.
   # Below A0 (21), this keyswitch itself produces no piano tone.
   scheduled=[(0,0,'cc',7,100),(0,0,'cc',10,64),(0,0,'cc',64,0),(0,1,'on',13,1),(round(.015*sr),0,'off',13,0)]
   # Explicit modest physical noises. Keep string-release resonance available;
   # reduce pedal/key noises to avoid foreground mechanical clicks.
   for number,value in [(20,48),(21,22),(22,20),(72,64),(98,0),(99,93)]:
    scheduled.append((0,0,'cc',number,value))
   for e in cc:
    if int(e['cc'])==11:raise ValueError('Use note velocity, not shared CC11 for individual piano voices')
    scheduled.append((round(float(e['time'])*sr),0,'cc',int(e['cc']),int(e['value'])))
   for e in events:
    start=round(float(e['start'])*sr);end=round((float(e['start'])+float(e['duration']))*sr)
    pitch=int(e['pitch']);velocity=int(e['velocity'])
    if not(21<=pitch<=108 and 1<=velocity<=127 and 0<=start<end<frames):raise ValueError(e)
    scheduled.append((start,2,'on',pitch,velocity));scheduled.append((end,1,'off',pitch,64))
   scheduled.sort();audio=np.zeros((frames,2),np.float32);left=np.zeros(block,np.float32);right=np.zeros(block,np.float32)
   ptrs=(C.POINTER(C.c_float)*2)(left.ctypes.data_as(C.POINTER(C.c_float)),right.ctypes.data_as(C.POINTER(C.c_float)));idx=0
   for begin in range(0,frames,block):
    count=min(block,frames-begin)
    while idx<len(scheduled) and scheduled[idx][0]<begin+count:
     at,_,kind,p1,p2=scheduled[idx];getattr(L,{'on':'send_note_on','off':'send_note_off','cc':'send_cc'}[kind])(s,max(0,at-begin),p1,p2);idx+=1
    L.render_block(s,ptrs,2,count);audio[begin:begin+count,0]=left[:count];audio[begin:begin+count,1]=right[:count]
   if not np.isfinite(audio).all():raise ValueError('Nonfinite piano audio')
   report={'engine':'sfizz','regions':regions,'sample_files':samples,'sample_rate':sr,'channels':2,'frames':frames,'duration':frames/sr,'musical_note_events':len(events),'cc_events':len(cc),'tuning':'Original Retuned selection, Markus Fiedler, MIDI keyswitch 13','shared_piano_instance':True,'velocity_layers':16,'sustain_cc':64,'max_voices':512,'resampling_quality_parameter':8,'sfz_envelopes_modified':False,'artificial_sustain_loops':False,'cc_initial_controls':{'string_release_resonance_20':48,'hammer_release_noise_21':22,'pedal_noise_22':20,'release_72':64,'start_offset_98':0,'velocity_response_99':93},'peak':float(np.max(np.abs(audio))),'rms':float(np.sqrt(np.mean(audio.astype(np.float64)**2))),'left_rms':float(np.sqrt(np.mean(audio[:,0].astype(np.float64)**2))),'right_rms':float(np.sqrt(np.mean(audio[:,1].astype(np.float64)**2))),'subjective_listening':False}
   return audio,report
  finally:L.free(s)

def main():
 p=argparse.ArgumentParser();p.add_argument('--events',type=Path,required=True);p.add_argument('--sfz',type=Path,required=True);p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 t=time.monotonic();spec=json.loads(a.events.read_text());audio,report=PianoEngine(a.library).render(a.sfz,spec)
 a.output.parent.mkdir(parents=True,exist_ok=True);wavfile.write(a.output,report['sample_rate'],audio)
 report['render_seconds']=time.monotonic()-t
 a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
