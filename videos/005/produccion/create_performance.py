#!/usr/bin/env python3
"""Expressive new piano performance of Chopin Op.27 No.2 from verified notation.

All 1806 compiled-source note anchors survive. Timestamped MIDI preserves the
printed graces/tuplets; explicit ornaments and editorial pedal cleaning are
documented. Musical tempo precedes and determines the eventual video duration.
"""
from pathlib import Path
import argparse,collections,hashlib,json,math
import numpy as np
import mido

QUARTERS=231
LEAD=.60
# Quarter-note beats per minute (6/8: dotted quarter = these figures / 1.5).
# Lento sostenuto; modest shared breathing, cadential ritardandi and a tempo.
TEMPO=[(0,42),(3,41.5),(6,43),(9,43),(12,40),(15,42.5),(18,43),
 (21,43),(24,39.5),(27,42),(36,43),(45,44),(51,45),(55,41),(57.75,44),
 (60,40),(63,40.5),(69,40),(72,37),(74.5,33),(75,42),(81,43),
 (87,40.5),(93,43),(96,42),(99,42),(108,43.5),(114,44.5),(123,45),
 (129,45),(132,44),(134.5,38),(135,42),(141,43),(144,41.5),(147,42),
 (150,40),(151.5,39),(153,37),(155.5,40),(156,42.5),(159,43),(168,44.5),
 (171,45),(174,43),(177,41.5),(180,40),(183,39),(184.5,38),(192,38),
 (198,37),(204,36.5),(207,35),(213,34),(216,33),(222,32),(225,30),
 (226.5,28),(228,25),(231,23)]
# Broad phrase/voicing interpretation. Local written hairpins refine it below.
RH=[(0,64),(3,65),(9,69),(12,65),(18,65),(21,72),(24,66),(27,63),
 (36,68),(45,72),(51,79),(55,63),(57.75,78),(60,70),(61.25,54),(63,56),
 (72,58),(75,64),(81,69),(87,65),(93,68),(96,64),(99,63),(108,68),
 (114,74),(123,77),(129,78),(132,78),(135,64),(141,73),(144,78),
 (147,78),(150,73),(153,78),(156,71),(159,72),(168,77),(171,80),
 (174,77),(177,76),(180,76),(183,76),(184.5,62),(192,59),(198,58),
 (204,56),(207,54),(213,52),(216,49),(222,47),(225,45),(228,42),(231,36)]

def interpolate(points,x):
 return float(np.interp(x,[p[0] for p in points],[p[1] for p in points]))

def clock():
 q=np.linspace(0,QUARTERS,QUARTERS*2048+1)
 bpm=np.interp(q,[p[0] for p in TEMPO],[p[1] for p in TEMPO])
 # Smooth phrase breaths shared by both hands; no asynchronous tempo drift.
 bpm*=1+.009*np.sin(2*np.pi*q/12)+.004*np.sin(2*np.pi*q/3)
 t=np.zeros_like(q);t[1:]=np.cumsum(.5*(60/bpm[:-1]+60/bpm[1:])*np.diff(q))
 return lambda x:float(np.interp(x,q,t)),float(t[-1])

