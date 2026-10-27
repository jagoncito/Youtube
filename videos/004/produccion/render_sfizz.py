#!/usr/bin/env python3
"""Render expressive timestamped note JSON through the open-source sfizz engine.

Only note/timing data and isolated CC0 instrument samples are used, never an
existing performance recording. Assumes JSON events are seconds and MIDI pitches.
Outputs unmastered float32 stereo stems plus their conservative chamber mix.
"""
import argparse, ctypes as C, json, math, re, time
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import soundfile as sf

MAPPINGS={
 ('solo','sustain'):'SViolinVib.sfz',('solo','spiccato'):'SViolinSpic.sfz',
 ('violin1','sustain'):'ViolinEnsSusVib.sfz',('violin1','spiccato'):'ViolinEnsSpic.sfz',('violin1','pizzicato'):'ViolinEnsPizz.sfz',
 ('violin2','sustain'):'ViolinEnsSusVib.sfz',('violin2','spiccato'):'ViolinEnsSpic.sfz',('violin2','pizzicato'):'ViolinEnsPizz.sfz',
 ('viola','sustain'):'ViolaEnsSusVib.sfz',('viola','spiccato'):'ViolaEnsSpic.sfz',('viola','pizzicato'):'ViolaEnsPizz.sfz',
 ('cello','sustain'):'CelloEnsSusVib.sfz',('cello','spiccato'):'CelloEnsSpic.sfz',('cello','pizzicato'):'CelloEnsPizz.sfz',
 ('bass','sustain'):'ContrabassSusNV.sfz',('bass','spiccato'):'ContrabassSpic.sfz',
 ('continuo','sustain'):'OrganQuiet.sfz'
}
DEFAULT_MIX={
 'solo':{'gain_db':0.,'pan':-.12,'width':.65},
 'violin1':{'gain_db':-10.,'pan':-.35,'width':.65},
 'violin2':{'gain_db':-12.,'pan':.25,'width':.65},
 'viola':{'gain_db':-12.,'pan':.12,'width':.6},
 'cello':{'gain_db':-10.,'pan':.32,'width':.55},
 'bass':{'gain_db':-14.,'pan':.2,'width':.4},
 'continuo':{'gain_db':-21.,'pan':0.,'width':.55}
}

def sustain_loops(path,text,events):
 # Original recordings have finite bows and no loop metadata. Only regions that
 # need a genuinely long held note receive a crossfaded loop in the steady bow.
 default=re.search(r'default_path=([^\r\n]+)',text).group(1).strip()
 chunks=text.split('<region>'); adjusted=[]
 for i,region in enumerate(chunks[1:],start=1):
  def number(op,default_value):
   m=re.search(r'(?m)^'+op+r'=([^\s]+)',region)
   return float(m.group(1)) if m else default_value
  sample=re.search(r'(?m)^sample=([^\r\n]+)',region).group(1).strip()
  info=sf.info(path.parent/default/sample)
  lo,hi=number('lokey',0),number('hikey',127)
  lv,hv=number('lovel',0),number('hivel',127)
  center,tune=number('pitch_keycenter',60),number('tune',0)
  matching=[e for e in events if lo<=e['pitch']<=hi and lv<=e['velocity']<=hv]
  needing=[e for e in matching if e['duration']+.35 > info.duration*.65/2**((e['pitch']-center+tune/100)/12)]
  if needing:
   end=min(5.5,info.duration*.60);start=max(1.,end-2.)
   if end-start<.5:raise ValueError('Sustain recording too short')
   chunks[i]+=f'\nloop_mode=loop_sustain\nloop_start={round(start*info.samplerate)}\nloop_end={round(end*info.samplerate)}\nloop_crossfade=0.12\n'
   adjusted.append(dict(sample=sample,longest_note_seconds=max(e['duration'] for e in needing),loop_start_seconds=start,loop_end_seconds=end,crossfade_seconds=.12))
 return '<region>'.join(chunks),adjusted

