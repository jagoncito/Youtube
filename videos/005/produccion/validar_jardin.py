#!/usr/bin/env python3
"""Technical cycle validation with a real full decode; no listening claimed."""
from pathlib import Path
import argparse,json,subprocess
import numpy as np

def main():
 ap=argparse.ArgumentParser();ap.add_argument('video',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(a.video)]));v=probe['streams'][0]
 subprocess.run(['ffmpeg','-v','error','-xerror','-nostdin','-i',str(a.video),'-map','0:v:0','-f','null','-'],check=True)
 filt="select='lt(n,8)+eq(n,360)+eq(n,720)+gte(n,1432)',scale=960:540:flags=area,format=gray"
 b=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(a.video),'-vf',filt,'-vsync','0','-f','rawvideo','-pix_fmt','gray','-'])
 f=np.frombuffer(b,np.uint8).reshape(-1,540,960).astype(np.float32);assert len(f)==18
 normal=np.mean(abs(np.diff(f[:8],axis=0)),axis=(1,2));late=np.mean(abs(np.diff(f[-8:],axis=0)),axis=(1,2));adj=float(np.median(np.r_[normal,late]));seam=float(abs(f[-1]-f[0]).mean())
 water=float(abs(f[8,270:430,250:600]-f[0,270:430,250:600]).mean())
 animal=float(abs(f[8,290:440,690:920]-f[0,290:440,690:920]).mean())
 result={'file':a.video.name,'full_decode':'passed','frames':int(v['nb_frames']),'width':v['width'],'height':v['height'],'duration_seconds':float(probe['format']['duration']),'codec':v['codec_name'],'profile':v['profile'],'pixel_format':v['pix_fmt'],'loop_boundary_gray_mae':seam,'adjacent_gray_mae_median':adj,'boundary_criterion':'boundary <= max(0.15, 4*ordinary adjacent MAE)','loop_boundary_passed':seam<=max(.15,4*adj),'water_change_15s_gray_mae':water,'character_region_change_15s_gray_mae':animal,'environment_motion_present':water>.005,'characters_animated':False,'auditory_review_performed':False}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 assert result['loop_boundary_passed'],'Cyclic join exceeds fixed visual threshold'
 assert result['environment_motion_present'],'Water region is static'
 assert animal<.2,'Supposedly static animals change significantly'
 assert (result['width'],result['height'],result['frames'])==(1920,1080,1440)
if __name__=='__main__':main()
