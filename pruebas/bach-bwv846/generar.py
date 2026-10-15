"""Prueba: primeros ocho compases de BWV 846. Síntesis propia sin muestras."""
from pathlib import Path
import wave
import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parent
# Alturas MIDI; patrón de semicorcheas de cada medio compás, repetido.
BARS = [
    [60,64,67,72,76,67,72,76],
    [60,62,69,74,77,69,74,77],
    [59,62,67,74,77,67,74,77],
    [60,64,67,72,76,67,72,76],
    [60,64,69,76,81,69,76,81],
    [60,62,66,69,74,66,69,74],
    [59,62,67,74,79,67,74,79],
    [59,60,64,67,72,64,67,72],
]
rng = np.random.default_rng(846)
step = 60 / 66 / 4
mix = np.zeros((int((128*step+4)*SR),2), dtype=np.float64)
for b, pitches in enumerate(BARS):
    for j, midi in enumerate(pitches*2):
        when = .15 + (b*16+j)*step + rng.uniform(-.003,.003)
        t = np.arange(int(3.4*SR))/SR
        f = 440 * 2**((midi-69)/12)
        note = np.zeros_like(t)
        # Parciales con ligera inarmonicidad y decaimiento dependiente de frecuencia.
        for h in range(1,13):
            freq = f*h*np.sqrt(1+0.000055*h*h)
            if freq > SR*.45:
                continue
            envelope = (1-np.exp(-t/.002))*np.exp(-t*(.85+h*.22))
            note += (1/h**1.65)*envelope*np.sin(2*np.pi*freq*t)
        note *= (.74 + .12*np.cos(j*np.pi/8)+rng.uniform(-.025,.025))
        pan = np.clip((midi-60)/48+.3,.2,.8)
        start = int(when*SR)
        mix[start:start+len(t),0] += note*np.sqrt(1-pan)
        mix[start:start+len(t),1] += note*np.sqrt(pan)
# Reflexiones suaves, sin bancos de sonido externos.
dry = mix.copy()
for seconds, gain in [(.071,.12),(.113,.09),(.179,.065),(.293,.04)]:
    delay = int(seconds*SR)
    mix[delay:] += gain*dry[:-delay,::-1]
mix[-int(1.5*SR):] *= np.linspace(1,0,int(1.5*SR))[:,None]
mix *= 10**(-1.5/20)/np.max(np.abs(mix))
assert np.isfinite(mix).all() and np.sqrt(np.mean(mix**2)) > .01
with wave.open(str(OUT/'bach-bwv846-prueba.wav'),'wb') as wav:
    wav.setparams((2,2,SR,0,'NONE','not compressed'))
    wav.writeframes((mix*32767).astype('<i2').tobytes())
print(f'Duración: {len(mix)/SR:.2f} s; pico: {np.max(np.abs(mix)):.4f}; notas: 128')
