#!/usr/bin/env python3
"""New 60s coastal environmental animation over the original 006 artwork.

Video effects only: small sea-surface displacement and a few faint water glints.
The skyline, breakwater, lantern, blanket and animals remain static. No audio.
"""
from pathlib import Path
import argparse,json,math,os,subprocess
W,H,FPS,PERIOD=1920,1080,24,60

def stamp(t):
 n=round(t*100);return f'{n//360000}:{n//6000%60:02d}:{n%6000//100:02d}.{n%100:02d}'

def water_glints():
 header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Glint,DejaVu Sans,12,&H00F6E9D5,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 events=[]
 # All points are on the open water to the right, away from characters and land.
 for x,y,length,period,phase in [(1600,363,19,15,1.7),(1730,402,24,20,5.1),
      (1570,457,29,15,8.3),(1780,514,37,20,12.8),(1710,601,42,30,18.2),
      (1835,710,32,20,8.6)]:
  for cycle in range(-1,math.ceil(PERIOD/period)+1):
   begin=cycle*period-phase;end=begin+period;a,b=max(0.,begin),min(PERIOD,end)
   if b<=a:continue
   f0,f1=(a-begin)/period,(b-begin)/period
   al=lambda f:round(255-28*math.sin(math.pi*f)**2)
   keys=[(f0,al(f0))]+[(q,al(q)) for q in (.125,.25,.375,.5,.625,.75,.875) if f0<q<f1]+[(f1,al(f1))]
   trans=''.join(f'\\t({round((keys[k-1][0]-f0)*period*1000)},{round((keys[k][0]-f0)*period*1000)},\\1a&H{keys[k][1]:02X}&)' for k in range(1,len(keys)))
   tag=(f'{{\\an7\\p1\\bord0\\shad0\\blur1.1\\1a&H{keys[0][1]:02X}&{trans}'
       f'\\move({x+7*f0:.3f},{y},{x+7*f1:.3f},{y})}}')
   shape=f'm 0 0 b {length*.3:.1f} -0.7 {length*.6:.1f} -0.7 {length} 0 l {length-2} 1 b {length*.6:.1f} 0.5 {length*.3:.1f} 0.5 2 1'
   events.append(f'Dialogue: 0,{stamp(a)},{stamp(b)},Glint,,0,0,0,,{tag}{shape}')
 return header+'\n'.join(events)+'\n'

def filters(ass):
 # Keep all motion well below the skyline. Patch A covers open sea; its alpha
 # explicitly excludes horns/wing tops. Patch B covers only right-hand surf.
 return (
 '[0:v]scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,setsar=1,format=yuv420p,split=3[bg][sea0][surf0];'
 '[sea0]crop=1400:310:500:320[sea];'
 "nullsrc=s=350x78:r=24:d=60,format=gray,geq=lum='128+2.0*sin(2*PI*(Y/19+T/6))+0.6*cos(2*PI*T/10)',scale=1400:310:flags=bilinear[xsea];"
 "nullsrc=s=350x78:r=24:d=60,format=gray,geq=lum='128+1.8*sin(2*PI*(X/95+T/12))+0.6*cos(2*PI*T/10)',scale=1400:310:flags=bilinear[ysea];"
 "[sea][xsea][ysea]displace=edge=smear,format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='if(between(X,200,1000)*gte(Y,210),0,78*exp(-pow((X-700)/650,4)-pow((Y-135)/100,4)))'[sea_fx];"
 '[bg][sea_fx]overlay=500:320[openwater];'
 '[surf0]crop=340:400:1570:480[surf];'
 "nullsrc=s=85x100:r=24:d=60,format=gray,geq=lum='128+2.3*sin(2*PI*(Y/27+T/10))+0.5*cos(2*PI*T/6)',scale=340:400:flags=bilinear[xsurf];"
 "nullsrc=s=85x100:r=24:d=60,format=gray,geq=lum='128+1.7*sin(2*PI*(X/47+T/12))+0.5*cos(2*PI*T/15)',scale=340:400:flags=bilinear[ysurf];"
 "[surf][xsurf][ysurf]displace=edge=smear,format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='68*exp(-pow((X-170)/145,4)-pow((Y-195)/165,4))'[surf_fx];"
 '[openwater][surf_fx]overlay=1570:480[shore];'
 f"[shore]ass=filename='{ass.as_posix()}',format=yuv420p[out]"
 )

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--image',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);ap.add_argument('--seconds',type=float,default=PERIOD);ap.add_argument('--qp',type=int,default=1);a=ap.parse_args()
 a.output.parent.mkdir(parents=True,exist_ok=True);ass=a.output.parent/'reflejos-mar.ass';ass.write_text(water_glints())
 cmd=['ffmpeg','-hide_banner','-loglevel','warning','-nostdin','-y','-filter_complex_threads','2','-loop','1','-framerate',str(FPS),'-i',str(a.image),'-filter_complex',filters(ass),'-map','[out]','-an','-t',str(a.seconds),'-c:v','libx264','-threads','3','-preset','fast','-qp',str(a.qp),'-profile:v','high','-g',str(10*FPS),'-keyint_min',str(10*FPS),'-sc_threshold','0','-flags','+cgop','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output)]
 cache=a.output.parent/'font-cache';cache.mkdir(exist_ok=True)
 subprocess.run(cmd,check=True,env=dict(os.environ,XDG_CACHE_HOME=str(cache)))
 config={'period_seconds':PERIOD,'fps':FPS,'width':W,'height':H,'effects':['small open-sea reflection displacement','small right-hand surf displacement','six faint water glints'],'characters_animated':False,'lighthouse_animated':False,'horizon_animated':False,'source_artwork':a.image.name,'open_sea_patch':[500,320,1400,310],'open_sea_alpha':'max78/255 with superellipse taper; zero for localX200..1000 and localY>=210','right_surf_patch':[1570,480,340,400],'right_surf_alpha':'max68/255 with superellipse taper','qp':a.qp}
 (a.output.parent/'escena-config.json').write_text(json.dumps(config,indent=2)+'\n');print(a.output)
if __name__=='__main__':main()