def spans(source,kinds):
 """LilyPond ends all hairpins with a common STOP type; close by voice."""
 result=[];active={}
 for e in source:
  if e['kind'] not in kinds:continue
  key=(e['staff'],e['voice']);q=e['quarter']
  if e.get('direction')==1:
   if key in active:
    old=active.pop(key);result.append((old,q))
  elif e.get('direction')==-1:
   if key in active:result.append((active.pop(key),q))
   active[key]=e
 for old in active.values():result.append((old,min(QUARTERS,old['quarter']+6)))
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--score',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True);p.add_argument('--tail-seconds',type=float,default=1.25);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 notes=json.loads((a.score/'mapped-midi-notes.json').read_text())
 source=json.loads((a.score/'source-events.json').read_text())
 assert len(notes)==1806 and len({n['id'] for n in notes})==1806
 at,music_duration=clock();music_end=LEAD+music_duration
 # This piano/score release was first measured using a 12-second exploratory
 # buffer. Only 1.25 seconds are needed after the final key release; the master
 # still verifies actual decay before any sub-audible fade.
 duration=math.ceil((music_end+a.tail_seconds)*24)/24
 art=collections.defaultdict(set)
 for e in source:
  if e['kind']=='ART':art[e['staff'],round(e['quarter'],6)].add(e['articulation'])
 ph=spans(source,{'SLUR','PHRASE'})
 hairpins=spans(source,{'CRESCENDO','DECRESCENDO'})
 # Terminate hairpins at an explicit dynamic if the engraver omits its STOP.
 hp=[]
 for e,end in hairpins:
  dyn=[d['quarter'] for d in source if d['kind']=='DYNAMIC' and d['staff']==e['staff'] and e['quarter']<d['quarter']<end]
  if dyn:end=min(dyn)
  if end>e['quarter']:hp.append((e,end))
 groups=collections.defaultdict(list)
 for n in notes:groups[n['staff'],round(n['onset_quarter'],6)].append(n)
 events=[];ornaments=[];pedal=[]
 for n in notes:
  q=n['onset_quarter'];mainq=n['main_quarter'];staff=n['staff'];pitch=n['pitch'];g=n['gate_quarters'];bar=n['bar']
  is_grace=n['grace_quarter']!=0
  arts=art[staff,round(mainq,6)]
  slurred=any(e['staff']==staff and e['voice']==n['voice'] and e['quarter']<=mainq<end for e,end in ph)
  # The MIDI gates already contain notated staccato and grace anticipations.
  # Preserve that distinction; lengthen plain connected notes very slightly.
  factor=1.012 if slurred and 'staccato' not in arts else .98
  if staff=='left':factor=.99
  endq=min(QUARTERS,q+g*factor)
  if staff=='right':
   value=interpolate(RH,mainq)
   top=max(x['pitch'] for x in groups[staff,round(q,6)])
   if pitch<top:value-=8
   if n['voice']=='2':value-=5
   if n['voice']=='' and not (150<=q<156):value-=3
   if is_grace:value-=8
   if g<.15:value-=2
  else:
   # Transparent accompaniment remains voiced across the full keyboard.
   value=interpolate(RH,mainq)*.67+1
   if abs(q%1.5)<.01:value+=3
   if pitch<46:value+=2
   if n['voice']!='bass':value+=2
  for e,end in hp:
   if e['staff']==staff and e['quarter']<=mainq<end:
    z=(mainq-e['quarter'])/(end-e['quarter'])
    dim=e['kind']=='DECRESCENDO' or 'smorz' in e.get('text','') or 'dim' in e.get('text','')
    value+=(-5 if dim else 5)*z
  if 'accent' in arts:value+=4
  if 'marcato' in arts:value+=5
  if any(e['kind']=='DYNAMIC' and e['dynamic']=='fz' and e['staff']==staff and abs(e['quarter']-mainq)<.005 for e in source):value+=7
  value+=1.0*math.sin(mainq*1.57+pitch*.13)
  velocity=max(27,min(96,round(value)))
  # Small deliberate melody placement against the shared accompaniment clock.
  rubato=(.012+.009*math.sin(q*.8)) if staff=='right' and not is_grace else 0
  if is_grace:rubato=-.004
  start=LEAD+at(q)+rubato
  end=LEAD+at(endq)+rubato
  ev={'start':round(start,6),'duration':round(max(.025,end-start),6),'pitch':pitch,
      'velocity':velocity,'part':'treble' if staff=='right' else 'bass','source_id':n['id'],
      'source_quarter':q,'main_quarter':mainq,'bar':bar,'voice':n['voice'],'grace':is_grace}
  # Written short upper mordents: ornament the top member, preserve lower voice.
  if staff=='right' and 'prall' in arts and pitch==max(x['pitch'] for x in groups[staff,round(q,6)]):
   span=ev['duration'];sequence=[pitch,pitch+2,pitch]
   for k,key in enumerate(sequence):
    item=dict(ev);item.update(start=round(start+k*span/3,6),duration=round(span/3*.92,6),pitch=key,ornament='written_prall',ornament_index=k)
    events.append(item)
   ornaments.append({'kind':'prall','source_id':n['id'],'quarter':q,'principal':pitch,'upper':pitch+2})
  elif n['id']=='right:556' and abs(q-151.5)<.01:
   # Opening trill before the score's explicitly written-out 18-note flourish.
   span=at(152)-at(q);count=7
   for k in range(count):
    item=dict(ev);item.update(start=round(start+k*span/count,6),duration=round(span/count*.92,6),pitch=pitch if k%2==0 else pitch+2,ornament='written_trill_lead_in',ornament_index=k)
    events.append(item)
   ornaments.append({'kind':'trill_lead_in','source_id':n['id'],'quarter':q,'end_quarter':152,'note':'The following printed fioritura is retained in full.'})
  elif n['id']=='right:21' and abs(q-19)<.01:
   # Turn printed at q19.75 during a tied E-flat: F E-flat D-natural E-flat.
   ev['duration']=round(LEAD+at(19.75)+rubato-start,6);events.append(ev)
   span=at(20)-at(19.75)
   for k,key in enumerate([77,75,74,75]):
    item=dict(ev);item.update(start=round(LEAD+at(19.75)+rubato+k*span/4,6),duration=round(span/4*.91,6),pitch=key,ornament='written_turn_D_natural',ornament_index=k)
    events.append(item)
   ornaments.append({'kind':'turn','source_id':n['id'],'quarter':19.75,'pitches':[77,75,74,75],'lower_accidental':'printed natural'})
  else:events.append(ev)
 # Physical piano keys cannot retain an old finger gate through a restrike.
 # The common damper pedal preserves resonance; no pitch anchor is removed.
 by_pitch=collections.defaultdict(list)
 for e in events:by_pitch[e['pitch']].append(e)
 gates_cleaned=0
 for same in by_pitch.values():
  same.sort(key=lambda e:e['start'])
  for old,new in zip(same,same[1:]):
   if old['start']+old['duration']>new['start']-.004:
    old['duration']=round(max(.015,new['start']-.004-old['start']),6);gates_cleaned+=1
 # Real source damper marks, with a small delay after each bass attack.
 for e in source:
  if e['kind']=='PEDAL':
   pedal.append({'time':round(LEAD+at(e['quarter'])+(.055 if e['direction']==-1 else 0),6),
      'cc':64,'value':127 if e['direction']==-1 else 0,'source_quarter':e['quarter'],'origin':'printed_pedal'})
 # Refresh only unusually long same-harmony pedal holds (e.g. opening Db).
 holds=[];on=None
 for e in sorted([e for e in source if e['kind']=='PEDAL'],key=lambda e:e['quarter']):
  if e['direction']==-1:on=e['quarter']
  elif on is not None:
   if e['quarter']-on>3.5:
    for q in np.arange((math.floor(on/3)+1)*3,e['quarter'],3):
     t=LEAD+at(float(q));pedal.extend([{'time':round(t+.016,6),'cc':64,'value':0,'source_quarter':float(q),'origin':'editorial_harmonic_refresh'},
       {'time':round(t+.085,6),'cc':64,'value':127,'source_quarter':float(q),'origin':'editorial_harmonic_refresh'}]);holds.append(float(q))
   on=None
 pedal+=[{'time':0.,'cc':64,'value':0,'origin':'initial_release'},{'time':round(music_end+.02,6),'cc':64,'value':0,'origin':'final_release'}]
 pedal.sort(key=lambda e:(e['time'],e['value']))
 events.sort(key=lambda e:(e['start'],e['pitch']))
 anchored=collections.defaultdict(list)
 for e in events:anchored[e['source_id']].append(e)
 assert set(anchored)=={n['id'] for n in notes}
 for n in notes:
  assert any(e['pitch']==n['pitch'] for e in anchored[n['id']]),n
 assert all(0<=e['start']<e['start']+e['duration']<duration for e in events)
 assert all(21<=e['pitch']<=108 and 1<=e['velocity']<=127 for e in events)
 result={'schema':'jagoncito-piano-performance/1','sample_rate':48000,'duration':duration,
  'music_start':LEAD,'notated_music_end':music_end,'notated_quarters':231,'bars':77,
  'work':'Frédéric Chopin: Nocturne in D-flat major, Op.27 No.2','tempo_unit':'quarter note',
  'tempo_points_bpm':TEMPO,'events':events,'cc_events':pedal,
  'notes':['One shared piano instance and physical damper state for both hands.',
   'Every compiled-source pitch anchor preserved; original MIDI stored separately.',
   'Printed grace anticipations/tuplets retained from MIDI; note lengths and velocities voiced editorially.',
   'Five short pralls, one delayed turn with printed D-natural, and a trill lead-in before printed fioritura are realized.',
   'Long same-harmony pedal holds refreshed at barlines; ordinary source pedal marks retained.',
   'No tempo adjustment to match a target video duration. No subjective listening performed.']}
 (a.out/'performance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 audit={'status':'passed','source_note_anchors':len(notes),'preserved_source_ids':len(anchored),
  'performance_note_events':len(events),'source_notes_by_staff':dict(collections.Counter(n['staff'] for n in notes)),
  'grace_note_anchors':sum(n['grace_quarter']!=0 for n in notes),'ornament_realizations':ornaments,
  'printed_pedal_marks':sum(e['kind']=='PEDAL' for e in source),'editorial_pedal_refresh_quarters':holds,
  'same_key_finger_gates_cleaned':gates_cleaned,'final_pedal_value':pedal[-1]['value'],
  'minimum_velocity':min(e['velocity'] for e in events),'maximum_velocity':max(e['velocity'] for e in events),
  'music_start':LEAD,'notated_music_end':music_end,'duration':duration,
  'source_sha256':{name:hashlib.sha256((a.score/name).read_bytes()).hexdigest() for name in ['partitura.midi','source-events.json','mapped-midi-notes.json']},
  'scope':'Coverage/voicing/pedal checks against the chosen digital score. No subjective audition or independent historical-edition collation.'}
 (a.out/'performance-validation.json').write_text(json.dumps(audit,indent=2)+'\n')
 # MIDI is a timestamped interchange performance at 1000 ticks/s, not notation.
 mid=mido.MidiFile(type=1,ticks_per_beat=1000);meta=mido.MidiTrack();mid.tracks.append(meta)
 meta.append(mido.MetaMessage('set_tempo',tempo=1000000,time=0));meta.append(mido.MetaMessage('track_name',name='Jagoncito Chopin Op27 No2 digital performance',time=0))
 track=mido.MidiTrack();mid.tracks.append(track);rows=[]
 for e in events:
  rows.extend([(round(e['start']*1000),2,mido.Message('note_on',note=e['pitch'],velocity=e['velocity'])),
   (round((e['start']+e['duration'])*1000),1,mido.Message('note_off',note=e['pitch'],velocity=0))])
 for e in pedal:rows.append((round(e['time']*1000),0,mido.Message('control_change',control=64,value=e['value'])))
 last=0
 for tick,order,msg in sorted(rows,key=lambda x:(x[0],x[1])):
  msg.time=tick-last;track.append(msg);last=tick
 track.append(mido.MetaMessage('end_of_track',time=max(0,round(duration*1000)-last)))
 mid.save(a.out/'interpretacion-digital.midi')
 print(json.dumps({k:audit[k] for k in ['status','source_note_anchors','performance_note_events','music_start','notated_music_end','duration','minimum_velocity','maximum_velocity']},indent=2))

if __name__=='__main__':main()
