#!/usr/bin/env python3
"""Technical delivery checks. No subjective listening is claimed.

Decode every video frame, measure the full WAV, and compare every AAC cycle
against its PCM source. Run after assembling the final media.
"""
from pathlib import Path
import hashlib, json, subprocess
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]

def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)

def probe(path):
    return json.loads(run(['ffprobe','-v','error','-show_streams','-show_format',
                          '-of','json',str(path)]).stdout)

def compare_audio(path, source, repetitions):
    """Full decoded AAC / PCM correlation and error for each complete cycle."""
    p = subprocess.Popen(['ffmpeg','-v','error','-xerror','-i',str(path),'-map','0:a:0',
                          '-f','f32le','-acodec','pcm_f32le','-'], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    results=[]
    with sf.SoundFile(source) as wav:
        for cycle in range(repetitions):
            wav.seek(0)
            sums=np.zeros(7,dtype=np.float64)
            left=wav.frames
            while left:
                count=min(left,65536)
                raw=p.stdout.read(count*wav.channels*4)
                if len(raw)!=count*wav.channels*4:
                    raise AssertionError(f'AAC ends early: cycle {cycle+1}')
                x=wav.read(count,dtype='float64',always_2d=True).ravel()
                y=np.frombuffer(raw,dtype='<f4').astype(np.float64)
                sums+= [len(x),x.sum(),y.sum(),x@x,y@y,x@y,(x-y)@(x-y)]
                left-=count
            n,sx,sy,xx,yy,xy,error=sums
            corr=(xy-sx*sy/n)/np.sqrt((xx-sx*sx/n)*(yy-sy*sy/n))
            snr=10*np.log10(xx/max(error,1e-30))
            assert corr>.98, (path,cycle,corr)
            assert snr>18, (path,cycle,snr)
            results.append({'cycle':cycle+1,'correlation':float(corr),'snr_db':float(snr)})
    extra=p.stdout.read()
    stderr=p.stderr.read().decode()
    assert p.wait()==0,stderr
    # AAC may include a final padded packet shorter than 1024 samples.
    assert len(extra)<=1024*2*4, len(extra)
    return results

def main():
    audio=ROOT/'beethoven-adagio-cantabile.wav'
    montage=json.loads((ROOT/'montaje.json').read_text())
    repetitions=montage['complete_work_repetitions']
    info=sf.info(audio)
    assert info.channels==2 and info.samplerate==48000 and info.subtype=='PCM_24',str(info)
    peak=0.; clipped=0; total=0; dc=np.zeros(2); tail=None
    for block in sf.blocks(audio,blocksize=65536,dtype='float64',always_2d=True):
        peak=max(peak,float(np.max(np.abs(block))))
        clipped+=int(np.count_nonzero(np.abs(block)>=.99999))
        total+=len(block);dc+=block.sum(axis=0);tail=block
    assert clipped==0
    assert peak<.90,peak
    # Actual final sample and final 100 ms must return to silence.
    with sf.SoundFile(audio) as w:
        w.seek(w.frames-int(w.samplerate*.1)); end=w.read(dtype='float64')
    assert np.max(np.abs(end))<.0001
    loud=run(['ffmpeg','-hide_banner','-nostats','-i',str(audio),'-af',
              'loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json','-f','null','-']).stderr
    measurement=json.JSONDecoder().raw_decode(loud[loud.rfind('{'):])[0]
    assert float(measurement['input_tp'])<=-1.0,measurement
    report={'scope':'Technical validation; no subjective audition performed',
            'wav':{'frames':info.frames,'sample_rate':info.samplerate,'channels':info.channels,
                   'subtype':info.subtype,'duration':info.duration,'sample_peak':peak,
                   'clipped_samples':clipped,'dc':(dc/total).tolist(),
                   'last_100ms_peak':float(np.max(np.abs(end))), 'ebur128':{
                       'integrated_lufs':float(measurement['input_i']),
                       'true_peak_dbtp':float(measurement['input_tp']),
                       'loudness_range_lu':float(measurement['input_lra']),
                       'gating_threshold_lufs':float(measurement['input_thresh']),
                       'method':'FFmpeg loudnorm input analysis; processed null output discarded.'}},
            'videos':{},'sha256':{}}
    for name,repeats in [('beethoven-adagio-cantabile.mp4',1),('beethoven-adagio-cantabile-extended.mp4',repetitions)]:
        path=ROOT/name
        metadata=probe(path)
        v=next(s for s in metadata['streams'] if s['codec_type']=='video')
        a=next(s for s in metadata['streams'] if s['codec_type']=='audio')
        assert (v['width'],v['height'],v['codec_name'],a['codec_name'])==(1920,1080,'h264','aac')
        assert v['r_frame_rate']=='24/1' and v['pix_fmt']=='yuv420p'
        assert int(a['sample_rate'])==info.samplerate and a['channels']==2
        # Stream-copy with reordered H.264 pictures may retain up to two final
        # frames after the audio. Check the actual audio duration separately.
        assert abs(float(metadata['format']['duration'])-info.duration*repeats)<3/24
        assert abs(float(a['duration'])-info.duration*repeats)<.002
        decoded=run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'])
        assert not decoded.stderr,decoded.stderr
        chapters=json.loads(run(['ffprobe','-v','error','-show_chapters','-of','json',str(path)]).stdout)
        assert len(chapters['chapters'])==repeats
        for i,ch in enumerate(chapters['chapters']):
            assert abs(float(ch['start_time'])-i*info.duration)<.0015
        report['videos'][name]={'duration':float(metadata['format']['duration']),
            'full_decode':'passed','audio_cycles':compare_audio(path,audio,repeats),
            'video_stream':v,'audio_stream':a,'embedded_chapters':
            chapters}
        print(f'Validated {name}',flush=True)
    for path in sorted(ROOT.rglob('*')):
        if path.is_file() and path.name not in ('validacion-entrega.json','manifest.json'):
            h=hashlib.sha256()
            with path.open('rb') as f:
                for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
            report['sha256'][str(path.relative_to(ROOT))]=h.hexdigest()
    out=ROOT/'produccion'/'validacion-entrega.json'
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(out)

if __name__=='__main__':main()
