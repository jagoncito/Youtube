#!/usr/bin/env python3
"""A new complete Beethoven op.13/II digital performance from verified notation.

One shared musical clock keeps both hands together. Persistent musical voices,
written articulations and explicit turn realizations govern note timing/voicing.
No finished performance recording or target video duration is an input.
"""
from pathlib import Path
import argparse,collections,hashlib,json,math
import numpy as np
import mido

QUARTERS=146
LEAD=.55
# Quarter-note BPM, chosen editorially for an unhurried, singing Adagio.
# The source's hidden q=36 is a transcription/playback choice, not presented
# here as an authenticated Beethoven metronome mark.
TEMPO=[(0,30.5),(2,31),(4,31.8),(6,30.9),(8,31.8),(10,32),(12,30.8),
 (14,29.5),(15,28),(15.75,29.5),(16,31.1),(18,31.5),(20,32.2),(22,31.1),
 (24,32.2),(26,32.5),(28,31),(30,29.8),(31.5,28.6),
 (32,32.1),(34,32.8),(36,33.6),(38,32.4),(39,31.3),(40,31.8),
 (41,30.8),(42,33),(44,31.8),(46,31.8),(48,31.2),(50,31.8),
 (52,30.5),(53.5,29),(54,28.6),(55.5,26.5),(56,30.4),
 (58,31),(60,31.5),(62,30.8),(64,31.5),(66,31.9),(68,30.7),
 (70,29.7),(71.5,28.6),(72,31),(74,31.5),(76,31.3),(78,31.9),
 (80,32.2),(82,33),(83,33.2),(84,33.6),(85,32.5),(86,31.8),
 (87.5,30.8),(88,30.8),(90,31.2),(92,31.5),(94,31.7),(96,32),
 (98,31.8),(99.5,29.5),(100,30.5),(102,31.1),(104,31.8),(106,30.9),
 (108,31.8),(110,32.1),(112,30.8),(114,29.8),(115.5,29.1),
 (116,31.2),(118,31.6),(120,32.2),(122,31.2),(124,32),(126,32.4),
 (128,30.6),(129.5,28.7),(130,29.8),(131.5,30.4),(132,31.4),
 (133,31),(134,29.8),(135.5,30.8),(136,31.6),(137,31),
 (138,29.8),(139,29),(140,28.5),(141,27.8),(142,27.4),(143,26.5),
 (144,25),(144.5,24.3),(145,20),(145.3,17),(146,15)]
# Phrase shape, not flat randomized velocities. Explicit sforzandi/fp below.
MELODY=[(0,61),(1,59),(2,64),(3.5,60),(4,61),(5,65),(5.5,67),
 (6,63),(7.5,62),(8,64),(9,61),(10,66),(11,62),(12,64),(13,68),
 (14,62),(15,57),(16,63),(17,60),(18,66),(19.5,62),(20,63),
 (21,67),(21.5,69),(22,65),(23.5,63),(24,66),(25,63),(26,68),
 (27,64),(28,65),(29,69),(30,62),(31.5,55),
 (32,62),(34,66),(36,70),(38,67),(39,64),(40,63),(41,60),
 (42,68),(43.5,64),(44,59),(46,63),(48,67),(50,71),
 (52,61),(53.75,66),(54.25,61),(55,54),(55.75,51),
 (56,60),(58,63),(60,64),(62,61),(64,63),(66,65),(68,62),
 (70,59),(71.5,56),(72,52),(74,54),(76,53),(78,55),(80,58),
 (81,66),(82,75),(83,77),(84,79),(85,72),(86,76),(86.17,45),
 (87.5,40),(88,51),(90,54),(92,53),(94,56),(96,60),(98,64),
 (99.5,67),(100,61),(102,64),(104,65),(106,62),(108,64),
 (110,66),(112,63),(114,60),(115.5,56),(116,63),(118,65),
 (120,67),(122,64),(124,66),(126,69),(128,64),(129.5,57),
 (130,50),(131.5,54),(132,58),(133,65),(133.8,57),
 (134,51),(135.5,58),(136,62),(136.8,68),(137.8,57),
 (138,50),(139,48),(140,46),(141,45),(142,43),(143,42),
 (144,38),(144.5,37),(145,36),(146,34)]
