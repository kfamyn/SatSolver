"""Voice-over with Kokoro (open-weights TTS, Apache-2.0), one line per caption beat,
each squeezed (speed) to fit its slot. Writes a full-length mono VO track at 44.1 kHz
+ <out>_caps.json (captions as spoken, with their real start times).

Run with the kokoro venv:
  /home/user/kokenv/bin/python vo_kokoro.py <reel_dir> <voice> <out.wav> [style]
style: plain | whisper (extra breath, softer, closer) ; voices: af_nicole (whispery),
am_santa (Santa), af_heart (natural), bm_fable (storyteller) ...
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

REEL, VOICE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
STYLE = sys.argv[4] if len(sys.argv) > 4 else 'plain'
K = Kokoro('/home/user/kokoro/kokoro-v1.0.onnx', '/home/user/kokoro/voices-v1.0.bin')
T = json.load(open(os.path.join(REEL, 'timings.json')))
SR = 44100
DUR = T['total_frames'] / T['fps']

# spoken versions of the on-screen captions (numbers spelled out, brand split so it's said right)
SAY = {
    "you open tiktok for 5 minutes": "You open TikTok, for five minutes.",
    "5 minutes turns into 3 hours": "Five minutes turns into three hours.",
    "screen time warns you. you tap ignore": "Screen Time warns you. You tap ignore.",
    "you swipe again... and hit a wall": "You swipe again... and hit a wall.",
    "a scrollwall.": "A scroll wall.",
    "no ignore button. zero coins": "No ignore button. Zero coins.",
    "so you actually focus": "So you actually focus.",
    "every focused minute earns coins": "Every focused minute earns coins.",
    "pay with your focus card. tilt to spend": "Pay with your Focus Card. Tilt to spend.",
    "and the wall lets you through": "And the wall lets you through.",
    "5 guilt-free minutes": "Five guilt-free minutes.",
    "then it's back.": "Then it's back.",
    "scrollwall. download it on the app store": "Scroll wall. Download it on the App Store.",
}
# whispers are slow: a tighter script for the whisper style
SAY_WHISPER = {
    "you open tiktok for 5 minutes": "Five minutes of TikTok.",
    "5 minutes turns into 3 hours": "Three hours later.",
    "screen time warns you. you tap ignore": "Screen Time warns you. Ignore.",
    "you swipe again... and hit a wall": "Swipe again... a wall.",
    "a scrollwall.": "A scroll wall.",
    "no ignore button. zero coins": "Zero coins left.",
    "so you actually focus": "So you focus.",
    "every focused minute earns coins": "Focus earns coins.",
    "pay with your focus card. tilt to spend": "Focus Card. Tilt to pay.",
    "and the wall opens": "The wall opens.",
    "and the wall lets you through": "The wall opens.",
    "5 guilt-free minutes": "Five guilt-free minutes.",
    "then it's back.": "Then it's back.",
    "scrollwall. download it on the app store": "Scroll wall. On the App Store.",
}
# extra room a line may spill into (the music still runs for 0.4 s of the next shot)
SPILL = {"5 guilt-free minutes": 0.35}


def synth(text, speed):
    a, sr = K.create(text, voice=VOICE, speed=speed, lang='en-gb' if VOICE.startswith('b') else 'en-us')
    a = np.asarray(a, dtype=np.float32)
    nz = np.where(np.abs(a) > 0.01)[0]  # trim leading/trailing silence
    a = a[max(0, nz[0] - 200):nz[-1] + 800] if len(nz) else a
    x = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
    return np.interp(x, np.arange(len(a)), a)


def whisperize(a):
    """breathier and closer: keep the voice, add shaped breath noise following its envelope."""
    rng = np.random.default_rng(3)
    env = np.convolve(np.abs(a), np.ones(441) / 441, mode='same')
    hiss = np.convolve(rng.normal(0, 1, len(a)), [1, -0.85], mode='same') * env * 1.6
    return a * 0.8 + hiss


MAXSPEED = 1.32
track = np.zeros(int(DUR * SR) + SR, dtype=np.float32)
caps = T['captions']
prev_end = 0.0
shown = []  # captions as actually spoken, for the burned-in preview
for i, (t0, cap) in enumerate(caps):
    t1 = caps[i + 1][0] if i + 1 < len(caps) else DUR
    slot = t1 - t0 - 0.12 + SPILL.get(cap, 0.0)
    text = (SAY_WHISPER if STYLE == 'whisper' else SAY).get(cap, cap)
    speed = 1.0
    a = synth(text, speed)
    while len(a) / SR > slot and speed < MAXSPEED:
        speed = min(MAXSPEED, speed * (len(a) / SR) / slot + 0.02)
        a = synth(text, speed)
    if STYLE == 'whisper':
        a = whisperize(a)
    start = max(t0 + 0.04, prev_end + 0.06)  # never overlap the previous line
    prev_end = start + len(a) / SR
    st = int(start * SR)
    track[st:st + len(a)] += a[: len(track) - st]
    shown.append((start, text.replace('Scroll wall', 'Scrollwall').replace('scroll wall', 'scrollwall').lower().rstrip('.')))
    print(f'{t0:5.2f}s -> {start:5.2f}s  slot {slot:.2f}  got {len(a) / SR:.2f}  speed {speed:.2f}  {text}')
track = track[: int(DUR * SR)]
track /= max(1e-6, np.abs(track).max()) / 0.9
sf.write(OUT, track, SR, subtype='PCM_16')
json.dump(shown, open(OUT.replace('.wav', '_caps.json'), 'w'), indent=1)
print('vo', OUT)
