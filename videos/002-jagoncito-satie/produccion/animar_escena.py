#!/usr/bin/env python3
"""Render a 12-second periodic scene: rain, firelight and subtle kitten breathing.

The artwork is generated separately. This program creates video effects only;
no animation of walking or speaking is claimed. Requires FFmpeg/libass/libx264.
"""
from pathlib import Path
import argparse, random, subprocess, os, tempfile, math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PERIOD = 12
FPS = 24

def timestamp(t):
    n = round(t*100)
    return f'{n//360000}:{n//6000%60:02d}:{n//100%60:02d}.{n%100:02d}'

def rain_ass(duration=24):
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Rain,DejaVu Sans,12,&H00F0D8B8,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    rng = random.Random(20261015)
    # Rectangles strictly inside individual glass panes, away from dragon/cat.
    panes = [(700,170,795,565),(833,110,1019,543),
             (1055,55,1240,475),(1291,45,1484,390),
             (1529,70,1715,350),(1767,150,1907,368)]
    events = []
    for xl, yt, xr, yb in panes:
        for _ in range(5):
            x = rng.uniform(xl+8,xr-8)
            period = rng.choice([4,6,12])
            phase = rng.uniform(0,period)
            length = rng.uniform(9,18)
            y0,y1 = yt-25,yb+25
            alpha = rng.choice(['BD','C5','CF'])
            for cycle in range(-1,math.ceil(duration/period)+1):
                begin = cycle*period-phase
                end = begin+period
                a,b = max(0,begin),min(duration,end)
                if b<=a:
                    continue
                ya = y0+(y1-y0)*(a-begin)/period
                yb_end = y0+(y1-y0)*(b-begin)/period
                tag=(f'{{\\an7\\p1\\bord0\\shad0\\1a&H{alpha}&'
                     f'\\clip({xl},{yt},{xr},{yb})'
                     f'\\move({x:.2f},{ya:.2f},{x:.2f},{yb_end:.2f})}}')
                drawing=f'm 0 0 l 1.1 0 1.1 {length:.2f} 0 {length:.2f}'
                events.append(f'Dialogue: 0,{timestamp(a)},{timestamp(b)},Rain,,0,0,0,,{tag}{drawing}')
    return header+'\n'.join(events)+'\n'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    ass=HERE/'lluvia.ass'
    ass.write_text(rain_ass())
    # All frequencies divide 12 s. Rain events use matching circular phases.
    filters=(
      '[0:v]scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,'
      'crop=1920:1080,setsar=1,format=yuv420p,split=3[bg][cat0][fire0];'
      '[cat0]crop=400:200:950:650[cat];'
      'color=c=0x808080:s=400x200:r=24:d=24,format=gray,geq=lum=128[xmap];'
      "color=c=0x808080:s=400x200:r=24:d=24,format=gray,"
      "geq=lum='floor(128+2.2*sin(2*PI*T/6)*exp(-pow((X-130)/115,2)-pow((Y-90)/60,2))+0.5)'[ymap];"
      "[cat][xmap][ymap]displace=edge=smear,tmix=frames=3:weights='1 2 1'[breath];"
      '[bg][breath]overlay=950:650[room];'
      "[fire0]crop=170:410:0:330,eq=brightness='0.012*cos(2*PI*t/3)+0.006*cos(2*PI*t/1.2)':eval=frame,"
      "format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':"
      "a='255*exp(-pow((X-5)/140,4)-pow((Y-200)/170,4))'[fire];"
      '[room][fire]overlay=0:330[lit];'
      f"[lit]ass=filename='{ass.as_posix()}',format=yuv420p[out]"
    )
    # The wrap is checked against the normal changes between adjacent frames.
    cmd=['ffmpeg','-hide_banner','-loglevel','warning','-nostdin','-y',
         '-filter_complex_threads','2','-loop','1','-framerate',str(FPS),
         '-i',str(ROOT/'imagen.png'),'-filter_complex',filters,
         '-map','[out]','-an','-t',str(PERIOD*2),
         '-c:v','libx264','-threads','3','-preset','fast','-crf','10',
         '-g',str(PERIOD*FPS),'-keyint_min',str(PERIOD*FPS),
         '-sc_threshold','0','-flags','+cgop','-pix_fmt','yuv420p',
         '-movflags','+faststart',str(args.output)]
    cache=Path(tempfile.gettempdir())/'jagoncito-font-cache'
    cache.mkdir(exist_ok=True)
    # Warm the encoder for one full cycle; retain the second closed GOP.
    with tempfile.TemporaryDirectory(prefix='jagoncito-scene-') as td:
        warm=Path(td)/'warmup24.mp4'
        cmd[-1]=str(warm)
        subprocess.run(cmd,check=True,env=dict(os.environ,XDG_CACHE_HOME=str(cache)))
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','warning','-nostdin','-y',
                        '-ss',str(PERIOD),'-i',str(warm),'-t',str(PERIOD),
                        '-map','0:v:0','-c','copy','-movflags','+faststart',str(args.output)],check=True)
    print(args.output)

if __name__=='__main__':
    main()
