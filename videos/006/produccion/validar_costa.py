#!/usr/bin/env python3
"""Decode every cycle frame and measure its join, sea motion and static regions."""
from pathlib import Path
import argparse,json,subprocess
import numpy as np

def main():
 ap=argparse.ArgumentParser();ap.add_argument('video',type=Path);ap.add_argument('--output',required=True,type=Path);a=ap.parse_args()
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(a.video)]));v=meta['streams'][0]
 subprocess.run(['ffmpeg','-v','error','-xerror','-nostdin','-i',str(a.video),'-map','0:v:0','-f','null','-'],check=True)
 filt="select='lt(n,8)+eq(n,360)+eq(n,720)+gte(n,1432)',scale=960:540:flags=area,format=gray"
 data=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(a.video),'-vf',filt,'-vsync','0','-f','rawvideo','-pix_fmt','gray','-'])
 f=np.frombuffer(data,np.uint8).reshape(-1,540,960).astype(np.float32);assert len(f)==18
 near=np.r_[np.mean(abs(np.diff(f[:8],axis=0)),axis=(1,2)),np.mean(abs(np.diff(f[-8:],axis=0)),axis=(1,2))]
 adj=float(np.median(near));seam=float(abs(f[-1]-f[0]).mean())
 water=float(abs(f[8,180:265,300:920]-f[0,180:265,300:920]).mean())
 surf=float(abs(f[8,280:420,810:940]-f[0,280:420,810:940]).mean())
 animal=float(abs(f[8,295:465,400:740]-f[0,295:465,400:740]).mean())
 horizon=float(abs(f[8,140:157,450:940]-f[0,140:157,450:940]).mean())
 pier=float(abs(f[8,120:158,70:365]-f[0,120:158,70:365]).mean())
 report={'file':a.video.name,'full_decode':'passed','frames':int(v['nb_frames']),'width':v['width'],'height':v['height'],'duration_seconds':float(meta['format']['duration']),'codec':v['codec_name'],'profile':v['profile'],'pixel_format':v['pix_fmt'],'loop_boundary_gray_mae':seam,'adjacent_gray_mae_median':adj,'boundary_criterion':'boundary <= max(0.15, 4*ordinary adjacent MAE)','loop_boundary_passed':seam<=max(.15,4*adj),'sea_change_15s_gray_mae':water,'surf_change_15s_gray_mae':surf,'character_region_change_15s_gray_mae':animal,'horizon_change_15s_gray_mae':horizon,'breakwater_change_15s_gray_mae':pier,'environment_motion_present':water>.005 and surf>.005,'characters_animated':False,'lighthouse_animated':False,'subjective_audition_performed':False}
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 assert report['loop_boundary_passed'],'Visual loop seam exceeds unchanged threshold'
 assert report['environment_motion_present'],'Water/surf does not move'
 assert animal<.2 and horizon<.2 and pier<.2,'Protected land/animal region changes significantly'
 assert (report['width'],report['height'],report['frames'])==(1920,1080,1440)
if __name__=='__main__':main()
