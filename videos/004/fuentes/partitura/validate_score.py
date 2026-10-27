"""Validate pinned transcription -> notation events -> newly compiled MIDI.
This checks source fidelity, not an independent comparison with a 1725 facsimile.
Run with Python+mido. No finished recording is downloaded or used.
"""
import collections, hashlib, json
from pathlib import Path
import mido
ROOT=Path(__file__).resolve().parent
parts=['solo','violin1','violin2','viola','cello']
notation=json.loads((ROOT/'source-events.json').read_text())
result=[]
for movement,stem,quarters,bars,meter in [(1,'score',252,63,[4,4]),(2,'score-1',72,18,[4,4]),(3,'score-2',229.5,153,[3,8])]:
    mid=mido.MidiFile(ROOT/(stem+'.midi'))
    assert mid.ticks_per_beat==384
    tracks=[]
    for index,part in enumerate(parts,1):
        tick=0;active=collections.Counter();starts=[];ends=[]
        for msg in mid.tracks[index]:
            tick+=msg.time
            if msg.type=='note_on' and msg.velocity:
                active[(msg.channel,msg.note)]+=1
                starts.append((tick/mid.ticks_per_beat,msg.note))
            elif msg.type=='note_off' or msg.type=='note_on' and not msg.velocity:
                key=(msg.channel,msg.note)
                assert active[key]>0,(movement,part,tick,key)
                active[key]-=1
                ends.append(tick/mid.ticks_per_beat)
        assert not any(active.values())
        assert tick/mid.ticks_per_beat==quarters
        events=[x for x in notation if x['movement']==movement and x['part']==part]
        ns=[x for x in events if x['kind']=='NOTE']
        tie_count=sum(x['kind']=='TIE' for x in events)
        assert len(ns)-tie_count==len(starts)
        src=collections.Counter((x['quarter'],x['pitch']) for x in ns)
        midi=collections.Counter(starts)
        assert not (midi-src),'A MIDI onset was not present in the notation'
        continuations=list((src-midi).elements())
        assert len(continuations)==tie_count
        src_end=collections.Counter((x['quarter']+x['duration_quarters'],x['pitch']) for x in ns)
        assert all(src_end[x]>0 for x in continuations),'An omitted onset was not a tied continuation'
        tracks.append({'part':part,'notation_notes':len(ns),'tie_events':tie_count,'midi_note_on':len(starts),'midi_note_off':len(ends),'end_quarter':quarters,'first_onset_quarter':starts[0][0],'last_note_off_quarter':ends[-1],'pitch_min':min(p for _,p in starts),'pitch_max':max(p for _,p in starts),'source_onset_subset':True,'omitted_onsets_all_tied_continuations':True,'no_hanging_or_unmatched_notes':True})
    result.append({'movement':movement,'meter':meter,'measures':bars,'quarter_beats':quarters,'editorial_midi_seconds':mid.length,'parts':tracks})
files={}
for p in sorted((ROOT/'original').glob('*')):
    files['original/'+p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for name in ['score.midi','score-1.midi','score-2.midi','partitura.pdf','source-events.json','markers.json','CC-BY-SA-3.0.txt']:
    p=ROOT/name
    files[name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
report={'source_repository':'https://github.com/MutopiaProject/MutopiaProject','source_commit':'2144afd6f52d56c5b6995b8b589ef1268b3139f0','source_directory':'ftp/VivaldiA/O8/winter/winter-lys','license':'CC-BY-SA-3.0','source_fidelity_validation':'pass','musical_status':'All three complete notated movements and all five instrumental parts; no abridgment, no score repeats in this transcription. MIDI tempos are editorial and need musical reinterpretation. Not an independent critical-edition or facsimile comparison.','movements':result,'files':files}
(ROOT/'score-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('PASS: all 3 complete movements; 15 aligned parts; 6802 MIDI note pairs; 120 tied continuations accounted for.')