SECTIONS=[('Opening theme and written-out upper-register return',0,32),
 ('First contrasting episode',32,56),('Theme return',56,72),
 ('Second contrasting episode and sforzando climax',72,100),
 ('Theme with triplet accompaniment',100,130),('Coda and final fermata',130,146)]


def interp(points,x):
 return float(np.interp(x,[p[0] for p in points],[p[1] for p in points]))


def clock():
 q=np.linspace(0,QUARTERS,QUARTERS*2048+1)
 bpm=np.interp(q,[p[0] for p in TEMPO],[p[1] for p in TEMPO])
 # Restrained shared breathing at the two- and four-bar scale.
 bpm*=1+.005*np.sin(2*np.pi*q/8)+.002*np.sin(2*np.pi*q/2)
 t=np.zeros_like(q);t[1:]=np.cumsum((60/bpm[:-1]+60/bpm[1:])*.5*np.diff(q))
 return lambda x:float(np.interp(x,q,t)),float(t[-1])


def write_midi(spec,path):
 mid=mido.MidiFile(type=1,ticks_per_beat=1000)
 meta=mido.MidiTrack();mid.tracks.append(meta)
 meta.append(mido.MetaMessage('set_tempo',tempo=1000000,time=0))
 meta.append(mido.MetaMessage('track_name',name='Jagoncito Beethoven op.13 II new digital performance',time=0))
 track=mido.MidiTrack();mid.tracks.append(track);rows=[]
 for e in spec['events']:
  rows.extend([(round(e['start']*1000),2,mido.Message('note_on',note=e['pitch'],velocity=e['velocity'])),
   (round((e['start']+e['duration'])*1000),1,mido.Message('note_off',note=e['pitch'],velocity=0))])
 for e in spec['cc_events']:rows.append((round(e['time']*1000),0,mido.Message('control_change',control=e['cc'],value=e['value'])))
 last=0
 for tick,order,msg in sorted(rows,key=lambda x:(x[0],x[1])):
  msg.time=tick-last;track.append(msg);last=tick
 track.append(mido.MetaMessage('end_of_track',time=max(0,round(spec['duration']*1000)-last)))
 mid.save(path)


