#!/usr/bin/env python3
"""Render a new, reproducible Chopin performance using CC0 piano notes.

Python 3.12; dependencies: numpy, scipy, mido. No existing performance is used.
Samples stay in the supplied cache, outside the repository. HTTPS verification
and a pinned repository commit plus SHA-256 checks remain enabled.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import urllib.request
import warnings

import mido
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
HERE = Path(__file__).resolve().parent


def read_score(path):
    midi = mido.MidiFile(path)
    notes, pedals = [], []
    for track_id, track in enumerate(midi.tracks):
        tick, active = 0, {}
        for event in track:
            tick += event.time
            q = tick / midi.ticks_per_beat
            if event.type == 'control_change' and event.control == 64:
                pedals.append((q, event.value >= 64))
            elif event.type == 'note_on' and event.velocity:
                active[event.note] = q
            elif event.type in ('note_on', 'note_off') and event.note in active:
                notes.append(dict(pitch=event.note, start=active.pop(event.note),
                                  end=q, hand='right' if track_id == 1 else 'left'))
    return sorted(notes, key=lambda n: (n['start'], n['pitch'])), sorted(set(pedals))


def make_time_map(bpm, take):
    # Preserve note values; interpret phrase endings and the final fermatas.
    q = np.arange(0, 103.001, .002, dtype=np.float64)
    measure = np.maximum((q - 1) / 4, 0)
    position = np.mod(q - 1, 4) / 4
    stretch = 1 + .028 * np.sin(2*np.pi*q/16 + take*.25)
    stretch += .022*np.cos(2*np.pi*q/4)
    for end in (17, 33, 49, 65, 81, 89):
        stretch += .14*np.exp(-((q-(end-.7))/.9)**2)
    # A modest forward motion at the central climax, followed by a long release.
    stretch -= .035*np.exp(-((q-68)/6)**2)
    stretch += .18*np.clip((q-85)/9, 0, 1)
    stretch += .28*np.clip((q-93)/8, 0, 1)
    stretch += .60*np.exp(-((q-92)/.8)**2)  # written pause with fermata
    stretch += .75*np.exp(-((q-100)/1.6)**2) # final chord with fermata
    seconds = np.cumsum(stretch) * .002 * 60 / bpm
    seconds -= seconds[0]
    return lambda quarter: np.interp(quarter, q, seconds)


def prepare_samples(folder, manifest):
    folder.mkdir(parents=True, exist_ok=True)
    entries = json.loads(manifest.read_text())['samples']
    result = {}
    for entry in entries:
        path = folder / entry['filename']
        if not path.exists():
            print('Downloading', entry['filename'], flush=True)
            with urllib.request.urlopen(entry['source'], timeout=120) as response:
                data = response.read()
            path.write_bytes(data)
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise RuntimeError(f'SHA-256 mismatch: {path.name}')
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', wavfile.WavFileWarning)
            rate, data = wavfile.read(path)
        assert rate == SR and data.ndim == 2 and data.shape[1] == 2
        data = data.astype(np.float32) / 2147483648.0  # PCM24 left aligned int32
        data -= np.mean(data[-min(len(data), SR):], axis=0, keepdims=True)
        # Anti-click onset, shorter than the piano's attack.
        data[:88] *= np.linspace(0, 1, 88, dtype=np.float32)[:, None]
        result[(entry['root_midi'], entry['layer'])] = data
    return result


def instrument(samples):
    roots = sorted(set(k[0] for k in samples))
    cache = {}
    def note(pitch, velocity):
        if pitch not in cache:
            root = min(roots, key=lambda n: abs(n-pitch))
            ratio = Fraction(2 ** (-(pitch-root)/12)).limit_denominator(3000)
            cache[pitch] = tuple(
                signal.resample_poly(samples[(root, layer)], ratio.numerator,
                                     ratio.denominator, axis=0).astype(np.float32)
                for layer in (1, 2))
        soft, medium = cache[pitch]
        length = min(len(soft), len(medium))
        amount = np.clip((velocity-42)/48, 0, .87)
        # Keep the captured loudness difference between the velocity layers.
        gain = np.clip((velocity/62)**1.35, .22, 1.55)
        return ((1-amount)*soft[:length] + amount*medium[:length])*gain
    return note


def add_room(audio, seed):
    # A small, quiet room, generated from noise. No external impulse recording.
    rng = np.random.default_rng(seed)
    n = int(SR*1.35)
    t = np.arange(n)/SR
    impulse = rng.standard_normal((n, 2)).astype(np.float32)
    impulse = signal.sosfilt(signal.butter(2, 3800, fs=SR, output='sos'),
                            impulse, axis=0).astype(np.float32)
    impulse *= np.exp(-6.9*t/1.2)[:, None]
    impulse[:int(SR*.028)] = 0
    impulse *= .075 / np.sqrt(np.sum(impulse[:, 0]**2))
    for seconds, amplitude in ((.021, .075), (.037, .056), (.053, .039), (.079, .027)):
        impulse[int(seconds*SR), 0] += amplitude
        impulse[int((seconds+.003)*SR), 1] += amplitude*.92
    for ch in range(2):
        audio[:, ch] += signal.oaconvolve(audio[:, ch], impulse[:, ch])[:len(audio)]
    return audio


def render_take(notes, pedals, piano, take):
    rng = np.random.default_rng(20261015 + take)
    bpm = (49.6, 50.6, 49.1)[take]
    timing = make_time_map(bpm, take)
    length = float(timing(101)) + 5.2
    out = np.zeros((int(length*SR), 2), dtype=np.float32)
    # Dynamics are shaped by phrases rather than random velocity alone.
    bars = np.arange(26)
    dynamics = np.array([49, 54, 55, 54, 52, 54, 55, 53, 51, 60, 57, 56,
                         63, 52, 55, 57, 66, 77, 68, 57, 57, 49, 44, 40, 36, 32])
    pedal_times = [p[0] for p in pedals]
    for event in notes:
        start_q, end_q = event['start'], event['end']
        held_end = end_q
        idx = np.searchsorted(pedal_times, end_q, side='right')-1
        if idx >= 0 and pedals[idx][1]:
            off = next((q for q, down in pedals[idx+1:] if not down), end_q)
            held_end = max(held_end, off)
        # Keep a light legato in unpedalled melody; retain the written rests.
        t0 = float(timing(start_q)) + .65
        t1 = float(timing(held_end)) + .65
        is_right = event['hand'] == 'right'
        t0 += rng.normal(0, .006) + (.013 if is_right else 0)
        if not is_right:
            t0 += max(event['pitch']-45, 0)*.00034
        dynamic = float(np.interp((start_q-1)/4 + .4, bars, dynamics))
        dynamic += (1.2, -1.0, -.5)[take]
        velocity = dynamic + (2 if is_right else -19) + rng.normal(0, 1.6)
        if not is_right and event['pitch'] < 44:
            velocity += 4.5
        tone = piano(event['pitch'], velocity)
        duration = max(.06, t1-t0)
        release = (.45 if is_right else .27) + (.15 if held_end>end_q else 0)
        if start_q >= 97:
            release = 3.5
        use = min(len(tone), int((duration+release)*SR))
        tone = tone[:use].copy()
        release_at = min(use, int(duration*SR))
        if release_at < use:
            rt = np.arange(use-release_at, dtype=np.float32)/SR
            tone[release_at:] *= np.exp(-6.5*rt/release)[:, None]
        # Piano position: gentle, kept narrow enough for mono playback.
        balance = np.clip((event['pitch']-60)/42, -.65, .65)
        tone[:, 0] *= 1 - .14*balance
        tone[:, 1] *= 1 + .14*balance
        first = max(0, int(t0*SR))
        use = min(len(tone), len(out)-first)
        if use > 0:
            out[first:first+use] += tone[:use]
    # Remove subsonic energy only, preserving the low E fundamental.
    out = signal.sosfilt(signal.butter(2, 22, btype='highpass', fs=SR, output='sos'),
                         out, axis=0).astype(np.float32)
    out = add_room(out, 6100+take)
    # Fade only room/noise tails; never cut the opening notes.
    fade = min(len(out), int(2.4*SR))
    out[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]**1.3
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=HERE.parent/'audio.wav')
    args = parser.parse_args()
    notes, pedals = read_score(HERE/'partitura.mid')
    samples = prepare_samples(args.samples, HERE/'instrumento-vsco-fuentes.json')
    piano = instrument(samples)
    takes, chapters, offset = [], [], 0.0
    for index in range(3):
        print(f'Rendering performance {index+1}/3', flush=True)
        take = render_take(notes, pedals, piano, index)
        chapters.append(dict(start_seconds=round(offset, 3),
                             title=f'Preludio op. 28 n.º 4 — interpretación {index+1}',
                             duration_seconds=round(len(take)/SR, 3)))
        takes.append(take)
        offset += len(take)/SR
    # Each performance includes its own natural decay. The joins occur in silence.
    audio = np.concatenate(takes, axis=0)
    peak = float(np.max(np.abs(audio)))
    gain = 10**(-1.5/20)/peak
    audio *= gain
    # TPDF dither before conversion to 16-bit PCM; below the musical noise floor.
    rng = np.random.default_rng(846284)
    audio += ((rng.random(audio.shape, dtype=np.float32)-
               rng.random(audio.shape, dtype=np.float32))/65536)
    pcm = np.round(np.clip(audio, -1, 1)*32767).astype(np.int16)
    wavfile.write(args.output, SR, pcm)
    manifest = dict(
        work='Frédéric Chopin — Preludio en mi menor, op. 28 n.º 4',
        sample_rate=SR, channels=2, pcm_bits=16,
        duration_seconds=round(len(audio)/SR, 3),
        complete_performances=3, notes_per_performance=len(notes),
        pitch_range_midi=[min(n['pitch'] for n in notes), max(n['pitch'] for n in notes)],
        peak_dbfs=round(float(20*np.log10(np.max(np.abs(pcm.astype(np.float64)))/32768)), 3),
        rms_dbfs=round(float(20*np.log10(np.sqrt(np.mean((pcm.astype(np.float64)/32768)**2)))), 3),
        clipped_samples=int(np.sum(np.abs(pcm.astype(np.int32))>=32767)),
        sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
        bytes=args.output.stat().st_size, chapters=chapters,
        performance='Nueva interpretación programada; tres pasadas completas con rubato y dinámica distintos. No es una grabación humana.',
        rights='Composición y transcripción de dominio público; muestras de piano VSCO2 CC0. No se usa una grabación comercial de la obra.',
        listening_review='Validación técnica automatizada; no se afirma escucha humana del resultado.')
    (HERE/'audio-manifiesto.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
