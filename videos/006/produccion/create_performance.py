#!/usr/bin/env python3
"""New expressive Clair de lune performance from the pinned, verified score.

Four persistent voices survive cross-staff writing. No audio recording is an
input, no new melody or unnotated ornament is added. Musical phrasing, not a
video-length target, determines the clock. All 1494 source anchors survive.
"""
from pathlib import Path
import argparse,collections,hashlib,json,math
import numpy as np
import mido

QUARTERS=324
LEAD=.60
# Quarter-note BPM: 9/8 dotted-quarter pulse is this number divided by 1.5.
TEMPO=[(0,58),(4.5,60),(9,60),(13.5,59),(18,61),(22.5,62),(27,60),
 (31.5,59),(36,60.5),(40.5,61),(45,61.5),(49.5,60.5),(54,63),(58.5,56),
 (63,55),(67.5,57),(72,55),(76.5,58),(81,62),(85.5,63.5),(90,62),
 (94.5,65),(99,67),(103.5,69),(108,58),(112.5,53),(116.5,47),
 (117,70),(121.5,70),(126,72),(130.5,70),(135,69),(139.5,70),
 (144,70.5),(148.5,71),(153,73),(157.5,74),
 (162,78),(166.5,79),(171,80),(175.5,81),(180,78),(184.5,72),
 (189,63),(193.5,63),(198,64),(202.5,64),(207,66),(211.5,65),
 (216,64),(220.5,58),(224.5,51),(225,57),(229.5,58),(234,59),
 (238.5,58),(243,60),(247.5,60.5),(252,61),(256.5,60),(261,58),
 (265.5,58),(270,59),(274.5,56),(279,55),(283.5,54),(288,52),
 (292.5,50),(297,49),(301.5,48),(306,47),(310.5,44),(315,43),
 (319.5,38),(324,32)]
# Phrase-level upper melody, with source hairpins refining local motion.
MELODY=[(0,56),(4.5,57),(9,59),(13.5,56),(18,59),(22.5,60),(27,58),
 (31.5,57),(36,59),(40.5,60),(45,60),(49.5,58),(54,64),(58.5,56),
 (63,52),(67.5,53),(72,54),(76.5,55),(81,58),(85.5,61),(90,62),
 (94.5,66),(99,69),(103.5,73),(108,56),(111,53),(112.5,51),(115.5,48),
 (117,57),(121.5,58),(126,63),(130.5,60),(135,59),(139.5,60),
 (144,64),(148.5,65),(153,68),(157.5,70),(162,73),(166.5,77),
 (171,80),(175.5,82),(180,87),(184.5,77),(188.5,64),(189,54),
 (193.5,54),(198,57),(202.5,55),(207,57),(211.5,56),(216,56),
 (220.5,52),(225,44),(229.5,45),(234,48),(238.5,47),(243,52),
 (247.5,53),(252,54),(256.5,52),(261,52),(265.5,53),(270,55),
 (274.5,50),(279,48),(283.5,47),(288,45),(292.5,40),(297,39),
 (301.5,37),(306,36),(310.5,35),(315,34),(319.5,32),(324,28)]


def interp(points,x):
 return float(np.interp(x,[p[0] for p in points],[p[1] for p in points]))


def clock():
 q=np.linspace(0,QUARTERS,QUARTERS*2048+1)
 bpm=np.interp(q,[p[0] for p in TEMPO],[p[1] for p in TEMPO])
 # Shared, restrained phrase breathing, never independent drifting hands.
 bpm*=1+.006*np.sin(2*np.pi*q/18)+.003*np.sin(2*np.pi*q/4.5)
 t=np.zeros_like(q);t[1:]=np.cumsum((60/bpm[:-1]+60/bpm[1:])*.5*np.diff(q))
 return lambda x:float(np.interp(x,q,t)),float(t[-1])


def slurs(source):
 out=[];active={}
 for e in source:
  if e['kind'] not in ('SLUR','PHRASE'):continue
  key=e['voice'],e['kind'];q=e['quarter']
  if e['direction']==-1:active[key]=q
  elif key in active:out.append((e['voice'],active.pop(key),q))
 return out


def hairpins(source):
 out=[];active={}
 for e in source:
  if e['kind'] not in ('CRESCENDO','DECRESCENDO','DYNAMIC'):continue
  voice=e['voice'];q=e['quarter']
  if e['kind']=='DYNAMIC':
   if voice in active:out.append((active.pop(voice),q))
  elif e['direction']==1:
   if voice in active:out.append((active.pop(voice),q))
  else:
   if voice in active:out.append((active.pop(voice),q))
   active[voice]=e
 for e in active.values():out.append((e,min(QUARTERS,e['quarter']+4.5)))
 return [(e,end) for e,end in out if end>e['quarter']]


