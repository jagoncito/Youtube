#!/usr/bin/env python3
"""Create the 6-minute loop and 30-minute film without re-encoding the picture.

Only the 12-second periodic animation is encoded. Complete piano works are
preserved; the 30-minute soundtrack is encoded continuously from five WAV loops.
"""
from pathlib import Path
import json, subprocess, tempfile, sys, argparse
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent

def run(cmd):
    subprocess.run(cmd,check=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scene-template',type=Path)
    args=parser.parse_args()
    audio=ROOT/'audio-bucle-6min.wav'
    with tempfile.TemporaryDirectory(prefix='jagoncito-video-') as td:
        template=args.scene_template or Path(td)/'escena-12s.mp4'
        if args.scene_template is None:
            run([sys.executable,str(HERE/'animar_escena.py'),'--output',str(template)])
        for seconds,video_loops,audio_loops,name in [
            (360,29,0,'bucle-6min.mp4'),
            (1800,149,4,'video-30min.mp4')]:
            cmd=['ffmpeg','-hide_banner','-loglevel','warning','-nostdin','-y',
                 '-stream_loop',str(video_loops),'-i',str(template),
                 '-stream_loop',str(audio_loops),'-i',str(audio),
                 '-map','0:v:0','-map','1:a:0','-c:v','copy',
                 '-c:a','aac','-b:a','192k','-ar','44100','-t',str(seconds),
                 '-video_track_timescale','24000',
                 '-metadata','artist=Jagoncito',
                 '-metadata','title=A Rainy Night with Jagoncito | Satie Gymnopédies',
                 '-metadata','comment=New digital piano performances; subtle periodic scene animation.']
            if seconds==1800:
                cmd += ['-af','afade=t=out:st=1797:d=3']
            cmd += ['-movflags','+faststart',str(ROOT/name)]
            run(cmd)
            print(name,flush=True)

if __name__=='__main__':
    main()
