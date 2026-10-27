#!/usr/bin/env python3
"""Create a complete Satie 1+3 performance, using verified CC0 piano samples.

The output is one six-minute 44.1-kHz stereo PCM16 WAV. No recording of the
works is incorporated. Samples stay outside the checkout. Requires FFmpeg.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request
import warnings

import mido
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
HERE = Path(__file__).resolve().parent
TOTAL = 360
WORKS = [
    dict(number=1, quarters=234, seconds=190, bars=78,
         phrase_ends=[36, 63, 93, 117, 153, 180, 210, 234]),
    dict(number=3, quarters=180, seconds=170, bars=60,
         phrase_ends=[39, 60, 81, 120, 144, 165, 180]),
]


def read_score(path):
    midi = mido.MidiFile(path)
    result = []
    roles = {1: 'melody', 2: 'harmony', 3: 'bass'}
    for track_id, track in enumerate(midi.tracks):
        tick = 0
        active = defaultdict(deque)
        for event in track:
            tick += event.time
            q = tick / midi.ticks_per_beat
            if event.type == 'note_on' and event.velocity:
                active[(event.channel, event.note)].append((q, event.velocity))
            elif event.type in ('note_off', 'note_on'):
                key = (event.channel, event.note)
                if not active[key]:
                    raise ValueError(f'Unmatched note-off: {path.name} {key}')
                start, velocity = active[key].popleft()
                result.append(dict(pitch=event.note, start=start, end=q,
                                   written_velocity=velocity,
                                   role=roles[track_id]))
        if any(active.values()):
            raise ValueError(f'Unclosed notes: {path.name}')
    return sorted(result, key=lambda n: (n['start'], n['pitch'], n['role']))


def verify_and_load_samples(folder):
    folder.mkdir(parents=True, exist_ok=True)
    entries = json.loads((HERE/'instrumento-vsco-fuentes.json').read_text())['samples']
    samples = {}
    for entry in entries:
        path = folder / entry['filename']
        if not path.exists():
            with urllib.request.urlopen(entry['source'], timeout=120) as response:
                path.write_bytes(response.read())
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise RuntimeError(f'SHA-256 mismatch: {path.name}')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', wavfile.WavFileWarning)
            rate, raw = wavfile.read(path)
        assert rate == SR and raw.ndim == 2 and raw.shape[1] == 2
        data = raw.astype(np.float32) / 2147483648.0
        data -= data[-min(len(data), SR):].mean(axis=0, keepdims=True)
        data[:44] *= np.linspace(0, 1, 44, dtype=np.float32)[:, None]
        # Preserve the recorded natural decay; remove only the last tiny edge.
        fade = min(2205, len(data)//10)
        data[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]
        samples[(entry['root_midi'], entry['layer'])] = data
    return samples


def make_piano(samples):
    roots = sorted(set(k[0] for k in samples))
    cache = {}
    def play(pitch, velocity):
        if pitch not in cache:
            root = min(roots, key=lambda n: abs(n-pitch))
            ratio = Fraction(2**(-(pitch-root)/12)).limit_denominator(3000)
            layers = [signal.resample_poly(samples[(root, layer)],
                       ratio.numerator, ratio.denominator, axis=0).astype(np.float32)
                      for layer in (1, 2)]
            length = max(map(len, layers))
            cache[pitch] = tuple(np.pad(a, ((0, length-len(a)), (0, 0))) for a in layers)
        soft, medium = cache[pitch]
        amount = float(np.clip((velocity-48)/53, 0, .43))
        gain = float(np.clip((velocity/61)**1.35, .35, 1.3))
        return ((1-amount)*soft + amount*medium)*gain
    return play


def make_timing(work):
    q = np.linspace(0, work['quarters'], work['quarters']*500+1)
    stretch = 1 + .014*np.sin(2*np.pi*q/27) + .008*np.sin(2*np.pi*q/11+.8)
    # Broad phrase breathing, rather than beat-by-beat mechanical wobble.
    for end in work['phrase_ends']:
        stretch += .065*np.exp(-((q-(end-.75))/1.6)**2)
    stretch += .16*np.clip((q-(work['quarters']-9))/9, 0, 1)**1.4
    dt = (stretch[1:]+stretch[:-1])*.5*np.diff(q)
    seconds = np.concatenate(([0.0], np.cumsum(dt)))
    score_seconds = work['seconds'] - 5.6
    seconds *= score_seconds/seconds[-1]
    timing = lambda quarter: np.interp(quarter, q, seconds)
    actual_bpm = 60/np.gradient(seconds, q)
    return timing, dict(mean_quarter_bpm=round(work['quarters']/score_seconds*60, 3),
                        minimum_quarter_bpm=round(float(actual_bpm.min()), 3),
                        maximum_quarter_bpm=round(float(actual_bpm.max()), 3),
                        score_seconds=round(score_seconds, 3))


def room(audio):
    # An original, restrained stereo room; no downloaded impulse response.
    rng = np.random.default_rng(1888)
    n = int(SR*1.6)
    t = np.arange(n, dtype=np.float32)/SR
    ir = rng.standard_normal((n, 2), dtype=np.float32)
    ir = signal.sosfilt(signal.butter(2, 3600, fs=SR, output='sos'), ir, axis=0)
    ir *= np.exp(-6.9*t/1.35)[:, None]
    ir[:int(SR*.035)] = 0
    ir *= .09/np.sqrt(np.sum(ir[:, 0]**2))
    for delay, amplitude in ((.024, .055), (.041, .041), (.067, .025), (.093, .014)):
        ir[int(delay*SR), 0] += amplitude
        ir[int((delay+.003)*SR), 1] += amplitude*.92
    for ch in range(2):
        audio[:, ch] += signal.oaconvolve(audio[:, ch], ir[:, ch])[:len(audio)]
    return audio


def render_work(work, notes, piano):
    rng = np.random.default_rng(188800+work['number'])
    timing, tempo_info = make_timing(work)
    out = np.zeros((work['seconds']*SR, 2), dtype=np.float32)
    for event in notes:
        start, end, role = event['start'], event['end'], event['role']
        # Syncopated pedal catches each harmony, then clears on the next bass.
        pedal_off = min(work['quarters'], np.ceil((end-1e-7)/3)*3)
        held = max(end, pedal_off)
        t0 = .4+float(timing(start))
        t0 += .008 if role == 'melody' else 0
        t0 += rng.normal(0, .0028)
        if role == 'harmony':
            t0 += .00034*(event['pitch']-48)
        t1 = .4+float(timing(held))+.035
        bar = start/3
        phrase = 1.8*np.sin(2*np.pi*bar/13-.8)+.8*np.sin(2*np.pi*bar/7)
        source = event['written_velocity']
        if role == 'melody':
            velocity = 52+(source-62)*.34+phrase
        elif role == 'harmony':
            velocity = 39+(source-62)*.28+phrase*.5
        else:
            velocity = 45+phrase*.65
        # Let final ensemble chords settle instead of doubling melody volume.
        if start >= work['quarters']-6:
            velocity = (42 if role == 'melody' else 38)+phrase*.3
        velocity += rng.normal(0, .7)
        tone = piano(event['pitch'], velocity)
        hold = max(.05, t1-t0)
        release = .6 if held > end else .38
        if end == work['quarters']:
            release = 4.4
        use = min(len(tone), int((hold+release)*SR))
        tone = tone[:use].copy()
        release_start = min(use, int(hold*SR))
        if release_start < use:
            rt = np.arange(use-release_start, dtype=np.float32)/SR
            tone[release_start:] *= np.exp(-6.9*rt/release)[:, None]
        # Keep source stereo image and use a narrow, natural keyboard spread.
        balance = float(np.clip((event['pitch']-60)/44, -.6, .6))
        tone[:, 0] *= 1-.10*balance
        tone[:, 1] *= 1+.10*balance
        first = max(0, int(t0*SR))
        count = min(len(tone), len(out)-first)
        if count > 0:
            out[first:first+count] += tone[:count]
    out = signal.sosfilt(signal.butter(2, 24, fs=SR, btype='highpass', output='sos'),
                         out, axis=0).astype(np.float32)
    out = room(out)
    # The final written chord has already completed. Fade only its quiet tail.
    fade = int(1.3*SR)
    out[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]**1.3
    tempo_info.update(notes=len(notes), bars=work['bars'], quarters=work['quarters'],
                      midi=Path(f"gymnopedie-{work['number']}.midi").name,
                      pitch_range_midi=[min(e['pitch'] for e in notes), max(e['pitch'] for e in notes)],
                      notes_by_role={r:sum(e['role']==r for e in notes)
                                     for r in ('melody', 'harmony', 'bass')})
    return out, tempo_info


def make_rain(length, music_rms):
    rng = np.random.default_rng(3191888)
    overlap, warmup = SR, SR
    n = length+overlap
    mono = rng.standard_normal(n+warmup, dtype=np.float32)
    side = rng.standard_normal(n+warmup, dtype=np.float32)
    sos = signal.butter(2, (780, 4900), btype='bandpass', fs=SR, output='sos')
    mono = signal.sosfilt(sos, mono)[warmup:].astype(np.float32)
    side = signal.sosfilt(sos, side)[warmup:].astype(np.float32)
    rain = np.column_stack((mono+.20*side, mono-.20*side))
    # The seam ends at the exact preceding sample of the beginning sequence.
    result = rain[overlap:].copy()
    x = np.linspace(0, 1, overlap, dtype=np.float32)
    x = x*x*(3-2*x)
    result[-overlap:] = (result[-overlap:]*(1-x[:, None])+rain[:overlap]*x[:, None])
    t = np.arange(length, dtype=np.float32)/SR
    drift = 1+.055*np.sin(2*np.pi*t/60)+.025*np.sin(2*np.pi*t/90+.5)
    result *= drift[:, None]
    target = music_rms*10**(-27/20)
    result *= target/np.sqrt(np.mean(result.astype(np.float64)**2))
    return result


def loudness(path):
    cmd = ['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-af',
           'loudnorm=I=-21:TP=-1.7:LRA=15:print_format=json', '-f', 'null', '-']
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    blocks = re.findall(r'\{[^{}]+"input_i"[^{}]+\}', p.stderr, re.S)
    if not blocks:
        raise RuntimeError('FFmpeg did not return loudness measurements')
    return json.loads(blocks[-1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=HERE.parent/'audio-bucle-6min.wav')
    args = parser.parse_args()
    samples = verify_and_load_samples(args.samples)
    piano = make_piano(samples)
    tracks, chapters, offset = [], [], 0
    for work in WORKS:
        print(f"Rendering Gymnopédie {work['number']}", flush=True)
        notes = read_score(HERE/f"gymnopedie-{work['number']}.midi")
        assert max(e['end'] for e in notes) == work['quarters']
        track, info = render_work(work, notes, piano)
        chapters.append(dict(title=f"Erik Satie — Gymnopédie n.º {work['number']}",
                             start_seconds=offset, duration_seconds=work['seconds'], **info))
        tracks.append(track)
        offset += work['seconds']
    music = np.concatenate(tracks)
    assert len(music) == TOTAL*SR
    music_rms = float(np.sqrt(np.mean(music.astype(np.float64)**2)))
    rain = make_rain(len(music), music_rms)
    rain_rms = float(np.sqrt(np.mean(rain.astype(np.float64)**2)))
    combined = music+rain
    del tracks, music, rain
    with tempfile.TemporaryDirectory(prefix='jagoncito-satie-master-') as folder:
        measurement = Path(folder)/'premaster.wav'
        wavfile.write(measurement, SR, combined)
        before = loudness(measurement)
    gain_db = min(-21-float(before['input_i']), -1.7-float(before['input_tp']))
    combined *= 10**(gain_db/20)
    peak = float(np.max(np.abs(combined)))
    assert peak < 1
    rng = np.random.default_rng(1381888)
    combined += ((rng.random(combined.shape, dtype=np.float32)-
                  rng.random(combined.shape, dtype=np.float32))/65536)
    pcm = np.round(np.clip(combined, -1, 1)*32767).astype(np.int16)
    wavfile.write(args.output, SR, pcm)
    levels = loudness(args.output)
    boundary_delta = (pcm[0].astype(np.int32)-pcm[-1].astype(np.int32)).tolist()
    seam = np.concatenate((pcm[-SR:], pcm[:SR])).astype(np.float64)/32768
    manifest = dict(
        title='Erik Satie — Gymnopédies n.º 1 y n.º 3', complete_works=2,
        sample_rate=SR, channels=2, pcm_bits=16, duration_seconds=TOTAL,
        bytes=args.output.stat().st_size,
        sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
        chapters=chapters,
        music='Interpretaciones virtuales nuevas; notas, silencios y repeticiones completos de ambas partituras.',
        ambience='Lluvia sintética filtrada, creada con ruido; sin grabaciones externas ni truenos.',
        ambience_rms_relative_to_music_db=round(20*np.log10(rain_rms/music_rms), 3),
        integrated_lufs=float(levels['input_i']), true_peak_dbtp=float(levels['input_tp']),
        loudness_range_lu=float(levels['input_lra']), linear_master_gain_db=round(gain_db, 3),
        pcm_peak_dbfs=round(20*np.log10(np.max(np.abs(pcm.astype(np.float64)))/32768), 3),
        clipped_samples=int(np.sum(np.abs(pcm.astype(np.int32))>=32767)),
        loop_boundary_delta_pcm16=boundary_delta,
        loop_seam_max_sample_step_dbfs=round(20*np.log10(np.max(np.abs(np.diff(seam,axis=0)))),3),
        rights='Satie (1888), transcripciones Mutopia de dominio público; muestras VSCO2 CC0, lluvia original.',
        listening_review='Revisión técnica automatizada. No se afirma escucha humana o valoración auditiva subjetiva.',
        no_commercial_work_recording_used=True,
    )
    assert manifest['clipped_samples'] == 0
    assert manifest['true_peak_dbtp'] <= -1.5
    assert args.output.stat().st_size < 100*1024**2
    (HERE/'audio-manifiesto.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
