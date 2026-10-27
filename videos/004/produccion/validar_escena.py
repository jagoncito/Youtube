#!/usr/bin/env python3
"""Decode every animation frame and inspect movement and the cyclic join."""
from pathlib import Path
import argparse,json,subprocess
import numpy as np

def main():
    ap=argparse.ArgumentParser();ap.add_argument('video',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(args.video)]))
    video=probe['streams'][0]
    # Decoder exercises the complete produced visual cycle.
    subprocess.run(['ffmpeg','-v','error','-xerror','-nostdin','-i',str(args.video),'-map','0:v:0','-f','null','-'],check=True)
    # Include ordinary adjacent frames plus both sides of the loop and two later states.
    filt="select='lt(n,8)+eq(n,360)+eq(n,720)+gte(n,1432)',scale=960:540:flags=area,format=gray"
    raw=subprocess.check_output(['ffmpeg','-v','error','-nostdin','-i',str(args.video),'-vf',filt,'-vsync','0','-f','rawvideo','-pix_fmt','gray','-'])
    frames=np.frombuffer(raw,dtype=np.uint8).reshape((-1,540,960)).astype(np.float32)
    if len(frames)!=18:raise ValueError(f'Expected 18 diagnostic frames, got {len(frames)}')
    normal=np.mean(np.abs(np.diff(frames[:8],axis=0)),axis=(1,2))
    late=np.mean(np.abs(np.diff(frames[-8:],axis=0)),axis=(1,2))
    boundary=float(np.abs(frames[-1]-frames[0]).mean())
    adjacent=float(np.median(np.r_[normal,late]))
    animal=frames[:,285:390,170:360]
    characters_change=float(np.abs(animal[0]-animal[8]).mean())
    exterior=frames[:,100:500,500:940]
    exterior_change=float(np.abs(exterior[0]-exterior[8]).mean())
    result={'file':args.video.name,'complete_video_decode':'passed','frames':int(video.get('nb_frames',0)),
            'width':video['width'],'height':video['height'],'duration_seconds':float(probe['format']['duration']),
            'loop_boundary_gray_MAE_0_255':boundary,'ordinary_adjacent_gray_MAE_median':adjacent,
            'boundary_criterion':'boundary <= max(0.15, 4*ordinary adjacent MAE)',
            'loop_boundary_passed':boundary<=max(.15,4*adjacent),
            'outdoor_change_15s_gray_MAE':exterior_change,'sheltered_character_region_change_15s_gray_MAE':characters_change,
            'environment_motion_present':exterior_change>.005,
            'characters_animated':False,'subjective_audio_review':False}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    assert result['loop_boundary_passed'],'Visual loop seam exceeds normal nearby movement'
    assert result['environment_motion_present'],'Outdoor region is static'
    assert result['frames']==1440 and result['width']==1920 and result['height']==1080
if __name__=='__main__':main()
