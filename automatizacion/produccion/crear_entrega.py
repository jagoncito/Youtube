#!/usr/bin/env python3
"""Produce a validated Jagoncito bundle for one UTC four-hour slot.

No API keys or interactive generation are used: this is a finite curated music
catalogue, fresh seeded performances and approved existing visual assets. Media
are generated outside the checkout; publication is handled by the caller.
"""
from __future__ import annotations
import argparse, contextlib, datetime as dt, hashlib, importlib.util, json, os, re
from pathlib import Path
import shutil, subprocess, sys, tempfile
import numpy as np
from scipy.io import wavfile
import piano

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
SR=44100
PERIOD=12
BASE=360
PIN='2144afd6f52d56c5b6995b8b589ef1268b3139f0'
PROFILES={
  1:dict(quarters=234,bars=78,preferred_seconds=190,phrase_ends=[36,63,93,117,153,180,210,234]),
  2:dict(quarters=195,bars=65,preferred_seconds=180,phrase_ends=[24,36,72,111,141,165,180,195]),
  3:dict(quarters=180,bars=60,preferred_seconds=170,phrase_ends=[39,60,81,120,144,165,180]),
}

def repository_asset(relative):
    path=(REPO/relative).resolve()
    path.relative_to(REPO)
    return path


def digest(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def utc_slot(value):
    date=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if date.tzinfo is None:
        raise ValueError('The slot must include its UTC timezone.')
    date=date.astimezone(dt.timezone.utc)
    if date.minute or date.second or date.microsecond or date.hour%4:
        raise ValueError('The UTC slot must start at 00, 04, 08, 12, 16 or 20:00.')
    return date

def selection(slot,catalog,plan_id=None):
    plans=catalog['plans']
    if len({x['id'] for x in plans}) != len(plans) or not plans:
        raise ValueError('The catalogue must contain unique plan IDs.')
    if plan_id:
        plan=next((x for x in plans if x['id']==plan_id),None)
        if plan is None: raise ValueError('Unknown plan ID.')
    else:
        plan=plans[int(slot.timestamp())//14400%len(plans)]
    canonical=slot.isoformat().replace('+00:00','Z')
    seed=int(hashlib.sha256(f'{canonical}:{plan["id"]}:v{catalog["version"]}'.encode()).hexdigest()[:8],16)
    a,b=plan['works']
    total=PROFILES[a]['preferred_seconds']+PROFILES[b]['preferred_seconds']
    first=round(BASE*PROFILES[a]['preferred_seconds']/total)+(seed%5-2)
    seconds=[first,BASE-first]
    result=dict(plan,slot=canonical,seed=seed,work_seconds=seconds)
    assert all(150<=s<=210 for s in seconds)
    return result

def verify_sources():
    manifest=json.loads((HERE/'fuentes.json').read_text())
    for score in manifest['scores']:
        n=score['number']
        for name,key in [(f'gymnopedie-{n}.ly','sha256'),
                         (f'gymnopedie-{n}.midi','midi_sha256'),
                         (f'gymnopedie-{n}-render.ly','render_source_sha256')]:
            if digest(HERE/name)!=score[key]:
                raise ValueError(f'Score verification failed: {name}')


def run(cmd,**kwargs):
    subprocess.run([str(x) for x in cmd],check=True,**kwargs)

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))

