#!/usr/bin/env python3
"""New periodic garden-video effects; no static image retouching.

Only the pond interior is displaced and softly blended. Animals, pond rim and
plants outside the mask remain static. Two new vector petals drift on the water;
the pre-existing petal near Jagoncito is not claimed to move.
"""
from pathlib import Path
import argparse, json, math, os, subprocess
W,H,FPS,PERIOD=1920,1080,24,60

def stamp(t):
 n=round(t*100);return f'{n//360000}:{n//6000%60:02d}:{n%6000//100:02d}.{n%100:02d}'

def drift_events(duration):
 header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Petal,DejaVu Sans,12,&H00D8B7E6,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Glint,DejaVu Sans,12,&H00CFE6F5,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 events=[]
 def add(x,y,dx,dy,period,phase,opacity,shape,style,blur):
  for cycle in range(-1,math.ceil(duration/period)+1):
   begin=cycle*period-phase;end=begin+period
   a,b=max(0.,begin),min(duration,end)
   if b<=a:continue
   f0,f1=(a-begin)/period,(b-begin)/period
   def al(f):return round(255-opacity*math.sin(math.pi*f)**2)
   keys=[(f0,al(f0))]+[(q,al(q)) for q in (.125,.25,.375,.5,.625,.75,.875) if f0<q<f1]+[(f1,al(f1))]
   trans=''.join(f'\\t({round((keys[k-1][0]-f0)*period*1000)},{round((keys[k][0]-f0)*period*1000)},\\1a&H{keys[k][1]:02X}&)' for k in range(1,len(keys)))
   tag=(f'{{\\an7\\p1\\bord0\\shad0\\blur{blur}\\1a&H{keys[0][1]:02X}&{trans}'
        f'\\move({x+dx*f0:.3f},{y+dy*f0:.3f},{x+dx*f1:.3f},{y+dy*f1:.3f})}}')
   events.append(f'Dialogue: 1,{stamp(a)},{stamp(b)},{style},,0,0,0,,{tag}{shape}')
 petal='m -4 0 b -8 -4 -3 -6 0 -2 b 4 -6 8 -3 5 0 b 2 4 -2 4 -4 0'
 add(806,625,24,4,60,12,165,petal,'Petal',.35)
 add(1070,738,16,3,30,8,140,petal,'Petal',.4)
 glint='m 0 0 b 7 -0.5 14 -0.5 22 0 l 20 1 b 14 0.6 7 0.6 1 1'
 for x,y,phase in [(590,620,2),(884,684,8),(1054,756,13),(740,799,17)]:
  add(x,y,8,0,20,phase,35,glint,'Glint',1.2)
 return header+'\n'.join(events)+'\n'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--image',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--seconds',type=float,default=PERIOD);a=ap.parse_args()
 a.output.parent.mkdir(parents=True,exist_ok=True);ass=a.output.parent/'jardin-petalos.ass';ass.write_text(drift_events(PERIOD))
 # A strictly interior water patch avoids the rim and animals. Smooth alpha
 # tapers to zero before any hard crop boundary. Map phases all divide 60s.
 filters=(
 '[0:v]scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,setsar=1,format=yuv420p,split=2[bg][water0];'
 '[water0]crop=1080:420:160:470[water];'
 "nullsrc=s=270x105:r=24:d=60,format=gray,geq=lum='128+1.6*sin(2*PI*(Y/34+T/10))+0.55*cos(2*PI*T/6)',scale=1080:420:flags=bilinear[xmap];"
 "nullsrc=s=270x105:r=24:d=60,format=gray,geq=lum='128+1.3*sin(2*PI*(X/65+T/12))+0.4*cos(2*PI*T/10)',scale=1080:420:flags=bilinear[ymap];"
 "[water][xmap][ymap]displace=edge=smear,format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='65*exp(-pow((X-540)/475,4)-pow((Y-210)/145,4))'[ripples];"
 '[bg][ripples]overlay=160:470[pond];'
 f"[pond]ass=filename='{ass.as_posix()}',format=yuv420p[out]"
 )
 cmd=['ffmpeg','-hide_banner','-loglevel','warning','-nostdin','-y','-filter_complex_threads','2','-loop','1','-framerate',str(FPS),'-i',str(a.image),'-filter_complex',filters,'-map','[out]','-an','-t',str(a.seconds),'-c:v','libx264','-threads','3','-preset','fast','-qp','1','-profile:v','high','-g',str(10*FPS),'-keyint_min',str(10*FPS),'-sc_threshold','0','-flags','+cgop','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output)]
 cache=a.output.parent/'font-cache';cache.mkdir(exist_ok=True)
 subprocess.run(cmd,check=True,env=dict(os.environ,XDG_CACHE_HOME=str(cache)))
 (a.output.parent/'escena-config.json').write_text(json.dumps({'period_seconds':PERIOD,'fps':FPS,'width':W,'height':H,'effects':['soft interior-pond reflection displacement','two newly drawn drifting water petals','minute water glints'],'characters_animated':False,'pre_existing_near_dragon_petal_animated':False,'water_effect_rectangle':[160,470,1080,420],'mask':'65/255 max alpha; superellipse centre local540,210 radii475,145','source_artwork':a.image.name},indent=2)+'\n')
 print(a.output)
if __name__=='__main__':main()
