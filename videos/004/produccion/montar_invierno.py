#!/usr/bin/env python3
"""Mux the complete concerto and an integral-repeat long version.

No score cutting, tempo changes, or truncated final repetitions. Source WAV
already contains the preserved musical tails and a measured inter-cycle pause.
Requires FFmpeg/ffprobe. No network or schedules.
"""
from pathlib import Path
import argparse, json, subprocess, tempfile
from fractions import Fraction

def metadata(chapters,repeats,base_seconds,title):
    lines=[';FFMETADATA1',f'title={title}','artist=Jagoncito',
           'comment=New sample-based digital realization of Vivaldi RV 297; original winter artwork and environmental animation.']
    full=[]
    for cycle in range(repeats):
        for ch in chapters:
            full.append({'start':cycle*base_seconds+ch['start'],'title':ch['title']+(f' (cycle {cycle+1})' if repeats>1 else '')})
    for i,ch in enumerate(full):
        end=full[i+1]['start'] if i+1<len(full) else repeats*base_seconds
        lines+=['[CHAPTER]','TIMEBASE=1/1000',f"START={round(ch['start']*1000)}",f'END={round(end*1000)}',f"title={ch['title']}"]
    return '\n'.join(lines)+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scene',type=Path,required=True)
    ap.add_argument('--audio',type=Path,required=True);ap.add_argument('--chapters',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,required=True);ap.add_argument('--repeats',type=int)
    args=ap.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    # PCM WAV exact duration is preferable to estimating from MIDI or frame count.
    audio_info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','a:0','-show_streams','-of','json',str(args.audio)]))['streams'][0]
    duration=float(int(audio_info['duration_ts'])*Fraction(audio_info['time_base']))
    repeats=args.repeats or max(2,round(1800/duration))
    if repeats<2:raise ValueError('Long version needs at least two whole concertos.')
    chapters=json.loads(args.chapters.read_text())
    if isinstance(chapters,dict):chapters=chapters['chapters']
    if len(chapters)!=3 or chapters[0]['start']!=0:raise ValueError('Expected three real movement chapter starts, first zero.')
    title='Vivaldi’s Winter | A Snowy Refuge with Jagoncito'
    with tempfile.TemporaryDirectory(prefix='jagoncito-winter-mux-') as td:
        for n,name in [(1,'vivaldi-winter-concerto.mp4'),(repeats,'vivaldi-winter-extended.mp4')]:
            seconds=n*duration
            meta=Path(td)/f'chapters-{n}.txt';meta.write_text(metadata(chapters,n,duration,title))
            cmd=['ffmpeg','-hide_banner','-loglevel','warning','-nostdin','-y',
                 '-stream_loop','-1','-i',str(args.scene),'-stream_loop',str(n-1),'-i',str(args.audio),
                 '-f','ffmetadata','-i',str(meta),'-map','0:v:0','-map','1:a:0','-map_metadata','2','-map_chapters','2',
                 '-c:v','copy','-c:a','aac','-b:a','256k','-ar','44100','-t',f'{seconds:.9f}',
                 '-video_track_timescale','24000','-movflags','+faststart',str(args.output_dir/name)]
            subprocess.run(cmd,check=True)
    result={'base_seconds':duration,'long_seconds':duration*repeats,'complete_concerto_repetitions':repeats,
            'visual_cycle_seconds':60,'tempos_changed_to_fit_duration':False,
            'audio_crossfade':False,'join':'Musical decay and inter-cycle pause preserved from base WAV; no movement overlap.',
            'files':['vivaldi-winter-concerto.mp4','vivaldi-winter-extended.mp4']}
    (args.output_dir/'montaje.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
