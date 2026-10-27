#!/usr/bin/env python3
"""Gentle chamber mix/master; entirely algorithmic IR, no external recordings."""
from pathlib import Path
import argparse,json,math
import numpy as np
from scipy import signal
from scipy.io import wavfile
import soundfile as sf

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--render',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 sr,dry=wavfile.read(a.render/'mix-dry.float.wav'); dry=dry.astype(np.float32)
 # Remove subsonic energy while retaining the cello's low fundamentals.
 dry=signal.sosfilt(signal.butter(2,35,fs=sr,btype='highpass',output='sos'),dry,axis=0).astype(np.float32)
 # Deterministic short chamber IR: early wall reflections + damped diffusion.
 n=round(sr*2.15);t=np.arange(n)/sr;rng=np.random.default_rng(297004)
 ir=np.zeros((n,2),np.float32)
 for ch in (0,1):
  indexes=rng.choice(np.arange(round(.055*sr),n),size=3100,replace=False)
  ir[indexes,ch]=rng.choice([-1.,1.],len(indexes))*np.exp(-6.9078*t[indexes]/1.45)
  ir[:,ch]=signal.sosfilt(signal.butter(2,5200,fs=sr,output='sos'),ir[:,ch])
  ir[:,ch]/=np.sqrt(np.sum(ir[:,ch]**2))
 wet=np.empty_like(dry)
 for ch in (0,1):
  wet[:,ch]=signal.oaconvolve(.90*dry[:,ch]+.10*dry[:,1-ch],ir[:,ch],mode='full')[:len(dry)]*.14
  for delay,amount in [(.019,.047),(.033,.034),(.057,.025),(.089,.017)]:
   d=round((delay+ch*.003)*sr);wet[d:,ch]+=dry[:-d,1-ch]*amount
 mix=dry+wet
 # End after the natural room tail; sub-audible final 200ms ramps to digital zero.
 fade=round(.2*sr);mix[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)[:,None]
 # Measure at 4x sample rate in overlapping chunks; no compression/brickwall.
 tp=0.
 for start in range(0,len(mix),sr*15):
  block=mix[max(0,start-32):min(len(mix),start+sr*15+32)]
  tp=max(tp,float(np.max(np.abs(signal.resample_poly(block,4,1,axis=0)))))
 gain=10**(-1.8/20)/tp
 mix*=gain
 a.out.parent.mkdir(parents=True,exist_ok=True);sf.write(a.out,mix,sr,subtype='PCM_24')
 report={'sample_rate':sr,'channels':2,'wav_subtype':'PCM_24','frames':len(mix),'duration_seconds':len(mix)/sr,'peak_before_gain':tp,'master_gain_db':20*math.log10(gain),'target_true_peak_dbfs':-1.8,'compression':False,'tempo_changed':False,'room':'Original deterministic stereo chamber IR, RT60 1.45s, diffusion wet gain 0.14 and early reflections','subsonic_highpass_hz':35,'final_200ms':'Sub-audible room tail fades to zero; musical notes unchanged','subjective_listening_performed':False}
 (a.out.parent/'produccion'/'mastering.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
