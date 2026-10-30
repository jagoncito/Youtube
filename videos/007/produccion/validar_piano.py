from pathlib import Path
import ctypes as C,json,math,time,sys,argparse
import numpy as np
from scipy.io import wavfile

p=argparse.ArgumentParser();p.add_argument('--library',required=True,type=Path);p.add_argument('--sfz',required=True,type=Path);p.add_argument('--out-dir',required=True,type=Path);args=p.parse_args()
LIB=args.library;SFZ=args.sfz;ROOT=args.out_dir;ROOT.mkdir(parents=True,exist_ok=True)
sr=48000;frames=sr*14;block=1024
L=C.CDLL(LIB);P=C.c_void_p;I=C.c_int;F=C.c_float
for name,restype,args in [('create_synth',P,[]),('free',None,[P]),('load_file',C.c_bool,[P,C.c_char_p]),('set_sample_rate',None,[P,F]),('set_samples_per_block',None,[P,I]),('set_num_voices',None,[P,I]),('enable_freewheeling',None,[P]),('set_sample_quality',None,[P,I,I]),('send_note_on',None,[P,I,I,I]),('send_note_off',None,[P,I,I,I]),('send_cc',None,[P,I,I,I]),('render_block',None,[P,C.POINTER(C.POINTER(F)),I,I]),('get_num_regions',I,[P]),('get_num_preloaded_samples',C.c_size_t,[P])]:
 f=getattr(L,'sfizz_'+name);f.restype=restype;f.argtypes=args
s=L.sfizz_create_synth();L.sfizz_set_sample_rate(s,sr);L.sfizz_set_samples_per_block(s,block);L.sfizz_set_num_voices(s,512);L.sfizz_enable_freewheeling(s);L.sfizz_set_sample_quality(s,1,8)
assert L.sfizz_load_file(s,str(SFZ).encode())
notes=[60,64,67]
events=[(0,0,'on',13,1),(.02,0,'off',13,0),(0,0,'cc',7,100),(0,0,'cc',10,64),(.3,0,'cc',64,127),(5.,0,'cc',64,0)]
for n in notes:events += [(.5,1,'on',n,70),(1.5,0,'off',n,64),(6.5,1,'on',n,70),(7.5,0,'off',n,64)]
# A later high chord confirms all other dynamic layers also load.
for n in [72,76,79]:events += [(10.,1,'on',n,105),(11.,0,'off',n,64)]
events.sort();events=[(round(t*sr),priority,kind,a,b) for t,priority,kind,a,b in events]
audio=np.zeros((frames,2),np.float32);left=np.zeros(block,np.float32);right=np.zeros(block,np.float32)
ptrs=(C.POINTER(F)*2)(left.ctypes.data_as(C.POINTER(F)),right.ctypes.data_as(C.POINTER(F)));idx=0
for begin in range(0,frames,block):
 count=min(block,frames-begin)
 while idx<len(events) and events[idx][0]<begin+count:
  at,_,kind,p1,p2=events[idx];getattr(L,'sfizz_send_'+{'on':'note_on','off':'note_off','cc':'cc'}[kind])(s,max(0,at-begin),p1,p2);idx+=1
 L.sfizz_render_block(s,ptrs,2,count);audio[begin:begin+count,0]=left[:count];audio[begin:begin+count,1]=right[:count]
report={'library':'Salamander Grand Piano v3 / Yamaha C5','sample_rate':sr,'loaded_regions':L.sfizz_get_num_regions(s),'loaded_sample_files':L.sfizz_get_num_preloaded_samples(s),'peak':float(abs(audio).max()),'rms':float(np.sqrt(np.mean(audio.astype(float)**2))),'finite':bool(np.isfinite(audio).all()),'subjective_listening':False}
def rms(a,b):return float(np.sqrt(np.mean(audio[round(a*sr):round(b*sr)].astype(float)**2)))
report.update(sustain_tail_rms=rms(2.5,3.5),damped_tail_rms=rms(8.5,9.5),left_rms=float(np.sqrt(np.mean(audio[:,0].astype(float)**2))),right_rms=float(np.sqrt(np.mean(audio[:,1].astype(float)**2))))
report['sustain_tail_advantage_db']=20*math.log10(report['sustain_tail_rms']/report['damped_tail_rms'])
L.sfizz_free(s);wavfile.write(ROOT/'piano-capability-test.float.wav',sr,audio)
(ROOT/'piano-capability-test.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
assert report['loaded_regions']>500 and report['loaded_sample_files']>100
assert report['finite'] and report['peak']>.001
assert report['sustain_tail_advantage_db']>6
