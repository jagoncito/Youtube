#!/usr/bin/env python3
"""Conservative stereo piano mastering with an original mathematical room IR.

No finished performance recording or recorded reverb response is an input.
No compression, per-note normalization, or whole-piece tempo manipulation.
"""
from pathlib import Path
import argparse,json,math
import numpy as np
from scipy import signal
from scipy.io import wavfile
import soundfile as sf

def rms(x):return float(np.sqrt(np.mean(x.astype(np.float64)**2)))

def main():
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--performance',type=Path);a=p.parse_args()
 sr,dry=wavfile.read(a.input);assert sr==48000 and dry.ndim==2 and dry.shape[1]==2
 assert np.isfinite(dry).all()
 before_rms=[rms(dry[:,c]) for c in (0,1)]
 ratio_db=20*math.log10(before_rms[1]/before_rms[0])
 # A single whole-program correction, never changing one hand or passage alone.
 # Preserve modest natural keyboard perspective while centering the recital.
 correction_db=np.clip(ratio_db,-6.,6.)*.40
 dry[:,0]*=10**(correction_db/20)
 dry[:,1]*=10**(-correction_db/20)
 mid=dry.mean(axis=1);side=(dry[:,0]-dry[:,1])*.5*.78
 dry[:,0]=mid+side;dry[:,1]=mid-side
 dry=signal.sosfilt(signal.butter(2,20,fs=sr,btype='highpass',output='sos'),dry,axis=0).astype(np.float32)
 # Short subdued chamber, keeping the original piano's release/resonance samples.
 frames=round(sr*2.1);t=np.arange(frames)/sr;rng=np.random.default_rng(2706006)
 ir=np.zeros((frames,2),np.float32)
 for ch in (0,1):
  idx=rng.choice(np.arange(round(.058*sr),frames),size=2700,replace=False)
  ir[idx,ch]=rng.choice([-1.,1.],len(idx))*np.exp(-6.9078*t[idx]/1.40)
  ir[:,ch]=signal.sosfilt(signal.butter(2,4600,fs=sr,output='sos'),ir[:,ch])
  ir[:,ch]/=np.sqrt(np.sum(ir[:,ch]**2))
 wet=np.empty_like(dry)
 for ch in (0,1):
  wet[:,ch]=signal.oaconvolve(.92*dry[:,ch]+.08*dry[:,1-ch],ir[:,ch],mode='full')[:len(dry)]*.090
  for delay,amount in [(.021,.025),(.041,.016),(.067,.010)]:
   d=round((delay+ch*.002)*sr);wet[d:,ch]+=dry[:-d,1-ch]*amount
 mix=dry+wet
 # Oversampled peak controls a single gain; neither limiter nor compressor.
 peak=0.
 for start in range(0,len(mix),sr*15):
  part=mix[max(0,start-32):min(len(mix),start+sr*15+32)]
  peak=max(peak,float(np.max(np.abs(signal.resample_poly(part,4,1,axis=0)))))
 gain=10**(-1.8/20)/peak;mix*=gain
 spec_path=a.performance or a.input.with_name('performance.json')
 spec=json.loads(spec_path.read_text())
 last_key=max(e['start']+e['duration'] for e in spec['events'])
 last_pedal=max(e['time'] for e in spec['cc_events'] if e['cc']==64 and e['value']==0)
 anchor_end=max(last_key,last_pedal);window=round(sr*.1)
 scan=[]
 for start in range(round(anchor_end*sr),len(mix)-window+1,window):
  scan.append((start,rms(mix[start:start+window])))
 first=None
 for i,(start,level) in enumerate(scan):
  if len(scan)-i>=5 and all(v<1e-4 for _,v in scan[i:i+5]) and all(v<1e-4 for _,v in scan[i:]):
   first=start/sr;break
 if first is None:raise RuntimeError('No stable complete natural decay below -80 dBFS; extend render.')
 cut_seconds=math.ceil((first+.5+.6)*24)/24
 cut_frames=round(cut_seconds*sr)
 if cut_frames>len(mix):raise RuntimeError('Render buffer too short for measured decay and breathing pause.')
 buffer_frames=len(mix);mix=mix[:cut_frames].copy()
 last_second=rms(mix[-sr:]);tail_peak=float(np.max(np.abs(mix[-round(.2*sr):])))
 # Refuse to hide an audible tail under an arbitrary duration fade.
 if last_second>10**(-80/20) or tail_peak>10**(-75/20):
  raise RuntimeError(f'Natural tail still audible; extend render: last-second RMS={last_second}, final200ms peak={tail_peak}')
 fade=round(sr*.2);mix[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)[:,None]
 a.output.parent.mkdir(parents=True,exist_ok=True);sf.write(a.output,mix,sr,subtype='PCM_24')
 blocks=[]
 for start in range(0,len(mix),sr*10):
  blocks.append({'start':start/sr,'rms_dbfs':20*math.log10(max(rms(mix[start:start+sr*10]),1e-12))})
 corr=float(np.corrcoef(mix[::20,0],mix[::20,1])[0,1])
 report={'sample_rate':sr,'channels':2,'wav_subtype':'PCM_24','frames':len(mix),'duration':len(mix)/sr,
  'input_channel_rms':before_rms,'input_right_minus_left_db':ratio_db,
  'whole_program_balance_correction_each_side_db':float(correction_db),'stereo_side_factor':.78,
  'subsonic_highpass_hz':20,'room':'Original deterministic stereo mathematical chamber; RT60 1.40 s, diffusion gain .090 and quiet early reflections',
  'target_true_peak_dbtp':-1.8,'master_gain_db':20*math.log10(gain),'compression':False,'limiter':False,
  'tail_last_second_rms_before_final_sub_audible_fade':last_second,
  'tail_last_second_dbfs':20*math.log10(max(last_second,1e-20)),
  'tail_final_200ms_peak_before_fade':tail_peak,'final_fade_seconds':.2,'input_buffer_duration_seconds':buffer_frames/sr,
  'last_key_off_seconds':last_key,'last_pedal_off_seconds':last_pedal,
  'first_stable_below_minus80dbfs_seconds':first,'stable_confirmation_seconds':.5,
  'breath_after_confirmation_seconds':.6,'only_post_music_quiet_buffer_trimmed_seconds':(buffer_frames-len(mix))/sr,
  'final_channel_rms':[rms(mix[:,c]) for c in (0,1)],'stereo_correlation':corr,
  'ten_second_rms_dbfs':blocks,'subjective_listening_performed':False,
  'note':'Only a whole-program stereo correction and master gain; pianist voicing resides in note velocities. No tempo changes.'}
 a.output.with_suffix('.mastering.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='ten_second_rms_dbfs'},indent=2))

if __name__=='__main__':main()
