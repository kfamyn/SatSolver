"""Reel 2 audio: subway bed (rumble + wheel clacks), a light lo-fi loop that stops dead
at CARD DECLINED and comes back when Scrollwall appears, and the money SFX
(ka-ching per swipe, declined buzz, head-whip, purple whoosh, coin plinks, pay chime).
Narration (vo_kokoro.py) on top, music ducked under it.

v3: softer swipe tinks; soft 'womp womp' for broke; no pauses except the one before
'Okay, real money...'; the car goes quiet
while everyone judges the guy, only his far-off scrolling is heard.

Usage: python3 audio.py <reel_dir> <out.wav> [vo.wav]
"""
import json
import os
import sys
import wave

import numpy as np

REEL, OUT = sys.argv[1], sys.argv[2]
T = json.load(open(os.path.join(REEL, 'timings.json')))
META = {int(k): v for k, v in json.load(open(os.path.join(REEL, 'meta.json')))['frames'].items()}
SR, FPS = 44100, T['fps']
DUR = T['total_frames'] / FPS
N = int(DUR * SR) + SR
rng = np.random.default_rng(11)
music, fx = np.zeros(N), np.zeros(N)


def shot_t(sid):
    sh = next(x for x in T['shots'] if x['id'] == sid)
    return sh['start'], sh['dur']


def events(key):
    return [(g - 1) / FPS for g in sorted(META) if META[g].get(key)]


def put(buf, sig, t, g=1.0):
    i = int(t * SR)
    if 0 <= i < len(buf):
        sig = sig[: len(buf) - i]
        buf[i:i + len(sig)] += sig * g


def env(n, a=0.003, decay=8.0):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t * decay)


def lp(x, k):
    return np.convolve(x, np.ones(k) / k, mode='same')


def tone(f, d, decay=6.0, harm=0.3):
    t = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + harm * np.sin(4 * np.pi * f * t)) * np.exp(-t * decay)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---- sfx
def kaching():
    """soft coin tink + a short finger swipe (not a harsh register)."""
    n = int(0.35 * SR)
    tink = tone(1976, 0.35, 16, 0.15) * 0.5
    tink[:int(0.25 * SR)] += tone(2960, 0.25, 22, 0.0)[:int(0.25 * SR)] * 0.25
    swipe = lp(rng.normal(0, 1, n), 14) * np.exp(-((np.arange(n) / SR - 0.03) ** 2) / 0.0006) * 0.25
    return lp(tink + swipe, 3)


def glance():
    """two muted woodblock taps: the awkward look-away."""
    out = np.zeros(int(0.3 * SR))
    for k, f in enumerate((660, 520)):
        seg = tone(f, 0.12, 40, 0.1)
        i = int(k * 0.11 * SR)
        out[i:i + len(seg)] += seg
    return out


def buzz():
    """soft 'womp womp' (muted, descending) for CARD DECLINED / broke."""
    out = np.zeros(int(0.8 * SR))
    for k, (f0, f1) in enumerate(((330, 311), (294, 262))):
        n = int(0.34 * SR)
        t = np.arange(n) / SR
        f = np.linspace(f0, f1, n)
        ph = 2 * np.pi * np.cumsum(f) / SR
        v = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * np.minimum(1, t / 0.03) * np.exp(-t * 3)
        v *= 1 + 0.15 * np.sin(2 * np.pi * 6 * t)  # a little 'wah'
        i = int(k * 0.36 * SR)
        out[i:i + n] += lp(v, 8)
    return out * 0.5


def whip():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    out = np.zeros(n)
    for k in (3, 6, 12):  # crude sweep from bright to dull
        out += lp(noise, k) * np.exp(-((t - 0.05 * k / 6) ** 2) / 0.002)
    return out * 0.6


def shimmer(d=1.0):
    n = int(d * SR)
    out = np.zeros(n)
    for k, m in enumerate((72, 76, 79, 83, 88)):
        st = int(k * d / 8 * SR)
        seg = tone(hz(m), d - k * d / 8, 3)
        out[st:st + len(seg)] += seg
    sweep = lp(rng.normal(0, 1, n), 4) * np.linspace(0, 1, n) * 0.3
    return (out * 0.25 + sweep) * np.minimum(1, (n - np.arange(n)) / (0.3 * SR))


# ---- music: light lo-fi (e-piano chords + soft drums)
def epiano(freqs, d):
    n = int(d * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 3)) for f in freqs)
    return s / len(freqs) * env(n, 0.01, 1.6)


