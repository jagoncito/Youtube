#!/usr/bin/env python3
"""Produce a validated Jagoncito bundle for one UTC four-hour slot.

No API keys or interactive generation are used. A delivery requires both an
unpublished scene and an unpublished unordered musical programme from the finite
curated catalogue. Seed changes do not establish creative novelty. Media are
generated outside the checkout; publication is handled by the caller.
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

def repository_asset(relative,root=REPO):
    root=Path(root).resolve()
    path=(root/relative).resolve()
    path.relative_to(root)
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

class NeedsNewAssets(ValueError):
    """The reviewed bank cannot supply both a new scene and a new programme."""


def creative_identity(plan,catalog,root=REPO):
    scene=plan.get('scene',catalog.get('scene'))
    if not isinstance(scene,dict) or not scene.get('id'):
        raise ValueError('A reviewed scene identity is required.')
    works=plan.get('works')
    if (not isinstance(works,list) or len(works)!=2 or len(set(works))!=2
            or any(type(n) is not int or n not in PROFILES for n in works)):
        raise ValueError('A musical programme must list two distinct supported work numbers.')
    image=repository_asset(scene['image'],root)
    if not image.is_file():
        raise ValueError('The reviewed scene image is unavailable.')
    with image.open('rb') as source:
        if source.read(100).startswith(b'version https://git-lfs.github.com/spec/v1'):
            raise ValueError('Download the real scene image with Git LFS before planning.')
    return dict(scene_sha256=digest(image),program=sorted(set(works)),scene_id=scene['id'])


def image_fingerprint(path):
    """Small decoded RGB tile and 256 luminance differences, independent of encoding.

    RGB is retained for low-detail images: a constant dHash must not make every
    solid colour the same image. This detects near copies, not artistic merit.
    """
    try:
        raw=subprocess.check_output(['ffmpeg','-v','error','-threads','1','-i',str(path),
            '-filter_threads','1','-vf','scale=17:16:flags=area','-frames:v','1',
            '-pix_fmt','rgb24','-f','rawvideo','pipe:1'],stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        raise ValueError('Cannot decode artwork for the image similarity check.') from error
    if len(raw)!=17*16*3:
        raise ValueError('Incomplete artwork image similarity sample.')
    rgb=np.frombuffer(raw,dtype=np.uint8).reshape(16,17,3).astype(np.float64)
    grey=rgb@np.array([.299,.587,.114])
    bits=grey[:,1:]>grey[:,:-1]
    return dict(rgb=rgb,grey=grey,dhash=bits)


def near_duplicate_image(a,b):
    """Conservative duplicate guard for re-encoding and modest cosmetic edits."""
    # Same pixels, metadata changes and ordinary recompression remain copies.
    rgb_rmse=float(np.sqrt(np.mean((a['rgb']-b['rgb'])**2)))
    if rgb_rmse<=4:
        return True
    if np.count_nonzero(a['dhash']!=b['dhash'])>12:
        return False
    left=a['grey']-np.mean(a['grey'])
    right=b['grey']-np.mean(b['grey'])
    # Flat images have a degenerate dHash. Only the RGB comparison above may
    # classify them as copies; red and blue must not collide as all-zero bits.
    if min(float(np.std(left)),float(np.std(right)))<3:
        return False
    correlation=float(np.sum(left*right)/np.sqrt(np.sum(left**2)*np.sum(right**2)))
    return correlation>=.985


def _document_identity(document,catalog):
    """Read old manifests as well as explicit identities in delivery records."""
    identity=dict(document.get('creative_identity') or {})
    manifest_image=document.get('files',{}).get('imagen.png',{}).get('sha256')
    chapters=[x['number'] for x in document.get('audio',{}).get('chapters',[])
              if isinstance(x,dict) and type(x.get('number')) is int]
    if identity.get('scene_sha256') and manifest_image and identity['scene_sha256']!=manifest_image:
        raise ValueError('Historical scene identity disagrees with the checksum manifest.')
    for works in [document.get('works'),document.get('program'),chapters]:
        if identity.get('program') and works and sorted(set(identity['program']))!=sorted(set(works)):
            raise ValueError('Historical programme identity disagrees with its musical works.')
    if not identity.get('scene_sha256'):
        identity['scene_sha256']=document.get('files',{}).get('imagen.png',{}).get('sha256')
    identity['scene_id']=identity.get('scene_id') or document.get('scene_id')
    if not identity.get('program'):
        identity['program']=document.get('program') or document.get('works')
    if not identity.get('program'):
        identity['program']=[x['number'] for x in document.get('audio',{}).get('chapters',[])
                             if isinstance(x,dict) and type(x.get('number')) is int]
    if not identity.get('program'):
        identity['program']=[int(match.group(1)) for name in document.get('files',{})
                             if (match:=re.search(r'(?:^|/)gymnopedie-(\d+)\.(?:ly|midi)$',name))]
    plan=next((p for p in catalog.get('plans',[]) if p['id']==document.get('plan_id')),None)
    if plan:
        identity['program']=identity.get('program') or plan['works']
        identity['scene_id']=identity.get('scene_id') or plan.get('scene',catalog.get('scene',{})).get('id')
    if identity.get('program'):
        identity['program']=sorted(set(identity['program']))
    return {key:value for key,value in identity.items() if value is not None and value!=[]}


def historical_identities(root,catalog,exclude_tag=None,image_paths=None):
    """Collect the entire published history, including files without an index row.

    A pending retry may exclude its own reservation. Existing published duplicates
    are preserved; every image and programme they used still blocks future use.
    Unknown published history blocks planning until its evidence is completed.
    """
    root=Path(root).resolve()
    identities=[]
    seen_manifests=set()
    excluded_folders=set()
    records=root/'automatizacion/entregas'
    record_documents=[json.loads(path.read_text()) for path in sorted(records.glob('*.json'))]
    retry_records=[item for item in record_documents if item.get('tag')==exclude_tag]
    retry_allowed=(bool(exclude_tag) and bool(retry_records)
                   and all(item.get('status') in ('pending','failure') for item in retry_records))
    def excluded(document):
        if not retry_allowed:
            return False
        if document.get('tag')==exclude_tag:
            return True
        try:
            stamp=utc_slot(document['slot'])
        except (KeyError,TypeError,ValueError):
            return False
        return stamp.strftime('jagoncito-%Y%m%d-%H00Z')==exclude_tag
    def combine(identity,other):
        for key,value in other.items():
            if identity.get(key) is not None and identity[key]!=value:
                raise ValueError('Historical creative identity disagrees with its manifest or media.')
            identity[key]=value
    def add(document,folder=None,required=False):
        if excluded(document):
            return
        identity=_document_identity(document,catalog)
        if folder is not None:
            image=folder/'imagen.png'
            if image.is_file():
                with image.open('rb') as source:
                    pointer=source.read(100).startswith(b'version https://git-lfs.github.com/spec/v1')
                if not pointer:
                    combine(identity,dict(scene_sha256=digest(image)))
        if required and (not identity.get('scene_sha256') or not identity.get('program')):
            raise NeedsNewAssets('Published history lacks its scene or programme identity; complete the historical manifest before publishing.')
        if identity:
            identities.append(identity)
    for record in record_documents:
        if excluded(record):
            folder=record.get('folder')
            if folder:
                excluded_folders.add(repository_asset(folder,root))
            elif record.get('card_path'):
                excluded_folders.add(repository_asset(record['card_path'],root).parent)
            continue
        identity=_document_identity(record,catalog)
        folder=None
        if record.get('folder'):
            folder=repository_asset(record['folder'],root)
        elif record.get('card_path'):
            folder=repository_asset(record['card_path'],root).parent
        elif isinstance(record.get('number'),int):
            folder=root/'videos'/f'{record["number"]:03d}'
        manifest=record.get('manifest')
        if isinstance(manifest,str):
            manifest_path=repository_asset(manifest,root)
            manifest=json.loads(manifest_path.read_text())
            seen_manifests.add(manifest_path)
        if folder is not None and (folder/'manifest.json').is_file():
            manifest_path=folder/'manifest.json'
            local=json.loads(manifest_path.read_text())
            seen_manifests.add(manifest_path)
            combine(identity,_document_identity(local,catalog))
        if isinstance(manifest,dict):
            combine(identity,_document_identity(manifest,catalog))
        # A failure/pending row with an identity also reserves those assets. The
        # caller can exclude the current retry by its exact tag.
        document=dict(record,creative_identity=identity)
        add(document,folder,required=record.get('status')=='success')
    for manifest_path in sorted((root/'videos').glob('*/manifest.json')):
        if manifest_path in seen_manifests:
            continue
        manifest=json.loads(manifest_path.read_text())
        seen_manifests.add(manifest_path)
        if excluded(manifest):
            excluded_folders.add(manifest_path.parent)
            continue
        add(manifest,manifest_path.parent,required=True)
    # Unindexed image folders must also prevent image reuse even when their
    # musical programme has not yet been reconstructed.
    for image in sorted((root/'videos').glob('*/imagen.png')):
        if image.parent in excluded_folders:
            continue
        if image_paths is not None:
            image_paths.add(image.resolve())
        if (image.parent/'manifest.json') not in seen_manifests:
            add({},image.parent)
    return identities


def select_new_plan(slot,catalog,root=REPO,plan_id=None,exclude_tag=None):
    """Choose only plans with a new scene AND a new unordered set of works."""
    image_paths=set()
    history=historical_identities(root,catalog,exclude_tag=exclude_tag,image_paths=image_paths)
    decoded={}
    image_hashes={}
    def fingerprint(path):
        path=Path(path).resolve()
        if path not in image_hashes:
            image_hashes[path]=digest(path)
        key=image_hashes[path]
        if key not in decoded:
            decoded[key]=image_fingerprint(path)
        return decoded[key]
    used_images={x['scene_sha256'] for x in history if x.get('scene_sha256')}
    used_scenes={x['scene_id'] for x in history if x.get('scene_id')}
    used_programmes={tuple(x['program']) for x in history if x.get('program')}
    plans=catalog['plans']
    if len({p['id'] for p in plans})!=len(plans) or not plans:
        raise ValueError('The catalogue must contain unique plan IDs.')
    if plan_id is not None:
        plans=[p for p in plans if p['id']==plan_id]
        if not plans:
            raise ValueError('Unknown plan ID.')
    # Retain predictable rotation as a preference, never as permission to reuse.
    offset=int(slot.timestamp())//14400%len(plans)
    for plan in plans[offset:]+plans[:offset]:
        scene=plan.get('scene',catalog.get('scene',{}))
        if scene.get('id') in used_scenes or tuple(sorted(set(plan['works']))) in used_programmes:
            continue
        identity=creative_identity(plan,catalog,root)
        if (identity['scene_sha256'] in used_images or identity['scene_id'] in used_scenes
                or tuple(identity['program']) in used_programmes):
            continue
        candidate=fingerprint(repository_asset(scene['image'],root))
        if any(near_duplicate_image(candidate,fingerprint(previous)) for previous in sorted(image_paths)):
            continue
        result=selection(slot,catalog,plan['id'])
        result['creative_identity']=identity
        return result
    raise NeedsNewAssets('No unpublished scene and musical programme remain. Add and review new artwork and music; seed changes and reordered works do not count as new material.')


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
    approved=REPO/'videos/001/imagen.png'
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
      'La escena y el programa musical no figuran en entregas anteriores. La interpretación se renderiza con variaciones expresivas; cambiar la semilla o el orden de las mismas obras no cuenta como una entrega nueva. '
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
    ap.add_argument('--history-exclude-tag',help='Exclude only this pending delivery reservation when retrying.')
    args=ap.parse_args()
    catalog=json.loads(args.catalog.read_text())
    verify_sources()
    try:
        plan=select_new_plan(utc_slot(args.slot),catalog,plan_id=args.plan_id,
                             exclude_tag=args.history_exclude_tag)
    except NeedsNewAssets as error:
        print(json.dumps({'status':'needs_new_assets','reason':str(error)},ensure_ascii=False))
        return 2
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
        manifest=dict(schema_version=2,creative_identity=plan['creative_identity'],slot=plan['slot'],plan_id=plan['id'],title=plan['title'],
                      seed=plan['seed'],works=plan['works'],intent=plan['intent'],catalogue_version=catalog['version'],
                      art_reused=scene.get('art_reused',True),scene_id=scene['id'],scene_axes=scene.get('axes',{}),
                      production='Unpublished scene and musical programme selected from a finite reviewed bank; seed and work order are not creative novelty.',
                      audio=audio,video_checks=checks,files=files,
                      subjective_listening_claim=False,published_to_youtube=False,producer_code_sha256=digest(Path(__file__)))
        (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        folder.rename(args.output)
    print(json.dumps({'bundle':str(args.output),'title':plan['title'],'slot':plan['slot'],'plan_id':plan['id']},ensure_ascii=False))

if __name__=='__main__':
    sys.exit(main())
