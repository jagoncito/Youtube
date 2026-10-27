#!/usr/bin/env python3
"""Animate only video effects over the new Winter artwork, never retouch the still.

60-second seamless environmental cycle: snow, a local lantern-light fluctuation,
and minute stream highlights. Jagoncito and the kitten remain still.
Requires FFmpeg with libass/libx264. No network, scheduling, or old media.
"""
from pathlib import Path
import argparse, json, math, os, random, subprocess

W,H,FPS,PERIOD=1920,1080,24,60

def stamp(t):
    n=round(t*100)
    return f'{n//360000}:{n//6000%60:02d}:{n//100%60:02d}.{n%100:02d}'

def atmosphere():
    header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Snow,DejaVu Sans,12,&H00FFF5EA,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Water,DejaVu Sans,12,&H00F5E4CD,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    rng=random.Random(297004)
    events=[]
    # Clip the snowy landscape and foreground away from the sheltered characters.
    # Snow is deliberately absent from x<880,y<865: the overhang and animals.
    for layer,count,xlo,xhi,ylo,yhi in [
        ('far',56,885,1950,-20,1110),('middle',26,885,1950,-20,1110),
        ('foreground',18,-30,1950,850,1110)]:
        for i in range(count):
            x=rng.uniform(xlo,xhi)
            period=rng.choice([30,60]) if layer=='far' else rng.choice([15,20,30])
            phase=rng.uniform(0,period)
            radius=rng.uniform(.65,1.25) if layer=='far' else rng.uniform(1.2,2.2)
            if layer=='foreground': radius=rng.uniform(2.1,3.5)
            blur=.7 if layer=='far' else 1.3
            if layer=='foreground': blur=2.1
            alpha='BC' if layer=='far' else 'AB'
            dx=rng.uniform(15,45)
            clip='880,0,1920,1080' if layer!='foreground' else '0,865,1920,1080'
            for cycle in range(-1,math.ceil(PERIOD/period)+1):
                begin=cycle*period-phase
                end=begin+period
                a,b=max(0,begin),min(PERIOD,end)
                if b<=a: continue
                f0,f1=(a-begin)/period,(b-begin)/period
                xa,xb=x+dx*f0,x+dx*f1
                ya,yb=ylo+(yhi-ylo)*f0,ylo+(yhi-ylo)*f1
                # Tiny octagonal soft flakes, not rain streaks or text glyphs.
                r=radius; k=.7*r
                shape=(f'm {-k:.2f} {-r:.2f} l {k:.2f} {-r:.2f} {r:.2f} {-k:.2f} '
                       f'{r:.2f} {k:.2f} {k:.2f} {r:.2f} {-k:.2f} {r:.2f} '
                       f'{-r:.2f} {k:.2f} {-r:.2f} {-k:.2f}')
                tag=(f'{{\\an7\\p1\\bord0\\shad0\\blur{blur:.1f}\\1a&H{alpha}&'
                     f'\\clip({clip})\\move({xa:.2f},{ya:.2f},{xb:.2f},{yb:.2f})}}')
                events.append(f'Dialogue: 1,{stamp(a)},{stamp(b)},Snow,,0,0,0,,{tag}{shape}')
    # Faint short surface glints, each fading before the circular cycle resets.
    # Coordinates lie on the water beyond the refuge; no animals are moved.
    for x,y,length in [(1130,1018,28),(1375,1041,36),(1468,987,25),
                       (1310,945,22),(1510,916,20),(1450,878,14),(1348,843,12)]:
        phase=rng.uniform(0,10)
        for cycle in range(-1,7):
            begin=cycle*10-phase; end=begin+8
            a,b=max(0,begin),min(PERIOD,end)
            if b<=a:continue
            f0,f1=(a-begin)/8,(b-begin)/8
            # Keep opacity periodic even for events clipped at the render boundary.
            def al(f): return round(255-26*max(0,math.sin(math.pi*f)))
            aa,ab=al(f0),al(f1)
            keys=[(f0,aa)]+[(f,al(f)) for f in (.25,.5,.75) if f0<f<f1]+[(f1,ab)]
            transforms=''.join(f'\\t({round((keys[k-1][0]-f0)*8000)},{round((keys[k][0]-f0)*8000)},\\1a&H{keys[k][1]:02X}&)' for k in range(1,len(keys)))
            tag=(f'{{\\an7\\p1\\bord0\\shad0\\blur1.3\\1a&H{aa:02X}&'
                 f'{transforms}'
                 f'\\move({x+8*f0:.2f},{y},{x+8*f1:.2f},{y})}}')
            events.append(f'Dialogue: 0,{stamp(a)},{stamp(b)},Water,,0,0,0,,{tag}m 0 0 l {length} 0 {length-4} 1 4 1')
    return header+'\n'.join(events)+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--image',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    args=ap.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
    ass=args.output.parent/'nieve-reflejos.ass';ass.write_text(atmosphere())
    filters=(
        '[0:v]scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,'
        'crop=1920:1080,setsar=1,format=yuv420p,split=2[bg][light0];'
        "[light0]crop=500:580:30:130,eq=brightness='0.012*cos(2*PI*t/6)+0.005*cos(2*PI*t/2.5)':eval=frame,"
        "format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':"
        "a='210*exp(-pow((X-252)/145,2)-pow((Y-320)/160,2))'[light];"
        '[bg][light]overlay=30:130[lit];'
        f"[lit]ass=filename='{ass.as_posix()}',format=yuv420p[out]"
    )
    cmd=['ffmpeg','-hide_banner','-loglevel','warning','-nostdin','-y',
         '-filter_complex_threads','2','-loop','1','-framerate',str(FPS),'-i',str(args.image),
         '-filter_complex',filters,'-map','[out]','-an','-t',str(PERIOD),
         '-c:v','libx264','-threads','3','-preset','fast','-qp','1','-profile:v','high',
         '-g',str(10*FPS),'-keyint_min',str(10*FPS),'-sc_threshold','0',
         '-flags','+cgop','-pix_fmt','yuv420p','-movflags','+faststart',str(args.output)]
    cache=args.output.parent/'font-cache';cache.mkdir(exist_ok=True)
    subprocess.run(cmd,check=True,env=dict(os.environ,XDG_CACHE_HOME=str(cache)))
    (args.output.parent/'escena-config.json').write_text(json.dumps({
        'period_seconds':PERIOD,'fps':FPS,'width':W,'height':H,'effects':['soft outdoor snow','local lantern light','minute stream highlights'],
        'characters_animated':False,'snow_exclusion':'x<880 and y<865 in the 1920x1080 frame',
        'source_artwork':args.image.name,'new_effects_seed':297004},indent=2)+'\n')
    print(args.output)
if __name__=='__main__': main()