def write_midi(spec,path):
 mid=mido.MidiFile(type=1,ticks_per_beat=1000)
 meta=mido.MidiTrack();mid.tracks.append(meta)
 meta.append(mido.MetaMessage('set_tempo',tempo=1000000,time=0))
 meta.append(mido.MetaMessage('track_name',name='Jagoncito Debussy Clair de lune digital performance',time=0))
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
 p.add_argument('--out',type=Path,required=True)
 p.add_argument('--tail-seconds',type=float,default=1.537465)
 a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 # Default tail was measured from this piano/score's release, not selected to fit a video duration.
 # A longer exploratory --tail-seconds is allowed; the master remeasures decay.
 notes=json.loads((a.score/'mapped-midi-notes.json').read_text())
 source=json.loads((a.score/'source-events.json').read_text())
 srcaudit=json.loads((a.score/'score-validation.json').read_text())
 assert len(notes)==srcaudit['midi_onsets']==1494
 assert len({n['id'] for n in notes})==len(notes)
 assert srcaudit['quarter_beats']==QUARTERS and srcaudit['bars']==72
 at,music_duration=clock();music_end=LEAD+music_duration
 duration=math.ceil((music_end+a.tail_seconds)*24)/24
 arts=collections.defaultdict(set)
 for e in source:
  if e['kind']=='ART':arts[e['voice'],round(e['quarter'],6)].add(e['articulation'])
 phrasing=slurs(source);hps=hairpins(source)
 groups=collections.defaultdict(list)
 for n in notes:groups[n['voice'],round(n['onset_quarter'],6)].append(n)
 # LilyPond exports marked arpeggio chords as simultaneous MIDI notes.
 # Realize only the written voices; do not spread unrelated melody notes.
 arpvoices=collections.defaultdict(set)
 for e in source:
  if e['kind']=='ARPEGGIO':arpvoices[round(e['quarter'],6)].add(e['voice'])
 arpdeltas={};arpreport=[]
 for q,voices in sorted(arpvoices.items()):
  members=[n for n in notes if abs(n['main_quarter']-q)<1e-7 and n['voice'] in voices]
  members.sort(key=lambda n:n['pitch'])
  span=.12 if len(members)>=7 else .095
  for k,n in enumerate(members):arpdeltas[n['id']]=span*k/max(1,len(members)-1)
  arpreport.append({'quarter':q,'bar':int(q/4.5)+1,'voices':sorted(voices),
    'pitches_low_to_high':[n['pitch'] for n in members],'span_seconds':span,
    'source_ids':[n['id'] for n in members]})
 events=[]
 for n in notes:
  q=n['onset_quarter'];mq=n['main_quarter'];v=n['voice'];key=round(q,6)
  pitch=n['pitch'];g=n['gate_quarters'];is_grace=n['grace_quarter']!=0
  slurred=any(voice==v and lo<=mq<hi for voice,lo,hi in phrasing)
  a_types=arts[v,round(mq,6)]
  factor=1.008 if slurred else .993
  if 'tenuto' in a_types:factor=1.012
  endq=min(QUARTERS,q+g*factor)
  value=interp(MELODY,mq)
  chord=groups[v,key];top=max(x['pitch'] for x in chord)
  if v=='red':
   if pitch<top:value-=5
   if q<1 and n['staff']=='lower':value-=6
   if 189<=mq<207:value-=5 # Calmato's moving green voice is heard through red pads.
  elif v=='green':
   if 189<=mq<207:value+=3
   elif mq>=315:value-=1 # final rolled upper chord, not a hidden accompaniment
   else:value-=12
   if pitch<top:value-=4
  elif v=='blue':
   value=value*.70+1
   if len(chord)>1 and pitch==top:value+=2
   if mq>=292.5:value=max(27,value+4) # coda arpeggios carry the music when red rests
   if abs(q%1.5)<.006:value+=1
  elif v=='grey':
   value=value*.66
   if pitch<48:value+=2
   if 207<=mq<225:value+=5 # quiet low counter-line beneath the late arpeggios
  if is_grace:value-=6
  for hp,end in hps:
   if hp['voice']==v and hp['quarter']<=mq<end:
    z=(mq-hp['quarter'])/(end-hp['quarter'])
    value+=(-3 if hp['kind']=='DECRESCENDO' else 3)*z
  if 'accent' in a_types:value+=4
  # Deterministic, tiny intra-phrase accent; dynamics are score/voice-led.
  value+=.6*math.sin(mq*1.39+pitch*.11)
  velocity=max(25,min(94,round(value)))
  delay=0.
  if v=='red':delay=.010+.004*math.sin(q*.6)
  elif v=='green' and 189<=q<207:delay=.009
  if is_grace:delay=-.003
  if n['id'] in arpdeltas:delay=arpdeltas[n['id']]
  start=LEAD+at(q)+delay;end=LEAD+at(endq)+delay
  events.append({'start':round(start,6),'duration':round(max(.025,end-start),6),
    'pitch':pitch,'velocity':velocity,'part':v,'source_id':n['id'],
    'source_quarter':q,'main_quarter':mq,'voice':v,'visual_staff':n['staff'],
    'bar':n['bar'],'grace':is_grace,'written_arpeggio':n['id'] in arpdeltas})
 # One physical key cannot overlap its own restrike; damper carries the resonance.
 same=collections.defaultdict(list);gates_cleaned=0
 for e in events:same[e['pitch']].append(e)
 for es in same.values():
  es.sort(key=lambda e:e['start'])
  for old,new in zip(es,es[1:]):
   if old['start']+old['duration']>new['start']-.004:
    old['duration']=round(max(.015,new['start']-.004-old['start']),6);gates_cleaned+=1
 # The chosen edition has no actual sustain marks. This is an explicit editorial
 # harmonic pedal realization, not a claim that unused LilyPond macros are marks.
 assert not [e for e in source if e['kind']=='PEDAL']
 boundaries={0.5}
 boundaries.update(float(q) for q in np.arange(4.5,QUARTERS,4.5))
 # Moving harmonies in arpeggio sections renew each dotted-quarter group.
 for lo,hi in [(117,225),(292.5,319.5)]:
  boundaries.update(float(q) for q in np.arange(lo,hi,1.5))
 # Low written bass changes add harmonic renewals in the chordal introduction.
 for n in notes:
  if n['voice']=='grey' and n['pitch']<60 and n['gate_quarters']>=.45:
   boundaries.add(float(n['main_quarter']))
 boundaries.update(arpvoices.keys())
 pedal=[{'time':0.,'cc':64,'value':0,'origin':'initial_release'}]
 for q in sorted(boundaries):
  if q<.5 or q>=QUARTERS:continue
  t=LEAD+at(q)
  if q>.5:pedal.append({'time':round(max(0,t-.012),6),'cc':64,'value':0,'source_quarter':q,'origin':'editorial_harmonic_renewal'})
  pedal.append({'time':round(t+.055,6),'cc':64,'value':127,'source_quarter':q,'origin':'editorial_harmonic_renewal'})
 # Preserve the written final dotted-quarter rest and let its chord decay through
 # it; release the editorial damper at the close of the complete final bar.
 pedal.append({'time':round(music_end+.02,6),'cc':64,'value':0,'origin':'final_bar_release'})
 pedal.sort(key=lambda e:(e['time'],e['value']));events.sort(key=lambda e:(e['start'],e['pitch']))
 ids={e['source_id'] for e in events}
 assert ids=={n['id'] for n in notes}
 byid={e['source_id']:e for e in events}
 assert all(byid[n['id']]['pitch']==n['pitch'] for n in notes)
 assert len(events)==len(notes) and all(0<=e['start']<e['start']+e['duration']<duration for e in events)
 assert all(21<=e['pitch']<=108 for e in events)
 spec={'schema':'jagoncito-piano-performance/1','sample_rate':48000,'duration':duration,
  'music_start':LEAD,'notated_music_end':music_end,'notated_quarters':QUARTERS,
  'bars':72,'work':'Claude Debussy: Clair de lune, Suite bergamasque III',
  'tempo_unit':'quarter note','tempo_points_bpm':TEMPO,'melody_velocity_points':MELODY,
  'source_note_anchors':len(notes),'events':events,'cc_events':pedal,
  'notes':['Every compiled-source pitch anchor preserved; no notes or unnotated ornaments added.',
   'Persistent red/green/blue/grey voices guide voicing despite cross-staff notation.',
   'Written rolled chords receive a documented short upward spread only in marked voices.',
   'The digital edition has no explicit pedal marks: all damper renewals are editorial harmonic decisions.',
   'Final written rest is retained; damper releases after the complete final bar.',
   'Con sordina is approached by restrained low-velocity sample layers; no physical una-corda model is claimed.',
   'No subjective audition performed; note/score fidelity is to the chosen digital transcription.']}
 (a.out/'performance.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
 write_midi(spec,a.out/'interpretacion-digital.midi')
 audit={'status':'passed','source_note_anchors':len(notes),'preserved_source_ids':len(ids),
  'performance_note_events':len(events),'notes_added':0,
  'notes_by_persistent_voice':dict(collections.Counter(n['voice'] for n in notes)),
  'grace_note_anchors':sum(n['grace_quarter']!=0 for n in notes),'written_arpeggio_realizations':arpreport,
  'explicit_source_pedal_marks':0,'editorial_pedal_renewal_count':len(boundaries),
  'pedal_control_events':len(pedal),'same_key_finger_gates_cleaned':gates_cleaned,
  'final_pedal_value':pedal[-1]['value'],'music_start':LEAD,'notated_music_end':music_end,
  'duration':duration,'minimum_velocity':min(e['velocity'] for e in events),
  'maximum_velocity':max(e['velocity'] for e in events),
  'source_sha256':{name:hashlib.sha256((a.score/name).read_bytes()).hexdigest() for name in ['partitura.midi','source-events.json','mapped-midi-notes.json']},
  'scope':'Digital score coverage, physical note gates, voicing and pedal checks; no historical-facsimile collation or subjective audition.'}
 (a.out/'performance-validation.json').write_text(json.dumps(audit,indent=2)+'\n')
 print(json.dumps({k:audit[k] for k in ['status','source_note_anchors','performance_note_events','notated_music_end','duration','minimum_velocity','maximum_velocity','pedal_control_events']},indent=2))

if __name__=='__main__':main()