def loop(length):
    beat = 60 / 96
    buf = np.zeros(int(length * SR) + SR)
    chords = [[57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 65], [52, 55, 59, 62]]
    for b in range(int(length / beat) + 1):
        t = b * beat
        if b % 2 == 0:
            ch = chords[(b // 2) % 4]
            put(buf, epiano([hz(m) for m in ch], beat * 2.2), t, 0.3)
            put(buf, tone(hz(ch[0] - 12), beat * 2, 2.5), t, 0.25)
        n = int(0.3 * SR)
        tt = np.arange(n) / SR
        if b % 4 in (0, 3):
            put(buf, np.sin(2 * np.pi * np.cumsum(45 + 80 * np.exp(-tt * 30)) / SR) * env(n, 0.002, 10), t, 0.5)
        if b % 2 == 1:
            put(buf, lp(rng.normal(0, 1, int(0.18 * SR)), 6) * env(int(0.18 * SR), 0.002, 18), t, 0.3)
        put(buf, np.diff(rng.normal(0, 1, 2000), prepend=0) * env(2000, 0.001, 70), t + beat / 2, 0.15)
    return buf[: int(length * SR)]


cut, _ = shot_t('declined')  # (end of the quiet 'judge' stretch)
fz0, fzd = shot_t('freeze')
back, _ = shot_t('pull_out')
pause0 = fz0 + fzd - 0.7  # the one pause: right before 'Okay, real money is a bit much'
judge_end = cut
end0, _ = shot_t('endcard')
m1 = loop(pause0)
m1[-400:] *= np.linspace(1, 0, 400)
put(music, m1, 0.0)
m2 = loop(DUR - back)
m2[: int(0.5 * SR)] *= np.linspace(0, 1, int(0.5 * SR))
put(music, m2, back, 0.9)

# ---- subway bed: rumble, wheel clacks (pairs), faint motor whine
t = np.arange(N) / SR
rumble = lp(lp(rng.normal(0, 1, N), 60), 60) * 3.0 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.3 * t))
bed = rumble + 0.02 * np.sin(2 * np.pi * (180 + 6 * np.sin(2 * np.pi * 0.1 * t)) * t)
for c in np.arange(0.4, DUR, 1.15):
    for dt in (0.0, 0.11):
        n = int(0.12 * SR)
        put(bed, lp(rng.normal(0, 1, n), 10) * env(n, 0.001, 35) * 1.2, c + dt)

# the 'judge that one guy' stretch: the car goes quiet, only his scrolling is heard (far off)
judge0, _ = shot_t('judge')
quiet = np.ones(N)
a, b = int(judge0 * SR), int(cut * SR)
ramp = int(0.25 * SR)
quiet[a:b] = 0.12
quiet[a:a + ramp] = np.linspace(1, 0.12, ramp)
for x in events('kaching'):
    far = judge0 <= x < cut
    put(fx, lp(kaching(), 6) if far else kaching(), x, 0.1 if far else 0.16)
for x in events('buzz'):
    put(fx, buzz(), x, 0.35)
for x in events('whip'):
    put(fx, glance(), x, 0.25)
# the quiet judge stretch ends when the card is declined
r = int(0.15 * SR)
quiet[int(judge_end * SR):int(judge_end * SR) + r] = np.linspace(0.12, 1, r)
for x in events('whoosh'):
    put(fx, shimmer(1.1), x, 0.6)
for x in events('coin'):
    put(fx, tone(1568, 0.25, 14), x, 0.18)
    put(fx, tone(2093, 0.2, 16), x + 0.05, 0.12)
for x in events('chime'):
    for k, f in enumerate((1047, 1319, 1568, 2093)):
        put(fx, tone(f, 0.9, 4), x + k * 0.06, 0.18)
for tt_, f in ((0.0, 880), (0.25, 1175), (1.0, 1568)):
    put(fx, tone(f, 0.2, 18), end0 + tt_, 0.22)
put(music, epiano([hz(m) for m in (48, 55, 64, 67, 72)], 2.4), end0 + 0.2, 0.45)

vo = np.zeros(N)
if len(sys.argv) > 3:
    with wave.open(sys.argv[3]) as w:
        v = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    vo[:min(N, len(v))] = v[:N]
    venv = np.convolve(np.abs(vo), np.ones(2205) / 2205, mode='same')
    music *= 1 - np.clip(venv * 8, 0, 0.6)
    fx *= 1 - np.clip(venv * 3, 0, 0.3)
mix = music * 0.5 * quiet + fx + bed * 0.12 * np.maximum(quiet, 0.4) + vo * 0.85
mix = np.tanh(mix * 1.15) * 0.88
L = int(DUR * SR)
pcm = (np.stack([mix[:L], mix[:L]], 1) * 32767).astype(np.int16)
with wave.open(OUT, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('audio', OUT, round(DUR, 2), 's')
