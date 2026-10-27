#!/usr/bin/env python3
"""New editorial performance of Mutopia's complete Vivaldi RV297.

Requires Python 3, numpy and mido. Uses compiled notation MIDI as pitch/rhythm
source and LilyPond engraver exports as articulation/slur source. No audio input.
Times are seconds. Performance MIDI uses a documented 1000ticks/s clock.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, math, pathlib, sys
import numpy as np
import mido
PARTS=['solo','violin1','violin2','viola','cello']
LENGTHS=[252,72,229.5]
TITLES=['I. Allegro non molto','II. Largo','III. Allegro']
TEMPI={
 1: [(0,68),(12,69),(40,71),(44,72),(68,71),(72,70),(86,72),(102,73),(150,72),(156,69),(184,69),(216,70),(220,74),(244,71),(248,58),(252,48)],
 2: [(0,37.5),(8,38.5),(16,37.5),(24,38.5),(30,36.8),(32,37.8),(44,38.4),(52,38.2),(60,36.5),(62,35.5),(68,31),(72,24)],
 3: [(0,70.5),(30,71),(36,73),(57,71),(61.5,73),(70.5,73),(75,74),(126,73),(138,71),(148.5,69),(149.9999,69),(150,44),(174,44),(178.4999,43),(178.5,74),(204,75),(222,73),(225,64),(228,50),(229.5,42)]
}
# General phrasing level. Each voice retains its own score dynamics below.
PHRASE={
 1:[(0,.76),(12,.83),(40,.95),(44,.98),(68,.88),(72,.95),(88,1),(102,.94),(130,.96),(156,.85),(184,.65),(212,.77),(220,1),(244,.96),(248,.91),(252,.70)],
 2:[(0,.80),(8,.88),(16,.84),(24,.94),(28,.85),(31,.78),(32,.80),(40,.86),(48,.90),(56,.91),(60,.83),(64,.80),(68,.70),(72,.50)],
 3:[(0,.88),(24,.94),(36,.92),(57,.87),(61.5,.91),(70.5,.98),(75,.95),(117,1),(138,.92),(150,.76),(165,.87),(178,.89),(178.5,1),(204,1),(225,.94),(229.5,.70)]
}

def interp(points,x):
 return float(np.interp(x,[p[0] for p in points],[p[1] for p in points]))

def clock(mov):
 end=LENGTHS[mov-1]
 q=np.linspace(0,end,round(end*768)+1)
 bpm=np.interp(q,[p[0] for p in TEMPI[mov]],[p[1] for p in TEMPI[mov]])
 # 0.45% breathing within four-bar phrases, shared by every part.
 bar=4 if mov!=3 else 1.5
 bpm*=1+.0045*np.sin(2*np.pi*q/(bar*4))
 sec=np.zeros_like(q)
 sec[1:]=np.cumsum((60/bpm[:-1]+60/bpm[1:])*.5*np.diff(q))
 return lambda at: float(np.interp(at,q,sec)),float(sec[-1])

def load_midi(path,mov):
 mid=mido.MidiFile(path); out=[]
 assert len(mid.tracks)==6
 for track_id,tr in enumerate(mid.tracks[1:],start=1):
  part=PARTS[track_id-1]; tick=0; active=collections.defaultdict(list); idx=0
  for e in tr:
   tick+=e.time
   if e.type=='note_on' and e.velocity:
    active[e.channel,e.note].append((tick,e.velocity))
   elif e.type=='note_off' or (e.type=='note_on' and not e.velocity):
    assert active[e.channel,e.note],(mov,part,e)
    start,v=active[e.channel,e.note].pop(0)
    out.append(dict(source_id=f'{mov}:{part}:{idx}',movement=mov,part=part,
      quarter=start/mid.ticks_per_beat,gate_quarters=(tick-start)/mid.ticks_per_beat,
      pitch=e.note,source_velocity=v)); idx+=1
  assert not any(active.values())
  assert tick/mid.ticks_per_beat==LENGTHS[mov-1]
 return out

def slur_ranges(source):
 ranges=collections.defaultdict(list)
 for mov in (1,2,3):
  for part in PARTS:
   for kind in ('SLUR','PHRASE'):
    stack=[]
    for e in sorted([e for e in source if e['movement']==mov and e['part']==part and e['kind']==kind],key=lambda x:(x['quarter'],-x['direction'])):
     if e['direction']==-1:stack.append(e['quarter'])
     elif stack:ranges[mov,part].append((stack.pop(),e['quarter']))
 return ranges

def upper_diatonic(pitch,mov):
 # F minor melodic context for I; E-flat major for II. Editorial upper neighbour.
 pcs=[0,1,3,5,7,8,10] if mov in (1,3) else [0,2,3,5,7,8,10]
 return next(n for n in range(pitch+1,pitch+4) if n%12 in pcs)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--score-dir',type=pathlib.Path,required=True);ap.add_argument('--out-dir',type=pathlib.Path,required=True);a=ap.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
 source=json.loads((a.score_dir/'source-events.json').read_text())
 art=collections.defaultdict(set); written=collections.defaultdict(list)
 for e in source:
  key=(e['movement'],e['part'],round(e['quarter'],6))
  if e['kind']=='ART':art[key].add(e['articulation'])
  if e['kind']=='NOTE':written[key+(e['pitch'],)].append(e['duration_quarters'])
 slurs=slur_ranges(source)
 allsource=[];events=[];cc=[];movements=[];audit=[];offset=.75
 for mov,name in enumerate(['score.midi','score-1.midi','score-2.midi'],start=1):
  notes=load_midi(a.score_dir/name,mov);allsource+=notes
  at,end=clock(mov); start=offset
  counters=collections.Counter()
  for n in notes:
   part=n['part']; q=n['quarter']; p=n['pitch']; key=(mov,part,round(q,6)); arts=art[key]
   lengths=written.get(key+(p,),[]); notation_length=max(lengths) if lengths else n['gate_quarters']
   slurred=any(lo<=q<hi for lo,hi in slurs[mov,part])
   is_pizz=mov==2 and part in ('violin1','violin2')
   if is_pizz: articulation='pizzicato'
   elif 'staccato' in arts or 'staccatissimo' in arts: articulation='spiccato'
   elif mov!=2 and n['gate_quarters']<=.13 and not slurred: articulation='spiccato'
   else: articulation='sustain'
   gate=n['gate_quarters']
   if 'staccatissimo' in arts:gate=notation_length*.38
   elif 'staccato' in arts:gate=notation_length*.60
   elif articulation=='spiccato':gate*=.92
   elif is_pizz:gate=min(gate,.23)
   elif slurred:gate*=1.015
   else:gate*=.985
   gate=min(gate,LENGTHS[mov-1]-q)
   # Tiny, deterministic attack offsets; ensemble stays synchronized within 7ms.
   jitter=.0018*math.sin((q*31.73+PARTS.index(part)*3.1))
   onset=start+at(q)+jitter
   duration=max(.035,at(q+gate)-at(q))
   velocity={'solo':87,'violin1':75,'violin2':73,'viola':69,'cello':75}[part]
   # Score piano/forte contrast, not per-note random loudness.
   if mov==1 and 184<=q<220 and part!='cello':velocity-=17
   if mov==1 and q>=220:velocity+=4
   if mov==2:
    velocity={'solo':81,'violin1':72,'violin2':70,'viola':48,'cello':58}[part]
   if mov==3 and 90<=q<150 and part in ('violin1','violin2'):velocity-=13
   # Gentle downbeat articulation; grouped slurs have no accents on inner notes.
   bar=4 if mov!=3 else 1.5
   if abs(q%bar)<.01:velocity+=3
   elif abs(q%1)<.01 and not slurred:velocity+=1
   if slurred and any(abs(q-hi)<.01 for lo,hi in slurs[mov,part]):velocity-=2
   velocity+=round(1.5*math.sin(q*2.06+PARTS.index(part)))
   velocity=max(40,min(104,velocity))
   base=dict(start=round(onset,6),duration=round(duration,6),pitch=p,velocity=velocity,part=part,articulation=articulation,source_id=n['source_id'],source_quarter=q,movement=mov)
   if 'trill' in arts and part=='solo':
    # The annotation exists in notation but is not emitted by LilyPond MIDI.
    # Preserve anchor, span and pitch; realize an alternating diatonic upper note.
    trgate=notation_length*(.74 if 'staccato' in arts else .97)
    trgate=min(trgate,LENGTHS[mov-1]-q)
    span=at(q+trgate)-at(q)
    count=max(3,int(round(span*8)))
    if count%2==0:count+=1
    if span<.38:count=3
    # Final principal settles over the last 12% of long cadential ornaments.
    settle=span*.12 if span>1.5 else 0
    for k in range(count):
     st=span-settle
     ev=dict(base);ev.update(start=round(onset+st*k/count,6),duration=round(st/count*.95+(settle if k==count-1 else 0),6),pitch=p if k%2==0 else upper_diatonic(p,mov),articulation='spiccato' if st/count<.2 else 'sustain',ornament='notated_trill',ornament_index=k,velocity=max(40,velocity-(2 if k%2 else 0)))
     events.append(ev)
    counters['realized_trills']+=1
   else:events.append(base)
   counters[articulation]+=1
   # Quiet organ follows the basso only. Respect the initial Tasto Solo of III.
   if part=='cello' and not (mov==3 and q<36):
    organ=dict(base);organ.update(part='continuo',velocity=48 if mov!=2 else 42,articulation='sustain',duration=round(max(.035,at(q+min(notation_length*.94,LENGTHS[mov-1]-q))-at(q)),6),continuo_policy='bass_doubling_no_invented_figured_harmony')
    events.append(organ);counters['continuo']+=1
  music_end=start+end
  # Three-second room tail and a modest breath; no overlaps/cut cadences.
  offset=math.ceil((music_end+3.5)*24)/24
  movements.append(dict(index=mov,title=TITLES[mov-1],start=round(start,6),music_end=round(music_end,6),notated_quarters=LENGTHS[mov-1],music_duration=round(end,6),tail_and_breath=round(offset-music_end,6),tempo_points_quarter_bpm=TEMPI[mov],nominal_quarter_bpm={1:70,2:38,3:72}[mov]))
  for part in PARTS+['continuo']:
   for rel in np.arange(0,end+.1,.5):
    # Shared phrase breathing and part-specific orchestration. CC11 is independent
    # of velocity-layer choice, so a sustained note can swell naturally.
    qgrid=np.linspace(0,LENGTHS[mov-1],2001)
    tgrid=np.array([at(q) for q in qgrid])
    break
   qgrid=np.linspace(0,LENGTHS[mov-1],2001);tgrid=np.array([at(q) for q in qgrid])
   for rel in np.arange(0,end+.1,.5):
    q=float(np.interp(rel,tgrid,qgrid));level=interp(PHRASE[mov],q)
    level*=1+.025*math.sin(2*math.pi*q/(16 if mov!=3 else 6))
    if part=='continuo':level*=.86
    cc.append(dict(time=round(start+rel,6),part=part,cc=11,value=max(42,min(117,round(112*level)))))
  audit.append(dict(movement=mov,source_notes=len(notes),notes_by_part=dict(collections.Counter(n['part'] for n in notes)),articulation_counts=dict(counters)))
 duration=math.ceil((offset+.5)*24)/24
 events.sort(key=lambda e:(e['start'],e['part'],e['pitch']))
 # Every source note survives either as one anchor or as an explicitly linked trill.
 grouped=collections.defaultdict(list)
 for e in events:
  if e['part']!='continuo':grouped[e['source_id']].append(e)
 assert set(grouped)=={n['source_id'] for n in allsource}
 for n in allsource:
  es=grouped[n['source_id']]; assert es[0]['pitch']==n['pitch'],n
  assert all(e['part']==n['part'] for e in es)
  assert any(e['pitch']==n['pitch'] for e in es)
 assert all(e['start']>=0 and e['duration']>0 and e['start']+e['duration']<duration for e in events)
 mix={'solo':{'gain_db':-1.5,'pan':-.12,'width':.30},'violin1':{'gain_db':-8.0,'pan':-.45,'width':.45},'violin2':{'gain_db':-8.5,'pan':.30,'width':.45},'viola':{'gain_db':-10.0,'pan':.18,'width':.40},'cello':{'gain_db':-6.5,'pan':0,'width':.35},'continuo':{'gain_db':-22.0,'pan':0,'width':.35}}
 result=dict(schema='jagoncito-performance-events/1',sample_rate=44100,duration=duration,movements=movements,mix=mix,events=events,cc_events=cc,performance_notes=['Complete three movements; no notes truncated to fit target duration.','Original compiled notation MIDI remains unmodified; velocities, gates and shared tempo are editorial.','Notated solo trills realized explicitly with linked upper-diatonic neighbours; not a copied audio performance.','Second movement: violin I/II pizzicato, viola arco pianissimo, cello quiet.','Third movement: Lento/Sirocco q150..178.5; Borea returns to Allegro; initial Tasto Solo respected.','Continuo is discreet organ doubling of bass, not a full realization of every figured-bass indication.','Performance MIDI uses 1000ticks/s timebase at 60BPM; musical tempos are recorded in JSON.'])
 (a.out_dir/'performance.json').write_text(json.dumps(result,indent=2)+'\n')
 (a.out_dir/'source-notes.json').write_text(json.dumps(allsource,indent=2)+'\n')
 # One linked, expressive MIDI, including all actual ornament and continuo events.
 mid=mido.MidiFile(type=1,ticks_per_beat=1000);meta=mido.MidiTrack();mid.tracks.append(meta);meta.append(mido.MetaMessage('set_tempo',tempo=1000000,time=0));last=0
 for mv in movements:
  tick=round(mv['start']*1000);meta.append(mido.MetaMessage('marker',text=mv['title'],time=tick-last));last=tick
 for ch,part in enumerate(PARTS+['continuo']):
  tr=mido.MidiTrack();mid.tracks.append(tr);tr.append(mido.MetaMessage('track_name',name=part,time=0));rows=[]
  for e in events:
   if e['part']==part:
    rows.append((round(e['start']*1000),1,mido.Message('note_on',channel=ch,note=e['pitch'],velocity=e['velocity'])))
    rows.append((round((e['start']+e['duration'])*1000),0,mido.Message('note_off',channel=ch,note=e['pitch'],velocity=0)))
  for e in cc:
   if e['part']==part:rows.append((round(e['time']*1000),-1,mido.Message('control_change',channel=ch,control=e['cc'],value=e['value'])))
  last=0
  for tick,order,msg in sorted(rows,key=lambda x:(x[0],x[1])):msg.time=tick-last;tr.append(msg);last=tick
  tr.append(mido.MetaMessage('end_of_track',time=max(0,round(duration*1000)-last)))
 mid.save(a.out_dir/'interpretacion-digital.midi')
 auditout=dict(status='passed',source_note_ids_preserved=len(grouped),source_notes=len(allsource),performance_events=len(events),movements=audit,source_files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.score_dir/n for n in ['score.midi','score-1.midi','score-2.midi','source-events.json']]},duration=duration,movement_timings=movements,scope='Pitch anchor, part and coverage audit against compiled source. This is not a subjective listening assessment.')
 (a.out_dir/'performance-validation.json').write_text(json.dumps(auditout,indent=2)+'\n')
 print(json.dumps({'duration':duration,'movements':movements,'events':len(events),'source_notes':len(allsource)},indent=2))
if __name__=='__main__':main()