def main():
 p=argparse.ArgumentParser();p.add_argument('--score',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True);p.add_argument('--tail-seconds',type=float,default=1.756761)
 # Default buffer is the measured full-decay length for this rendering, not a video-duration target.
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 notes=json.loads((a.score/'mapped-midi-notes.json').read_text())
 source=json.loads((a.score/'source-events.json').read_text())
 srcaudit=json.loads((a.score/'score-validation.json').read_text())
 assert len(notes)==srcaudit['midi_onsets']==1629
 assert len({n['id'] for n in notes})==len(notes)
 assert srcaudit['quarter_beats']==QUARTERS and srcaudit['bars']==73
 at,music_duration=clock();music_end=LEAD+music_duration
 duration=math.ceil((music_end+a.tail_seconds)*24)/24
 arts=collections.defaultdict(set)
 for e in source:
  if e['kind']=='ART':arts[e['staff'],e['voice'],round(e['quarter'],6)].add(e['articulation'])
 groups=collections.defaultdict(list)
 for n in notes:groups[n['staff'],n['voice'],round(n['onset_quarter'],6)].append(n)
 # Turns are printed as glyph/text and therefore silent in baseline MIDI.
 # Resolve every glyph, including the explicit E-natural auxiliary in bar21.
 ornament_source=json.loads((a.score/'ornament-realization.json').read_text())
 turns=[]
 for written in ornament_source['turns']:
  attacks=written['new_attacks']
  turns.append({'bar':written['bar'],'principal_pitch':written['principal_pitch'],
   'principal_quarter':written['principal_onset_quarter'],
   'shorten_at_quarter':written['principal_end_quarter'],
   'quarters':[n['quarter'] for n in attacks], 'pitches':[n['pitch'] for n in attacks],
   'end_quarter':attacks[-1]['quarter']+attacks[-1]['duration_quarters']})
 assert len(turns)==3 and ornament_source['added_attacks']==12
 turn_principals={}
 for turn in turns:
  match=[n for n in notes if n['voice']=='melody' and n['pitch']==turn['principal_pitch'] and abs(n['onset_quarter']-turn['principal_quarter'])<1e-7]
  assert len(match)==1,turn
  turn['principal_source_id']=match[0]['id'];turn_principals[match[0]['id']]=turn
 events=[];grace_realizations=[]
 for n in notes:
  q=n['onset_quarter'];mq=n['main_quarter'];v=n['voice'];staff=n['staff'];pitch=n['pitch'];g=n['gate_quarters'];is_grace=n['grace_quarter']!=0
  bar=n['bar'];a_types=arts[staff,v,round(mq,6)]
  value=interp(MELODY,mq);chord=groups[staff,v,round(q,6)];top=max(x['pitch'] for x in chord)
  if staff=='upper' and v=='melody':
   role='melody';value-=4 if pitch<top else 0
   # In bar44 the written main voice becomes the soft repeated chord bed.
   if bar==44 and q>86.01:value=43-2*(q-86)
   if any(abs(mq-z)<1e-6 for z in [82,83,84]):value+=11
   if abs(mq-86)<1e-6:value=81 if pitch==top else 74
  elif staff=='upper':
   role='inner_accompaniment';value=value*.56+3
   if pitch==top and len(chord)>1:value+=1
   if bar in [24,26,27,28]:value+=7 # chromatic inner line retains its identity
   if bar==72 and q<143: value=43 # melody crosses through the second voice
  else:
   # Nested lower voice1 is the arpeggiated bed; voice2 is the long bass.
   role='bass' if v=='2' or (v=='' and (g>=.45 or pitch<48)) else 'lower_accompaniment'
   if role=='bass':value=value*.66+3
   else:value=value*.53+4
   if bar in [38,40,46]:
    role='lower_countermelody';value=interp(MELODY,mq)+1
   if bar in [42,43]:value=interp(MELODY,mq)*.59+2
   if pitch<40:value-=2
   if len(chord)>1 and pitch<top:value-=2
   if bar==69:
    # Written crescendo/decrescendo belongs to the repeated lower chords.
    value+=8*max(0,1-abs(q-136.85)/.9)
  if is_grace:value-=8
  # Preserve the small written rinforzando gestures in the coda. The first
  # is attached to bar70's grace; bars71/72 mark the principal after it.
  if (bar==70 and is_grace) or (v=='melody' and not is_grace and any(abs(q-z)<1e-7 for z in [141,143])):
   value+=8
  if staff=='upper' and v=='accompaniment':
   if 52.25<=q<=53.75:value+=4*(q-52.25)/1.5
   if 54.25<=q<=55.75:value-=4*(q-54.25)/1.5
   if 80.5<=q<82:value+=4*(q-80.5)/1.5
  if 'staccato' in a_types:value-=1
  # A tiny deterministic color variation, not random timing/dynamic jitter.
  value+=.65*math.sin(q*1.41+pitch*.13)
  if role in ['inner_accompaniment','lower_accompaniment']:
   value+=1.0*math.cos(2*math.pi*q) # gentle pulse hierarchy
  velocity=max(25,min(94,round(value)))
  factor=1.009 if role in ['melody','lower_countermelody'] else .965
  if role=='bass':factor=.983
  if 'staccato' in a_types:factor=.53
  if 'fermata' in a_types:factor=1.
  endq=min(QUARTERS,q+g*factor)
  if n['id'] in turn_principals:endq=turn_principals[n['id']]['shorten_at_quarter']
  delay=(.010+.003*math.sin(q*.7)) if role=='melody' else 0.
  start=LEAD+at(q)+delay;end=LEAD+at(endq)+delay
  if is_grace:
   # The three unslashed notes in bar22 form a brief, shaped lead-in.
   if bar==22:
    peers=sorted([z for z in notes if z['grace_quarter'] and z['bar']==22],key=lambda z:z['grace_quarter'])
    k=[z['id'] for z in peers].index(n['id']);offsets=[-.180,-.119,-.060]
    start=LEAD+at(mq)+offsets[k];end=start+[.058,.056,.057][k]
   else:
    # Slashed single acciaccaturas are quick, before the principal beat.
    start=LEAD+at(mq)-.092;end=LEAD+at(mq)-.008
   grace_realizations.append({'source_id':n['id'],'bar':bar,'pitch':pitch,
    'seconds_before_principal':round(LEAD+at(mq)-start,6),'duration_seconds':round(end-start,6)})
  events.append({'start':round(start,6),'duration':round(max(.02,end-start),6),
   'pitch':pitch,'velocity':velocity,'part':role,'source_id':n['id'],
   'source_quarter':q,'main_quarter':mq,'voice':v,'visual_staff':staff,'bar':bar,
   'grace':is_grace,'written_turn_realization':False,'articulations':sorted(a_types)})
 for turn in turns:
  for k,(q,pitch) in enumerate(zip(turn['quarters'],turn['pitches'])):
   nextq=turn['quarters'][k+1] if k<3 else turn['end_quarter']
   value=interp(MELODY,q)-3+[0,-1,-2,0][k]
   start=LEAD+at(q)+.010;end=LEAD+at(nextq)+.006
   events.append({'start':round(start,6),'duration':round(end-start,6),
    'pitch':pitch,'velocity':round(value),'part':'melody_ornament','source_id':None,
    'derived_from_source_id':turn['principal_source_id'],'ornament_id':f"turn-bar{turn['bar']}-{k+1}",
    'source_quarter':q,'main_quarter':q,'voice':'melody','visual_staff':'upper',
    'bar':turn['bar'],'grace':False,'written_turn_realization':True,'articulations':[]})
 # Prevent a single physical piano key overlapping its own following attack.
 same=collections.defaultdict(list);gates_cleaned=[]
 for e in events:same[e['pitch']].append(e)
 for es in same.values():
  es.sort(key=lambda e:e['start'])
  for old,new in zip(es,es[1:]):
   if abs(old['start']-new['start'])<.001:
    raise RuntimeError(f'Unresolved simultaneous physical-key unison: {old} {new}')
   if old['start']+old['duration']>new['start']-.004:
    previous=old['duration'];old['duration']=round(max(.012,new['start']-.004-old['start']),6)
    gates_cleaned.append({'source_id':old['source_id'],'pitch':old['pitch'],'old_gate_seconds':previous,'new_gate_seconds':old['duration']})
 # All sustain is editorial: the chosen source contains no pedal marks.
 assert not [e for e in source if e['kind']=='PEDAL']
 boundaries=set(float(q) for q in np.arange(0,146,1.))
 # Explicit faster harmonic rhythm / chromatic bass / coda.
 for lo,hi in [(32,44),(46,52),(72,100),(130,144)]:
  boundaries.update(float(q) for q in np.arange(lo,hi,.5))
 for n in notes:
  if n['staff']=='lower' and n['pitch']<49 and n['gate_quarters']>=.45:boundaries.add(float(n['main_quarter']))
 pedal=[{'time':0.,'cc':64,'value':0,'origin':'initial_release'}]
 for q in sorted(boundaries):
  if q>=145:continue
  t=LEAD+at(q)
  if q>0:pedal.append({'time':round(t+.018,6),'cc':64,'value':0,'source_quarter':q,'origin':'editorial_harmonic_renewal'})
  pedal.append({'time':round(t+.082,6),'cc':64,'value':127,'source_quarter':q,'origin':'editorial_harmonic_renewal'})
 # Last written staccato-like separated notes lead to a fully held fermata.
 for q in [144.25,144.75]:
  pedal.append({'time':round(LEAD+at(q),6),'cc':64,'value':0,'source_quarter':q,'origin':'editorial_final_written_rest_clearance'})
 pedal.append({'time':round(LEAD+at(145)+.082,6),'cc':64,'value':127,'source_quarter':145,'origin':'final_fermata_chord'})
 pedal.append({'time':round(music_end+.045,6),'cc':64,'value':0,'origin':'final_fermata_release'})
 pedal.sort(key=lambda e:(e['time'],e['value']));events.sort(key=lambda e:(e['start'],e['pitch']))
 anchors={e['source_id']:e for e in events if e['source_id'] is not None}
 assert set(anchors)=={n['id'] for n in notes}
 assert all(anchors[n['id']]['pitch']==n['pitch'] for n in notes)
 assert len(events)==len(notes)+12
 assert all(0<=e['start']<e['start']+e['duration']<duration for e in events)
 assert all(21<=e['pitch']<=108 for e in events)
 spec={'schema':'jagoncito-piano-performance/2','sample_rate':48000,'duration':duration,
  'music_start':LEAD,'notated_music_end':music_end,'notated_quarters':QUARTERS,'bars':73,
  'work':'Ludwig van Beethoven: Piano Sonata No.8 op.13, II. Adagio cantabile',
  'tempo_unit':'quarter note','tempo_points_bpm':TEMPO,'melody_velocity_points':MELODY,
  'clock_breathing':{'four_bar_fraction':.005,'one_bar_fraction':.002},
  'source_note_anchors':len(notes),'written_turns':turns,'written_grace_realizations':grace_realizations,
  'source_sections':[{'label':label,'start_quarter':lo,'end_quarter':hi,
    'start_seconds':LEAD+at(lo),'end_seconds':LEAD+at(hi)} for label,lo,hi in SECTIONS],
  'events':events,'cc_events':pedal,
  'notes':['All 1629 compiled-source physical pitch anchors are preserved, including six written grace notes.',
   'All three printed turn glyphs receive an explicit four-note realization; 12 derived attacks are separately identified.',
   'The principal turn notes are shortened to accommodate the written ornament, with no removal of their pitch anchor.',
   'The final fermata is expressed in the shared tempo curve and held piano keys, without cutting the last bar.',
   'Voicing follows melody/accompaniment roles, with explicit lower-voice counter-lines and bar44 texture change.',
   'Sforzandi at bars42-43, forte-piano at44 and rinforzando gestures at70-72 are retained as local attacks, not globally flattened.',
   'No pedal marks occur in the chosen transcription: CC64 renewals and clearance during final rests are editorial.',
   'The original piano uses switch sustain; no continuous half-pedal physics or separately recorded una-corda is claimed.',
   'No subjective audition performed; source fidelity is to the selected digital transcription, not an independent historical collation.']}
 (a.out/'performance.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
 write_midi(spec,a.out/'interpretacion-digital.midi')
 audit={'status':'passed','source_note_anchors':len(notes),'preserved_source_ids':len(anchors),
  'performance_note_events':len(events),'unexplained_added_notes':0,'written_turn_derived_attacks':12,
  'notes_by_persistent_voice':dict(collections.Counter(n['staff']+':'+n['voice'] for n in notes)),
  'source_grace_notes':len(grace_realizations),'written_grace_realizations':grace_realizations,
  'written_turn_realizations':turns,'explicit_source_pedal_marks':0,
  'editorial_pedal_renewal_count':len(boundaries),'pedal_control_events':len(pedal),
  'same_key_finger_gate_shortening':gates_cleaned,'final_pedal_value':pedal[-1]['value'],
  'music_start':LEAD,'notated_music_end':music_end,'duration':duration,
  'minimum_velocity':min(e['velocity'] for e in events),'maximum_velocity':max(e['velocity'] for e in events),
  'source_sha256':{name:hashlib.sha256((a.score/name).read_bytes()).hexdigest() for name in ['partitura.midi','source-events.json','mapped-midi-notes.json','ornament-realization.json']},
  'scope':'Complete selected-transcription anchors, turn/grace realization, physical note gates, voicing and pedal; no subjective audition.'}
 (a.out/'performance-validation.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:audit[k] for k in ['status','source_note_anchors','performance_note_events','notated_music_end','duration','minimum_velocity','maximum_velocity','pedal_control_events']},indent=2))

if __name__=='__main__':main()
