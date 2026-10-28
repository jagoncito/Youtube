#!/usr/bin/env python3
"""Mux one complete Clair de lune and N complete repetitions. No cutting/retiming."""
from pathlib import Path
from fractions import Fraction
import argparse,json,subprocess,tempfile
TITLE='Debussy: Clair de Lune | Jagoncito by the Sea'
WORK='Clair de lune (Suite bergamasque, III)'

def metadata(n,d):
 lines=[';FFMETADATA1',f'title={TITLE}','artist=Jagoncito','copyright=Score transcription: Keith OHara / Mutopia, Public Domain; digital performance and audiovisual adaptation CC BY 3.0; piano samples Alexander Holm / CC BY 3.0. See accompanying credits.','comment=New sampled-grand-piano digital realization; original moonlit coastal artwork and environmental animation.']
 for i in range(n):
  lines+=['[CHAPTER]','TIMEBASE=1/1000',f'START={round(i*d*1000)}',f'END={round((i+1)*d*1000)}',f'title={WORK}'+(f' (cycle {i+1})' if n>1 else '')]
 return '\n'.join(lines)+'\n'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--scene',type=Path,required=True);ap.add_argument('--audio',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);ap.add_argument('--repeats',type=int);a=ap.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 s=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','a:0','-show_streams','-of','json',str(a.audio)]))['streams'][0]
 d=float(int(s['duration_ts'])*Fraction(s['time_base']));sr=int(s['sample_rate']);n=a.repeats or max(2,round(1800/d));assert n>=2
 files=['debussy-clair-de-lune.mp4','debussy-clair-de-lune-extended.mp4']
 with tempfile.TemporaryDirectory(prefix='jagoncito006-mux-') as td:
  for reps,name in [(1,files[0]),(n,files[1])]:
   meta=Path(td)/f'chapters{reps}.txt';meta.write_text(metadata(reps,d));seconds=reps*d
   subprocess.run(['ffmpeg','-hide_banner','-loglevel','warning','-nostdin','-y','-stream_loop','-1','-i',str(a.scene),'-stream_loop',str(reps-1),'-i',str(a.audio),'-f','ffmetadata','-i',str(meta),'-map','0:v:0','-map','1:a:0','-map_metadata','2','-map_chapters','2','-c:v','copy','-c:a','aac','-b:a','256k','-ar',str(sr),'-t',f'{seconds:.9f}','-video_track_timescale','24000','-movflags','+faststart',str(a.output_dir/name)],check=True)
 result={'base_seconds':d,'long_seconds':d*n,'complete_work_repetitions':n,'sample_rate':sr,'standalone_wav_channels':int(s['channels']),'visual_cycle_seconds':60,'tempos_changed_to_fit_duration':False,'same_new_performance_repeated':True,'audio_crossfade':False,'join':'Complete release and room tail from the source WAV preserved, followed by its lead-in; no overlap/cut of musical notes.','container_note':'Stream-copied H.264 B pictures can retain up to two extra final video frames; exact audio duration checked separately.','files':files,'public_chapters':[{'start_seconds':i*d,'title':WORK+(f' — repeat {i+1}' if i else '')} for i in range(n)]}
 (a.output_dir/'montaje.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
