"""Reel 1 v2 audio (no voice: TikTok's text-to-speech goes on top in the app).

Lo-fi loop while he scrolls -> tape-stop into the overscroll thud -> sub boom +
force-field hum when the wall lands -> music back, lighter, for the focus part
(coin plinks, ding, pay chime) -> shimmer when the wall dissolves -> boom +
hum again when it comes back.

Usage: python3 audio2.py <reel_dir> <out.wav>
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
FPS = T['fps']
DUR = T['total_frames'] / FPS
N = int(DUR * SR) + SR
rng = np.random.default_rng(7)


def shot_t(sid):
    for sh in T['shots']:
        if sh['id'] == sid:
            return sh['start'], sh['dur']
    raise KeyError(sid)


def events(key):
    out = []
    for g in sorted(META):
        if META[g].get(key):
            out.append((g - 1) / FPS)
    return out


def put(buf, sig, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig * g


def env(n, a=0.005, decay=6.0):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t * decay)


def lp(x, k):
    return np.convolve(x, np.ones(k) / k, mode='same')


def epiano(freqs, d):
    n = int(d * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 3)) for f in freqs)
    return s / len(freqs) * env(n, 0.01, 1.6)


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-t * 30)) / SR) * env(n, 0.002, 9)


def snare():
    n = int(0.2 * SR)
    return lp(rng.normal(0, 1, n), 6) * env(n, 0.002, 18) * 0.6


def hat():
    n = int(0.05 * SR)
    return np.diff(rng.normal(0, 1, n), prepend=0) * env(n, 0.001, 70) * 0.25


def tone(f, d, decay=6.0):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * decay)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


CHORDS = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]  # Fmaj7 Em7 Dm7 Cmaj7


def loop(length, bright=1.0, drums=True):
    beat = 60 / 88
    buf = np.zeros(int(length * SR) + SR)
    nb = int(length / beat) + 1
    for b in range(nb):
        t = b * beat
        if b % 2 == 0:
            ch = CHORDS[(b // 2) % 4]
            put(buf, epiano([hz(m) for m in ch], beat * 2.2), t, 0.35)
            put(buf, tone(hz(ch[0] - 12), beat * 2, 2.5), t, 0.3)
        if drums:
            if b % 4 in (0, 3) or (b % 4 == 2 and b % 8 == 6):
                put(buf, kick(), t, 0.7)
            if b % 2 == 1:
                put(buf, snare(), t, 0.45)
            for h in range(2):
                put(buf, hat(), t + h * beat / 2 + (0.03 if h else 0), 0.8)
    buf = buf[: int(length * SR)]
    warble = 1 + 0.004 * np.sin(2 * np.pi * 0.7 * np.arange(len(buf)) / SR)  # tape wow
    idx = np.clip(np.cumsum(warble) - 1, 0, len(buf) - 1)
    buf = np.interp(idx, np.arange(len(buf)), buf)
    if bright < 1:
        buf = lp(buf, int(2 + (1 - bright) * 12))
    return buf


def tape_stop(sig, d=0.45):
    """slow the last d seconds down to a halt."""
    n = int(d * SR)
    head, tail = sig[:-n], sig[-n:]
    speed = np.linspace(1, 0, n) ** 1.5
    pos = np.cumsum(speed)
    return np.concatenate([head, np.interp(pos, np.arange(n), tail) * np.linspace(1, 0.2, n)])


def boom():
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(32 + 80 * np.exp(-t * 12)) / SR) * env(n, 0.002, 2.2)
    crack = lp(rng.normal(0, 1, n), 3) * env(n, 0.001, 22)
    return sub * 1.0 + crack * 0.35


def hum(d):
    n = int(d * SR)
    t = np.arange(n) / SR
    saw = ((55 * t) % 1 - 0.5) + 0.5 * ((55.4 * t) % 1 - 0.5) + 0.3 * np.sin(2 * np.pi * 110 * t)
    s = lp(saw, 30) * (0.75 + 0.25 * np.sin(2 * np.pi * 6 * t))
    fade = np.minimum(1, t / 0.08) * np.minimum(1, (d - t) / 0.25)
    return s * fade


def shimmer(d=1.2, up=True):
    n = int(d * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, m in enumerate((72, 76, 79, 83, 84, 88)):
        st = k * d / 8
        seg = tone(hz(m), d - st, 3)
        out[int(st * SR):int(st * SR) + len(seg)] += seg
    sweep = lp(rng.normal(0, 1, n), 4) * (t / d if up else 1 - t / d) * 0.3
    return (out * 0.25 + sweep) * np.minimum(1, (d - t) / 0.3)


music = np.zeros(N)
fx = np.zeros(N)

thud = events('thud')[0]
hit1, hit2 = events('wall_hit')[0], events('wall_hit')[-1]
dissolve = events('dissolve')[0]
desk0, _ = shot_t('desk')

# 1) doomscroll loop, tape-stopped into the overscroll thud
a = loop(thud)
put(music, tape_stop(a), 0.0, 1.0)
# 2) silence-ish under the wall: just the hum. 3) focus part: lighter loop, no kick at first
b = loop(DUR - desk0 + 1, bright=0.6, drums=True)
b[: int(0.4 * SR)] *= np.linspace(0, 1, int(0.4 * SR))
cut = events('cut')[0]  # comic beat: music stops dead, he freezes... then the wall
seg = b[: int((cut - desk0) * SR)]
seg[-200:] *= np.linspace(1, 0, 200)
put(music, seg, desk0, 0.85)

# clock ticks accelerate with the time-lapse
st, d = shot_t('clock')
t, iv = st, 0.22
while t < st + d:
    put(fx, np.diff(rng.normal(0, 1, 900), prepend=0) * env(900, 0.0005, 300), t, 0.35)
    t += iv
    iv = max(0.07, iv * 0.85)
for t in events('tap'):
    put(fx, np.diff(rng.normal(0, 1, 1200), prepend=0) * env(1200, 0.0005, 250), t, 0.5)
put(fx, boom() * 0.6, thud, 0.6)  # the feed won't move: dull thud
put(fx, boom(), hit1, 1.0)
put(fx, hum(desk0 - hit1 + 0.4), hit1, 0.18)
put(fx, hum(dissolve - desk0 + 0.3), desk0, 0.08)  # still there, quieter, while he works
put(fx, shimmer(1.3), dissolve, 0.7)
put(fx, boom(), hit2, 1.0)
end0, _ = shot_t('endcard')
put(fx, hum(end0 - hit2 + 0.3), hit2, 0.2)
# the phone goes flying: cartoon whoosh up, clatter on the floor (twice: bounce)
n = int(0.45 * SR)
tt = np.arange(n) / SR
put(fx, np.sin(2 * np.pi * np.cumsum(500 + 1400 * tt / 0.45) / SR) * np.sin(np.pi * tt / 0.45) * 0.5
    + lp(rng.normal(0, 1, n), 3) * np.sin(np.pi * tt / 0.45) * 0.3, events('whoosh')[0], 0.35)
for k, t in enumerate(events('clatter')):
    for j in range(4):
        put(fx, np.diff(rng.normal(0, 1, 1500), prepend=0) * env(1500, 0.0005, 120), t + j * 0.035 + rng.random() * 0.01,
            (0.6 if k == 0 else 0.3) / (j + 1))
    put(fx, tone(2600 + 300 * k, 0.12, 30), t, 0.12)
# end card: little pops for ghost / title / button, and a warm resolving chord
for t, f in ((0.0, 880), (0.25, 1175), (1.0, 1568)):
    put(fx, tone(f, 0.2, 18), end0 + t, 0.25)
put(music, epiano([hz(m) for m in (48, 55, 64, 67, 72)], 2.4), end0 + 0.2, 0.5)
for sid in ('desk_top', 'coins'):
    st, d = shot_t(sid)
    for k in range(9):
        put(fx, tone(1568 + (k % 3) * 160, 0.3, 12), st + 0.1 + k * d / 9, 0.16)
for t in events('ding'):
    put(fx, tone(1319, 0.6), t, 0.25)
    put(fx, tone(1760, 0.6), t + 0.08, 0.2)
for t in events('chime'):
    for k, f in enumerate((1047, 1319, 1568, 2093)):
        put(fx, tone(f, 0.9, 4), t + k * 0.06, 0.2)

room = lp(rng.normal(0, 1, N), 40) * 0.015
crackle = (rng.random(N) > 0.9996) * rng.normal(0, 0.3, N)
mix = music * 0.55 + fx + room + crackle * 0.3
mix = np.tanh(mix * 1.2) * 0.85
L = int(DUR * SR)
pcm = (np.stack([mix[:L], mix[:L]], 1) * 32767).astype(np.int16)
with wave.open(OUT, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('audio', OUT, round(DUR, 2), 's')
