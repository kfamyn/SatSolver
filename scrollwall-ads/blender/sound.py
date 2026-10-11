"""Sound design for THE FEED, synthesised from scratch and timed to the cut list
in fx.json. Usage: python3 sound.py <thefeed_dir> <out.wav>"""
import json
import math
import sys
import wave

import numpy as np

src, out = sys.argv[1], sys.argv[2]
meta = json.load(open(f'{src}/fx.json'))
total = meta['total']
fx = {int(k): v for k, v in meta['frames'].items()}
SR = 48000
FPS = 30
N = int((total / FPS + 1.0) * SR)
L = np.zeros(N)
R = np.zeros(N)
rng = np.random.default_rng(1)


def t2i(sec):
    return int(sec * SR)


def add(sig, at, gain=1.0, pan=0.0):
    i = t2i(at)
    if i >= N:
        return
    sig = sig[: N - i]
    L[i:i + len(sig)] += sig * gain * (1 - max(0, pan))
    R[i:i + len(sig)] += sig * gain * (1 + min(0, pan))


def env(n, a=0.002, d=0.1):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def tick(pitch=1.0):
    n = t2i(0.09)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 2600 * pitch * t) * np.exp(-t * 90) + 0.6 * np.sin(2 * np.pi * 900 * pitch * t) * np.exp(-t * 60)
    click = rng.normal(0, 1, n) * np.exp(-t * 900)
    return (body * 0.6 + click * 0.5)


def swipe():
    n = t2i(0.22)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    # crude band sweep: differentiate (highpass) and window
    hp = np.diff(noise, prepend=0)
    return hp * np.sin(np.pi * t / t[-1]) ** 2 * 0.35


def thump(f0=55, d=0.35):
    n = t2i(d * 2)
    t = np.arange(n) / SR
    f = f0 + 90 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / d * 2.5)


def impact():
    n = t2i(2.5)
    t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(30 + 160 * np.exp(-t * 14)) / SR) * np.exp(-t * 2.2)
    crunch = rng.normal(0, 1, n) * np.exp(-t * 18)
    ring = np.sin(2 * np.pi * 523 * t) * np.exp(-t * 1.4) * 0.12 + np.sin(2 * np.pi * 784 * t) * np.exp(-t * 1.1) * 0.08
    return sub * 1.0 + crunch * 0.5 + ring


def babble(n):
    """Muffled 'feed audio': chopped formant-ish noise bursts."""
    t = np.arange(n) / SR
    carrier = rng.normal(0, 1, n)
    # smooth (lowpass) by moving average
    k = 40
    carrier = np.convolve(carrier, np.ones(k) / k, mode='same')
    form = np.sin(2 * np.pi * (220 + 120 * np.sin(2 * np.pi * 3.1 * t)) * t)
    chop = (np.sin(2 * np.pi * 7.3 * t) > -0.2).astype(float)
    return carrier * 6 * (0.6 + 0.4 * form) * chop


# --------------------------------------------------------------- timeline
shot_of = {g: fx[g]['shot'] for g in fx}
starts = {}
for g in sorted(shot_of):
    starts.setdefault(shot_of[g], g)
sec = lambda g: (g - 1) / FPS
slam_g = starts[16] + 5
spiral_end = sec(slam_g)

# clock: a tick on every cut + a steady tick that accelerates through the spiral
for sh, g in starts.items():
    if sh <= 15:
        add(tick(1.0 + sh * 0.02), sec(g), 0.55, pan=(-0.3 if sh % 2 else 0.3))
t = 0.0
iv = 0.5
while t < spiral_end - 0.05:
    add(tick(0.8), t, 0.25)
    t += iv
    iv = max(0.07, iv * 0.93)

# thumb swipes on the thumb shots
for sh in (3, 8, 11):
    g0 = starts[sh]
    n = sum(1 for g in shot_of if shot_of[g] == sh)
    for k in range(0, n, 4 if sh == 3 else 3):
        add(swipe(), sec(g0 + k), 0.6, pan=0.2)

# heartbeat from the vertigo shot to the slam
g = starts[10]
beat = 0.75
tt = sec(g)
while tt < spiral_end - 0.1:
    add(thump(48, 0.18), tt, 0.7)
    add(thump(52, 0.15), tt + 0.16, 0.45)
    tt += beat
    beat = max(0.32, beat * 0.9)

# drone + babble swelling until the slam, then hard cut
n_sp = t2i(spiral_end)
tt = np.arange(n_sp) / SR
k = tt / spiral_end
drone = (np.sin(2 * np.pi * (46 + 30 * k ** 2) * tt) + 0.5 * np.sin(2 * np.pi * (46.7 + 31 * k ** 2) * tt * 2)
         + 0.25 * np.sign(np.sin(2 * np.pi * (92 + 60 * k ** 2) * tt)) * k)
riser = np.diff(rng.normal(0, 1, n_sp), prepend=0) * k ** 4 * 0.5
L[:n_sp] += (drone * (0.05 + 0.35 * k ** 2) + riser) * 0.8
R[:n_sp] += (drone * (0.05 + 0.35 * k ** 2) + riser) * 0.8
bab = babble(n_sp) * (0.08 + 0.3 * k ** 2)
L[:n_sp] += bab
R[:n_sp] += np.roll(bab, 300)

# THE SLAM: everything stops; impact, then near silence
cut = t2i(spiral_end)
L[cut:] = 0
R[cut:] = 0
add(impact(), spiral_end, 1.0)

# Wally's curious "hm?" during his head tilt
g = starts[17] + 24
n = t2i(0.5)
t = np.arange(n) / SR
hm = np.sin(2 * np.pi * np.cumsum(420 + 160 * t / t[-1]) / SR) * np.sin(np.pi * t / t[-1]) * 0.18
add(hm, sec(g), 1.0)

# dawn: warm pad fades in
g = starts[18]
d0 = sec(g)
n = N - t2i(d0)
t = np.arange(n) / SR
pad = sum(np.sin(2 * np.pi * f * t) for f in (220, 277.2, 329.6, 440)) / 4
add(pad * np.minimum(1, t / 1.5) * 0.12, d0, 1.0)

# room tone after the slam
L[cut:] += rng.normal(0, 0.004, N - cut)
R[cut:] += rng.normal(0, 0.004, N - cut)

mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.2) * 0.9
pcm = (mix[: int(total / FPS * SR)] * 32767).astype(np.int16)
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('wrote', out, len(pcm) / SR, 's')
