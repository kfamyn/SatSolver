"""Reel 1 audio: narration on top, a soft ambient bed (ducked under the voice),
room tone, and only a handful of sound effects (clock, tap, slam, coins, chime).

Usage: python3 audio.py <reel_dir> <out.wav>
"""
import json
import os
import sys
import wave

import numpy as np

REEL, OUT = sys.argv[1], sys.argv[2]
T = json.load(open(os.path.join(REEL, 'timings.json')))
META = {int(k): v for k, v in json.load(open(os.path.join(REEL, 'meta.json')))['frames'].items()}
SR = 44100
N = int(T['total_frames'] / T['fps'] * SR) + SR
vo = np.zeros(N)
fx = np.zeros(N)
rng = np.random.default_rng(5)


def read(path):
    with wave.open(path) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        sr = w.getframerate()
    if sr != SR:  # simple resample
        x = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
        a = np.interp(x, np.arange(len(a)), a)
    return a


def put(buf, sig, t, g=1.0):
    i = int(t * SR)
    sig = sig[: max(0, N - i)]
    buf[i:i + len(sig)] += sig * g


def tone(f, d, decay=6.0, harm=0.3):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + harm * np.sin(4 * np.pi * f * t)) * np.exp(-t * decay)


def click(d=0.03, hp=True):
    n = int(d * SR)
    s = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 300)
    return np.diff(s, prepend=0) if hp else s


for sh in T['shots']:
    put(vo, read(sh['vo']), sh['start'] + 0.05, 1.0)
    st, d = sh['start'], sh['dur']
    if sh['id'] == 'clock':  # ticking that speeds up with the time-lapse
        t, iv = st, 0.5
        while t < st + d:
            put(fx, click(0.02), t, 0.25)
            t += iv
            iv = max(0.09, iv * 0.88)
fps = T['fps']
for g, m in META.items():
    t = (g - 1) / fps
    if m.get('tap'):
        put(fx, click(0.025), t, 0.5)
    if m.get('slam'):
        n = int(0.9 * SR)
        tt = np.arange(n) / SR
        put(fx, np.sin(2 * np.pi * np.cumsum(40 + 120 * np.exp(-tt * 18)) / SR) * np.exp(-tt * 5), t, 0.9)
        put(fx, rng.normal(0, 1, n) * np.exp(-tt * 25), t, 0.25)
    if m.get('ding'):
        put(fx, tone(1319, 0.6), t, 0.25)
        put(fx, tone(1760, 0.6), t + 0.08, 0.2)
    if m.get('chime'):
        for k, f in enumerate((1047, 1319, 1568)):
            put(fx, tone(f, 0.8, 4), t + k * 0.07, 0.2)
# coins during the desk time-lapse
for sh in T['shots']:
    if sh['id'] == 'desk_top':
        for k in range(10):
            put(fx, tone(1568 + (k % 3) * 120, 0.25, 14), sh['start'] + 0.3 + k * sh['dur'] / 11, 0.12)

# ambient bed: slow pad, ducked under the narration
t = np.arange(N) / SR
pad = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate((110, 164.8, 220, 277.2))) / 4
pad *= 0.5 + 0.5 * np.sin(2 * np.pi * t / 8)
env = np.convolve(np.abs(vo), np.ones(4410) / 4410, mode='same')
duck = 1 - np.clip(env * 6, 0, 0.7)
room = np.convolve(rng.normal(0, 1, N), np.ones(30) / 30, mode='same') * 0.02
mix = vo * 0.95 + fx + pad * 0.05 * duck + room
mix = np.tanh(mix * 1.1) * 0.9
L = int(T['total_frames'] / fps * SR)
pcm = (np.stack([mix[:L], mix[:L]], 1) * 32767).astype(np.int16)
with wave.open(OUT, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('audio', OUT)
