"""Reel 1 v2 — tight cut (~20 s) paced for TikTok's built-in text-to-speech.

Each caption is added in TikTok as a text box with Text-to-speech on; TikTok's
voice reads ~3 words/s. Shots are 0.6-2.6 s. Writes timings.json + captions.md.
Usage: [VO_PLAN=plan.json] python3 script2.py <out_dir>
"""
import json
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/user/reel2'
FPS = 30

# (caption for TikTok TTS, [(shot id, seconds), ...])
BEATS = [
    ("you open tiktok for 5 minutes", [('wide', 0.9), ('swipe_pov', 0.9)]),
    ("5 minutes turns into 3 hours", [('clock', 0.9), ('overhead', 1.0)]),
    ("screen time warns you. you tap ignore", [('limit', 0.9), ('face_blank', 0.6), ('ignore_tap', 0.8)]),
    ("you swipe again... and hit a wall", [('swipe_bounce', 0.9), ('wall_rise', 0.8), ('face_recoil', 0.6)]),
    ("a scrollwall.", [('wall_hero', 1.2)]),
    ("you have to pay to scroll", [('shield', 0.9), ('face_stare', 0.7)]),
    ("so you actually focus", [('desk', 0.8), ('desk_top', 0.7)]),
    ("every focused minute earns coins", [('coins', 0.9), ('balance', 0.9)]),
    ("pay with your focus card. tilt to spend", [('pay_pov', 0.8), ('tilt', 0.9), ('unlocked', 0.6)]),
    ("and the wall lets you through", [('wall_open', 1.6)]),
    ("5 guilt-free minutes", [('golden', 1.3)]),
    # comic beat: music cuts, he freezes, looks up... wall slams back, phone goes flying.
    # The caption lands on the hit (offset), so the silence stays silent.
    ("then it's back.", [('wall_back', 2.6)], 1.15),
    ("scrollwall. download it on the app store", [('endcard', 2.4)]),
]


PLAN = os.environ.get('VO_PLAN')  # vo_kokoro.py plan: stretch beats so each line fits at a natural pace
FIXED = {'wall_back'}  # comic timing stays as cut
GAP = 0.25  # breath between lines


def fit(cap, seq, offset):
    if not PLAN or any(sid in FIXED for sid, _ in seq):
        return seq
    need = json.load(open(PLAN)).get(cap)
    have = sum(d for _, d in seq) - offset
    if need is None or need + GAP <= have:
        return seq
    k = (need + GAP + offset) / sum(d for _, d in seq)
    return [(sid, d * k) for sid, d in seq]


def main():
    os.makedirs(OUT, exist_ok=True)
    shots, caps = [], []
    t = 0.0
    i = 0
    for beat in BEATS:
        cap = beat[0]
        seq = fit(cap, beat[1], beat[2] if len(beat) > 2 else 0.0)
        caps.append((t + (beat[2] if len(beat) > 2 else 0.0), cap))
        for sid, d in seq:
            n = int(round(d * FPS))
            shots.append({'i': i, 'id': sid, 'start': t, 'dur': n / FPS, 'frames': n, 'line': ''})
            t += n / FPS
            i += 1
    total = int(round(t * FPS))
    json.dump({'fps': FPS, 'total_frames': total, 'shots': shots, 'captions': caps}, open(os.path.join(OUT, 'timings.json'), 'w'), indent=1)
    with open(os.path.join(OUT, 'captions.md'), 'w') as f:
        f.write('# TikTok text-to-speech captions\n\nAdd each line as a text box starting at the time shown, tap Text-to-speech, pick the voice.\n\n')
        for k, (ts, cap) in enumerate(caps):
            end = caps[k + 1][0] if k + 1 < len(caps) else t
            f.write(f'- {ts:05.2f}s – {end:05.2f}s  "{cap}"\n')
    for s_ in shots:
        print(f"{s_['i']:02d} {s_['id']:13s} {s_['start']:5.2f}s +{s_['dur']:.2f}s")
    print('total', round(t, 2), 's,', len(shots), 'shots')


if __name__ == '__main__':
    main()