class Sfizz:
 def __init__(self,lib):
  self.lib=C.CDLL(str(lib)); L=self.lib
  def bind(name,restype,args):
   f=getattr(L,name);f.restype=restype;f.argtypes=args;setattr(self,name.removeprefix('sfizz_'),f)
  P=C.c_void_p;I=C.c_int;F=C.c_float
  bind('sfizz_create_synth',P,[]);bind('sfizz_free',None,[P]);bind('sfizz_load_string',C.c_bool,[P,C.c_char_p,C.c_char_p])
  bind('sfizz_set_sample_rate',None,[P,F]);bind('sfizz_set_samples_per_block',None,[P,I])
  bind('sfizz_enable_freewheeling',None,[P]);bind('sfizz_set_sample_quality',None,[P,I,I]);bind('sfizz_set_num_voices',None,[P,I])
  bind('sfizz_send_note_on',None,[P,I,I,I]);bind('sfizz_send_note_off',None,[P,I,I,I]);bind('sfizz_send_cc',None,[P,I,I,I])
  bind('sfizz_render_block',None,[P,C.POINTER(C.POINTER(F)),I,I]);bind('sfizz_get_num_regions',I,[P]);bind('sfizz_get_num_preloaded_samples',C.c_size_t,[P])

 def render(self,path,events,cc_events,sr,frames,part,artic,block=1024):
  L=self;s=L.create_synth();audio=np.zeros((frames,2),np.float32)
  try:
   L.set_sample_rate(s,sr);L.set_samples_per_block(s,block);L.set_num_voices(s,128);L.enable_freewheeling(s);L.set_sample_quality(s,1,8)
   text=path.read_text().replace('\\','/')
   loops=[]
   if artic=='sustain':text,loops=sustain_loops(path,text,events)
   # The original files keep very long release envelopes (up to four seconds).
   # Tighten releases for clear baroque separation without clipping sample tails.
   release=.15 if artic=='spiccato' else (.25 if artic=='pizzicato' else (.22 if part=='solo' else .32))
   attack=.001 if artic in ('spiccato','pizzicato') else (.006 if part=='solo' else .009)
   text=re.sub(r'ampeg_release=[^\s]+',f'ampeg_release={release}',text)
   text=re.sub(r'ampeg_attack=[^\s]+',f'ampeg_attack={attack}',text)
   if not L.load_string(s,str(path).encode(),text.encode()):raise RuntimeError(f'Unable to load {path}')
   regions=L.get_num_regions(s);samples=L.get_num_preloaded_samples(s)
   if not regions or not samples:raise RuntimeError(f'Empty instrument {path}: {regions} regions {samples} samples')
   scheduled=[(0,0,'cc',7,100),(0,0,'cc',10,64),(0,0,'cc',11,100)]
   for e in cc_events:
    scheduled.append((round(float(e['time'])*sr),0,'cc',int(e['cc']),int(e['value'])))
   has_expression=any(e['cc']==11 for e in cc_events)
   for e in events:
    start=round(float(e['start'])*sr);end=round((float(e['start'])+float(e['duration']))*sr)
    pitch=int(e['pitch']);velocity=int(round(float(e['velocity'])))
    if not (0<=pitch<=127 and 1<=velocity<=127 and end>start):raise ValueError(e)
    if not has_expression and 'expression' in e:scheduled.append((start,0,'cc',11,max(0,min(127,round(float(e['expression'])*127)))))
    scheduled.append((start,2,'on',pitch,velocity));scheduled.append((end,1,'off',pitch,64))
   scheduled.sort();left=np.zeros(block,np.float32);right=np.zeros(block,np.float32)
   ptrs=(C.POINTER(C.c_float)*2)(left.ctypes.data_as(C.POINTER(C.c_float)),right.ctypes.data_as(C.POINTER(C.c_float)))
   idx=0
   # Skip initial silence efficiently, but still render the complete timeline.
   for begin in range(0,frames,block):
    count=min(block,frames-begin)
    while idx<len(scheduled) and scheduled[idx][0]<begin+count:
     frame,_,kind,p1,p2=scheduled[idx];delay=max(0,frame-begin)
     if kind=='cc':L.send_cc(s,delay,p1,p2)
     elif kind=='on':L.send_note_on(s,delay,p1,p2)
     else:L.send_note_off(s,delay,p1,p2)
     idx+=1
    L.render_block(s,ptrs,2,count)
    audio[begin:begin+count,0]=left[:count];audio[begin:begin+count,1]=right[:count]
   if not np.isfinite(audio).all():raise ValueError('Nonfinite sample in render')
   return audio,dict(instrument=path.name,regions=regions,preloaded_samples=samples,peak=float(np.max(np.abs(audio))),rms=float(np.sqrt(np.mean(audio.astype(np.float64)**2))),release_seconds=release,attack_seconds=attack,crossfaded_sustain_regions=loops)
  finally:L.free(s)