def make_audio(plan,output,cache):
    samples=piano.verify_and_load_samples(cache)
    play=piano.make_piano(samples)
    tracks=[];chapters=[];offset=0
    for n,seconds in zip(plan['works'],plan['work_seconds']):
        profile=dict(PROFILES[n],number=n,seconds=seconds,seed=plan['seed']+n*7919,
                     dynamic_bias=((plan['seed']//17)%7-3)*.20)
        notes=piano.read_score(HERE/f'gymnopedie-{n}.midi')
        if max(x['end'] for x in notes)!=profile['quarters']:
            raise ValueError('Incomplete score duration.')
        track,info=piano.render_work(profile,notes,play)
        tracks.append(track)
        chapters.append(dict(number=n,title=f'Erik Satie — Gymnopédie No. {n}',
                             start_seconds=offset,duration_seconds=seconds,**info))
        offset+=seconds
    music=np.concatenate(tracks)
    if len(music)!=BASE*SR: raise ValueError('Incorrect base duration.')
    rms=float(np.sqrt(np.mean(music.astype(np.float64)**2)))
    rain=piano.make_rain(len(music),rms,seed=plan['seed']^3191888)
    combined=music+rain
    del tracks,music,rain
    with tempfile.TemporaryDirectory(prefix='jagoncito-master-') as td:
        premaster=Path(td)/'premaster.wav'
        wavfile.write(premaster,SR,combined)
        before=piano.loudness(premaster)
    gain_db=min(-21-float(before['input_i']),-1.8-float(before['input_tp']))
    combined*=10**(gain_db/20)
    rng=np.random.default_rng(plan['seed']^1381888)
    combined+=(rng.random(combined.shape,dtype=np.float32)-rng.random(combined.shape,dtype=np.float32))/65536
    pcm=np.round(np.clip(combined,-1,1)*32767).astype(np.int16)
    wavfile.write(output,SR,pcm)
    levels=piano.loudness(output)
    clipped=int(np.sum(np.abs(pcm.astype(np.int32))>=32767))
    if clipped or float(levels['input_tp'])>-1.5:
        raise ValueError('Audio level validation failed.')
    # Compare the actual wrap step to ordinary adjacent quiet-rain samples.
    neighborhood=np.concatenate((pcm[-SR:],pcm[:SR])).astype(np.int32)
    steps=np.abs(np.diff(neighborhood,axis=0))
    seam=steps[SR-1]
    typical=np.concatenate((steps[:SR-1],steps[SR:]))
    bound=np.percentile(typical,99,axis=0)*1.5+2
    if np.any(seam>bound): raise ValueError('Audio loop introduces an abnormal sample step.')
    return dict(duration_seconds=BASE,chapters=chapters,notes=sum(x['notes'] for x in chapters),
                integrated_lufs=float(levels['input_i']),true_peak_dbtp=float(levels['input_tp']),
                clipped_samples=clipped,loop_delta_pcm16=seam.tolist(),
                loop_reference_p99_pcm16=np.percentile(typical,99,axis=0).tolist(),
                waveform_sha256=digest(output),rain_relative_rms_db=-27)

def make_scene(scene,output,seed):
    if scene.get('scene_template'):
        shutil.copyfile(repository_asset(scene['scene_template']),output)
        return
    source=repository_asset(scene['animator'])
    spec=importlib.util.spec_from_file_location('jagoncito_scene',source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The approved scene has validated effect coordinates. Do not apply them
    # silently to an unrelated scene: a new scene requires its own template.
    approved=REPO/'videos/002-jagoncito-satie/imagen.png'
    if repository_asset(scene['image'])!=approved.resolve():
        raise ValueError('A different scene requires an approved scene_template.')
    old_argv=sys.argv
    try:
        module.ROOT=approved.parent
        # Generated ASS stays outside tracked directories.
        with tempfile.TemporaryDirectory(prefix='jagoncito-rain-') as td:
            module.HERE=Path(td)
            sys.argv=[str(source),'--output',str(output)]
            with contextlib.redirect_stdout(sys.stderr):
                module.main()
    finally:
        sys.argv=old_argv

def validate_scene(scene,template=None):
    if scene.get('scene_template'):
        if not scene.get('scene_manifest'):
            raise ValueError('A pre-rendered scene requires its reviewed manifest.')
        evidence=json.loads(repository_asset(scene['scene_manifest']).read_text())
        if not evidence.get('seam_pass') or not evidence.get('source_raw',{}).get('periodic_pass'):
            raise ValueError('The pre-rendered scene has not passed its seam review.')
        for key,field in [('image','source_image_sha256'),('thumbnail','thumbnail_sha256'),('scene_template','template_sha256')]:
            if digest(repository_asset(scene[key]))!=evidence[field]:
                raise ValueError(f'Scene integrity mismatch: {key}')
    image=probe(repository_asset(scene['image']))
    picture=next(x for x in image['streams'] if x['codec_type']=='video')
    if picture['width']<1280 or picture['height']<720:
        raise ValueError('Scene artwork is too small.')
    thumbnail=repository_asset(scene['thumbnail'])
    data=probe(thumbnail)
    picture=next(x for x in data['streams'] if x['codec_type']=='video')
    if (picture['width'],picture['height'])!=(1280,720) or thumbnail.stat().st_size>=2*1024**2:
        raise ValueError('Incorrect YouTube thumbnail size.')
    if template:
        data=probe(template)
        picture=next(x for x in data['streams'] if x['codec_type']=='video')
        if (picture['codec_name'],picture['width'],picture['height'],picture['r_frame_rate'])!=('h264',1920,1080,'24/1'):
            raise ValueError('The scene template must be H.264 1080p24.')
        if abs(float(data['format']['duration'])-PERIOD)>.01:
            raise ValueError('The scene template must contain one 12-second cycle.')


def make_movies(folder,template,title):
    for seconds,loops,name in [(BASE,0,'bucle-6min.mp4'),(1800,4,'video-30min.mp4')]:
        cmd=['ffmpeg','-hide_banner','-loglevel','warning','-nostdin','-y',
             '-stream_loop',str(seconds//PERIOD-1),'-i',str(template),
             '-stream_loop',str(loops),'-i',str(folder/'audio-bucle-6min.wav'),
             '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
             '-ar',str(SR),'-t',str(seconds),'-video_track_timescale','24000',
             '-metadata','artist=Jagoncito','-metadata',f'title={title}']
        if seconds==1800: cmd+=['-af','afade=t=out:st=1797:d=3']
        cmd+=['-movflags','+faststart',str(folder/name)]
        run(cmd)

def validate_movies(folder):
    results={}
    for name,seconds in [('bucle-6min.mp4',BASE),('video-30min.mp4',1800)]:
        data=probe(folder/name)
        v=next(x for x in data['streams'] if x['codec_type']=='video')
        a=next(x for x in data['streams'] if x['codec_type']=='audio')
        if (v['codec_name'],v['width'],v['height'],v['r_frame_rate'])!=('h264',1920,1080,'24/1'):
            raise ValueError('Incorrect video format.')
        if a['codec_name']!='aac' or a['channels']!=2 or a['sample_rate']!=str(SR):
            raise ValueError('Incorrect audio format.')
        if abs(float(data['format']['duration'])-seconds)>.05:
            raise ValueError('Incorrect film duration.')
        run(['ffmpeg','-hide_banner','-v','error','-xerror','-threads','2','-i',folder/name,
             '-map','0:v:0','-map','0:a:0','-f','null','-'],stdout=subprocess.DEVNULL)
        results[name]={'duration_seconds':seconds,'complete_decode_exit_code':0,
                       'width':1920,'height':1080,'fps':24,'bytes':(folder/name).stat().st_size}
    return results

def documents(folder,plan,audio,scene,catalog):
    lines=[]
    for repeat in range(5):
        for chapter in audio['chapters']:
            n=repeat*BASE+chapter['start_seconds']
            lines.append(f'{n//60:02d}:{n%60:02d} Gymnopédie No. {chapter["number"]}')
    numbers=' and '.join(str(n) for n in plan['works'])
    description=(scene.get('description','A quiet corner with Jagoncito and soft piano.')+'\n\n'
      +f'Soft Satie piano for {plan["intent"]}, accompanied by a very light layer of rain. '
      +scene.get('animation','Delicate rain moves quietly in the background.')+'\n\n'
      +f'Erik Satie’s Gymnopédies No. {numbers}, played completely in a newly rendered digital interpretation. '
      'This 30-minute session repeats a six-minute musical programme five times.\n\n'
      +'\n'.join(lines)+'\n\n'
      'Composition: Erik Satie (1888). Public-domain score transcriptions: Evin Robertson / Mutopia Project. '
      'Piano samples: VSCO 2 Community Edition, Simon Dalzell / Ivy Audio and Versilian Studios / Sam Gossner, CC0 1.0. '
      'Rain is synthesized. No commercial recording of the works is used.\n\n'
      +'\n'.join(f'https://github.com/MutopiaProject/MutopiaProject/blob/{PIN}/ftp/SatieE/gymnopedie_{n}/gymnopedie_{n}.ly' for n in plan['works'])
      +'\nhttps://github.com/sgossner/VSCO-2-CE/tree/440300901dfe9275fd84e0b7763af1f8443ae62e\n')
    tags='Jagoncito, Erik Satie, Gymnopedies, classical piano, soft piano, gentle rain, piano for reading, quiet focus'
    text=f'TÍTULO\n{plan["title"]}\n\nDESCRIPCIÓN\n{description}\nETIQUETAS\n{tags}\n'
    (folder/'publicacion.txt').write_text(text)
    sources=folder/'fuentes';sources.mkdir()
    for number in plan['works']:
        for suffix in ['ly','midi']:
            shutil.copyfile(HERE/f'gymnopedie-{number}.{suffix}',sources/f'gymnopedie-{number}.{suffix}')
    for name in ['VSCO-CC0-LICENSE.txt','fuentes.json','instrumento-vsco-fuentes.json']:
        shutil.copyfile(HERE/name,sources/name)
    (folder/'README.md').write_text(
      f'# {plan["title"]}\n\nPrograma {plan["id"]}, slot {plan["slot"]}. '
      'Incluye vídeo de 30 minutos, bucle de 6 minutos, un único WAV de 6 minutos, imagen, miniatura y textos de publicación. '
      'Los MP4 incorporan el audio. Las obras están completas; el montaje de 30 minutos repite la base cinco veces. '
      'La ilustración y la miniatura son activos aprobados reutilizados. La interpretación musical se ha renderizado de nuevo con variaciones expresivas controladas por la semilla del slot. '
      'No se utiliza una grabación ajena de la obra.\n\n'
      'Validación técnica automatizada; no se afirma escucha humana ni éxito comercial garantizado. '
      'La producción autónoma usa un catálogo finito; no ejecuta investigación ni generación de imágenes con IA en segundo plano.\n')
    return description

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--slot',required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--cache',type=Path,required=True)
    ap.add_argument('--catalog',type=Path,default=HERE/'catalogo.json')
    ap.add_argument('--plan-id')
    ap.add_argument('--plan-only',action='store_true')
    args=ap.parse_args()
    catalog=json.loads(args.catalog.read_text())
    verify_sources()
    plan=selection(utc_slot(args.slot),catalog,args.plan_id)
    if args.plan_only:
        print(json.dumps(plan,ensure_ascii=False,indent=2));return
    if args.output.exists(): raise ValueError('Output already exists; refusing to overwrite.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    scene=plan.get('scene',catalog['scene'])
    for key in ['image','thumbnail']:
        if not repository_asset(scene[key]).is_file(): raise FileNotFoundError(scene[key])
    validate_scene(scene)
    with tempfile.TemporaryDirectory(prefix='.jagoncito-bundle-',dir=args.output.parent) as td:
        folder=Path(td)/'bundle';folder.mkdir()
        shutil.copyfile(repository_asset(scene['image']),folder/'imagen.png')
        shutil.copyfile(repository_asset(scene['thumbnail']),folder/'miniatura.jpg')
        audio=make_audio(plan,folder/'audio-bucle-6min.wav',args.cache)
        template=Path(td)/'scene.mp4'
        make_scene(scene,template,plan['seed'])
        validate_scene(scene,template)
        make_movies(folder,template,plan['title'])
        checks=validate_movies(folder)
        documents(folder,plan,audio,scene,catalog)
        files={}
        for f in sorted(folder.rglob('*')):
            if f.is_file(): files[str(f.relative_to(folder))]={'bytes':f.stat().st_size,'sha256':digest(f)}
        manifest=dict(schema_version=1,slot=plan['slot'],plan_id=plan['id'],title=plan['title'],
                      seed=plan['seed'],intent=plan['intent'],catalogue_version=catalog['version'],
                      art_reused=scene.get('art_reused',True),scene_id=scene['id'],scene_axes=scene.get('axes',{}),
                      production='New seeded digital interpretation from a finite curated catalogue.',
                      audio=audio,video_checks=checks,files=files,
                      subjective_listening_claim=False,published_to_youtube=False,producer_code_sha256=digest(Path(__file__)))
        (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        folder.rename(args.output)
    print(json.dumps({'bundle':str(args.output),'title':plan['title'],'slot':plan['slot'],'plan_id':plan['id']},ensure_ascii=False))

if __name__=='__main__':
    main()
