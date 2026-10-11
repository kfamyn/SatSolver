"""Chiptune sound design for the PS1 'Day' short, timed from meta.json.
Usage: python3 sound_day.py <ps1day_dir> <out.wav>"""
import json
import sys
import wave

import numpy as np

src, out = sys.argv[1], sys.argv[2]
meta = json.load(open(f'{src}/meta.json'))
total = meta['total']
M = {int(k): v for k, v in meta['frames'].items()}
SR, FPS = 44100, 30
N = int(total / FPS * SR) + SR
mix = np.zeros(N)
rng = np.random.default_rng(3)
sec = lambda g: (g - 1) / FPS


def T(d):
    return np.arange(int(d * SR)) / SR


def sq(f, d, duty=0.5, decay=0.0):
    t = T(d)
    w = np.where((t * f) % 1 < duty, 1.0, -1.0)
    return w * (np.exp(-t * decay) if decay else 1)


def tri(f, d):
    t = T(d)
    return 2 * np.abs(2 * ((t * f) % 1) - 1) - 1


def noise(d, decay=30):
    t = T(d)
    return rng.uniform(-1, 1, len(t)) * np.exp(-t * decay)


def sweep(f0, f1, d, duty=0.5, decay=0):
    t = T(d)
    f = f0 + (f1 - f0) * t / d
    ph = np.cumsum(f) / SR
    w = np.where(ph % 1 < duty, 1.0, -1.0)
    return w * (np.exp(-t * decay) if decay else 1)


def add(sig, at, gain=1.0):
    i = int(at * SR)
    if i >= N or i < 0:
        return
    sig = sig[: N - i]
    mix[i:i + len(sig)] += sig * gain


def fade(sig, a=0.005, r=0.02):
    n = len(sig)
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] = np.linspace(1, 0, nr)
    return sig * e


NOTE = lambda n: 440 * 2 ** ((n - 69) / 12)

# ---------------------------------------------------------------- timeline
starts = {}
for g in sorted(M):
    starts.setdefault(M[g]['shot'], g)
slam_g = next(g for g in sorted(M) if M[g].get('slam'))
t_slam = sec(slam_g)
music_g = next(g for g in sorted(M) if M[g].get('music'))
t_music = sec(music_g)

# ACT 1: tick on every cut + accelerating clock, swipes, hypnotic drone, feed chirps
for g in sorted(M):
    if M[g].get('tick'):
        add(fade(sq(1760, 0.03, 0.25, 60)), sec(g), 0.35)
        add(noise(0.02, 200) * 0.5, sec(g), 0.35)
t, iv = 0.0, 0.5
while t < t_slam - 0.05:
    add(fade(sq(880, 0.02, 0.5, 80)), t, 0.18)
    t += iv
    iv = max(0.12, iv * 0.95)
for g in range(1, slam_g):
    sh = M.get(g, {}).get('shot', '')
    if sh.startswith('A') and (g - 1) % 12 == 0:
        add(fade(noise(0.12, 25) * np.linspace(1, 0.2, int(0.12 * SR))), sec(g), 0.22)  # swipe
n = int(t_slam * SR)
tt = np.arange(n) / SR
drone = tri(55, t_slam)[:n] * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * tt)) * 0.12
mix[:n] += drone
for k in range(int(t_slam * 7)):  # muffled 'feed' chirps
    at = rng.uniform(0, t_slam - 0.1)
    f = rng.choice([523, 659, 784, 988, 1175])
    add(fade(sq(f, 0.05, 0.125, 30)), at, 0.05)

# THE WALL: hard cut, 8-bit crash
i = int(t_slam * SR)
mix[i:] = 0
add(noise(1.2, 4) * 0.8, t_slam, 0.7)
add(sweep(220, 40, 0.6, 0.5, 4) * 0.6, t_slam, 0.7)

# snap out: blink blip + '!' alert
for g in sorted(M):
    m = M[g]
    if m.get('blink'):
        add(fade(sq(1320, 0.04, 0.5, 40)), sec(g), 0.2)
    if m.get('alert'):
        add(fade(sq(NOTE(81), 0.07, 0.5)), sec(g), 0.35)
        add(fade(sq(NOTE(88), 0.18, 0.5, 8)), sec(g) + 0.07, 0.35)

# MUSIC: upbeat chiptune from the focus montage to the end (140 BPM)
bpm = 140
beat = 60 / bpm
prog = [(48, 64), (55, 62), (57, 60), (53, 65)]  # bass root, lead anchor (C G Am F)
melody = [0, 4, 7, 4, 9, 7, 4, 2]
t = t_music
bar = 0
end = total / FPS
while t < end:
    root, anchor = prog[bar % 4]
    chill = t > sec(starts['E1'])
    for b in range(4):
        tb = t + b * beat
        if tb >= end:
            break
        add(fade(sq(NOTE(root - 12), beat * 0.9, 0.25)), tb, 0.10)  # bass
        add(fade(sq(NOTE(root - 12 + 7), beat * 0.4, 0.25)), tb + beat / 2, 0.06)
        if not chill:
            add(sweep(160, 40, 0.09, 0.5, 30), tb, 0.35)  # kick
            add(noise(0.03, 120), tb + beat / 2, 0.12)  # hat
            if b % 2 == 1:
                add(noise(0.12, 30), tb, 0.18)  # snare
        for h in range(2):
            idx = (bar * 8 + b * 2 + h) % len(melody)
            n_ = anchor + melody[idx] - 12 * (bar % 2 == 1 and h == 1)
            add(fade(sq(NOTE(n_ + 12), beat * 0.45, 0.5 if not chill else 0.125, 6)), tb + h * beat / 2, 0.06 if not chill else 0.04)
    t += 4 * beat
    bar += 1

# coins, ding, tap, chime
for g in sorted(M):
    m = M[g]
    at = sec(g)
    if m.get('coin'):
        add(fade(sq(988, 0.06, 0.5)), at, 0.18)
        add(fade(sq(1319, 0.28, 0.5, 9)), at + 0.06, 0.18)
    if m.get('ding'):
        for k, n_ in enumerate([84, 88, 91, 96]):
            add(fade(sq(NOTE(n_), 0.12, 0.5, 6)), at + k * 0.07, 0.2)
    if m.get('tap'):
        add(fade(sq(1500, 0.03, 0.5, 60)), at, 0.25)
    if m.get('chime'):
        for k, n_ in enumerate([79, 83, 86, 91, 95]):
            add(fade(sq(NOTE(n_), 0.2, 0.25, 5)), at + k * 0.05, 0.2)

L = mix[: int(total / FPS * SR)]
L = np.tanh(L * 1.3) * 0.85
pcm = (np.stack([L, L], 1) * 32767).astype(np.int16)
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('wrote', out)
