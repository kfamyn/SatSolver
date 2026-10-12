"""Reel 1 — "How the Scrollwall works". Shot list mirroring the reference's
rhythm (shot lengths measured from it), second-person narration, then TTS.

Usage: python3 script.py <out_dir>   -> vo_XX.wav + timings.json
"""
import json
import os
import subprocess
import sys
import wave

OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/user/reel1'
PIPER = '/home/user/ttsenv/bin/piper'
VOICE = '/home/user/voices/en_US-ryan-high.onnx'
FPS = 30

# (id, reference shot length s, camera/shot idea, narration)
SHOTS = [
    ('wide', 1.30, 'establishing wide, slow push-in', 'Imagine you have'),
    ('phone_pov', 1.13, 'first-person insert: the phone in your hand', 'a phone'),
    ('ots', 5.00, 'over-the-shoulder, slow push toward the screen', 'that never runs out of videos. You open it for five minutes.'),
    ('clock', 5.13, 'wall clock close-up, hands spinning (time-lapse), slow push', 'But the clock keeps moving, and your thumb keeps scrolling.'),
    ('face', 1.70, 'face close-up lit by the phone, slow push', 'For hours.'),
    ('overhead', 5.23, 'top-down over the bed, slowly rotating, sun beam crawling', 'The whole afternoon disappears. Screen Time warns you,'),
    ('ignore', 2.20, 'phone screen close-up: Screen Time limit, tap Ignore', 'but you tap ignore.'),
    ('frontcam', 3.77, "the phone's front camera as CCTV: HUD + face box", "What you don't know, is that Scrollwall is counting."),
    ('wall', 2.70, 'phone screen close-up: the scrollwall slams down', 'You hit a scroll wall.'),
    ('face2', 4.03, 'face close-up, slow push-in', 'There is no ignore button. And your balance is zero.'),
    ('desk', 4.27, 'desk wide, slow dolly: he sits down to work', 'So you sit down, and actually focus.'),
    ('desk_top', 3.73, 'top-down over the desk, coins dropping, time-lapse', 'Every focused minute earns you coins.'),
    ('balance', 1.27, 'phone insert: balance 50', 'Fifty.'),
    ('pay_pov', 4.67, 'first-person: hands hold the phone, unlock offer', 'You pay with your Focus Card, to unlock five minutes.'),
    ('tilt', 4.57, 'front-cam CCTV again: he tilts the phone to spend', 'Tilt to spend, and the feed is yours again.'),
    ('end', 6.17, 'golden-hour wide, slow pull back, calm scrolling', 'Guilt free. Until the wall comes back.'),
]


def wav_len(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def main():
    os.makedirs(OUT, exist_ok=True)
    t = 0.0
    timings = []
    for i, (sid, ref, idea, line) in enumerate(SHOTS):
        wav = os.path.join(OUT, f'vo_{i:02d}.wav')
        subprocess.run([PIPER, '-m', VOICE, '-f', wav, '--length_scale', '0.95'], input=line.encode(), check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        vo = wav_len(wav)
        dur = max(ref, vo + 0.25)
        frames = int(round(dur * FPS))
        timings.append({'i': i, 'id': sid, 'idea': idea, 'line': line, 'start': t, 'dur': frames / FPS, 'frames': frames,
                        'vo': wav, 'vo_len': vo, 'ref': ref})
        t += frames / FPS
    json.dump({'fps': FPS, 'total_frames': int(round(t * FPS)), 'shots': timings}, open(os.path.join(OUT, 'timings.json'), 'w'), indent=1)
    for s in timings:
        print(f"{s['i']:02d} {s['id']:10s} ref {s['ref']:.2f}s -> {s['dur']:.2f}s  vo {s['vo_len']:.2f}s  | {s['line']}")
    print('total', round(t, 2), 's')


if __name__ == '__main__':
    main()