def main():
 p=argparse.ArgumentParser();p.add_argument('--events',type=Path,required=True);p.add_argument('--samples',type=Path,required=True);p.add_argument('--library',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--only',default='');p.add_argument('--preview-seconds',type=float);a=p.parse_args()
 spec=json.loads(a.events.read_text());sr=int(spec.get('sample_rate',44100));events=spec['events'];cc=spec.get('cc_events',[])
 if a.only:events=[e for e in events if e['part'] in a.only.split(',')]
 end=max(e['start']+e['duration'] for e in events)+3.
 end=float(spec.get('duration',end))
 if a.preview_seconds:end=min(end,a.preview_seconds);events=[e for e in events if e['start']<end]
 frames=round(end*sr);a.out.mkdir(parents=True,exist_ok=True)
 engine=Sfizz(a.library);mix=np.zeros((frames,2),np.float32);stats=[]
 groups=sorted({(e['part'],e.get('articulation','sustain')) for e in events})
 for part,artic in groups:
  t=time.monotonic();subset=[e for e in events if e['part']==part and e.get('articulation','sustain')==artic]
  mapping=MAPPINGS.get((part,artic))
  if mapping is None:raise ValueError(f'Unsupported part/articulation {(part,artic)}')
  notecc=[e for e in cc if e['part']==part and e['time']<end]
  audio,st=engine.render(a.samples/mapping,subset,notecc,sr,frames,part,artic)
  config={**DEFAULT_MIX[part],**spec.get('mix',{}).get(part,{})};g=10**(float(config['gain_db'])/20);pan=float(config['pan']);width=float(config.get('width',.65))
  # Narrow the recorded stereo field before placing the section in the ensemble.
  mid=audio.mean(axis=1);side=(audio[:,0]-audio[:,1])*.5*width
  audio[:,0]=(mid+side)*math.sqrt(1-pan)*g;audio[:,1]=(mid-side)*math.sqrt(1+pan)*g
  mix+=audio
  wavfile.write(a.out/f'{part}-{artic}.float.wav',sr,audio)
  st.update(part=part,articulation=artic,events=len(subset),mix=config,seconds=time.monotonic()-t)
  stats.append(st);print(json.dumps(st),flush=True)
 wavfile.write(a.out/'mix-dry.float.wav',sr,mix)
 metadata={'duration':frames/sr,'sample_rate':sr,'channels':2,'format':'IEEE_FLOAT_32','stems':stats,'peak':float(np.max(np.abs(mix))),'rms':float(np.sqrt(np.mean(mix.astype(np.float64)**2))),'subjective_listening':False,'engine':'sfizz','resampling_quality_parameter':8,'resampling_mode':'offline sinc','note':'Original SFZ sample tuning and keymaps preserved; release and attack envelopes adjusted for articulation.'}
 (a.out/'render-report.json').write_text(json.dumps(metadata,indent=2));print('DONE',json.dumps(metadata),flush=True)
if __name__=='__main__':main()
