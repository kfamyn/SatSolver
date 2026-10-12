"""Reel 2 — 'What if scrolling cost money?' (subway). Beats = narrator lines + shots.
Captions are the spoken text. With VO_PLAN (vo_kokoro.py plan) beats stretch to fit
the voice at a natural pace.
Usage: [VO_PLAN=plan.json] python3 script.py <out_dir>
"""
import json
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/user/reel4'
FPS = 30
PLAN = os.environ.get('VO_PLAN')
GAP = 0.1  # tight: each beat is as long as its line + a breath
MIN_SHOT = 0.35
PAUSE_AFTER = {"Two stops later? Broke.": 0.7}  # the one deliberate pause, before 'Okay, real money...'
FIXED = {'endcard'}

BEATS = [
    ("What if scrolling cost money?", [('hook_pov', 1.0), ('hook_face', 0.7)]),
    ("One cent. Every swipe.", [('ticker', 1.6)]),
    ("The subway would go quiet.", [('aisle', 1.7)]),
    ("People would read again.", [('paper', 0.9), ('book', 0.8)]),
    ("You'd make eye contact.", [('eyes1', 0.7), ('eyes2', 0.7), ('eyes_away', 0.9)]),
    ("And judge that one guy.", [('judge', 1.0), ('frantic', 1.3)]),
    ("Two stops later? Broke.", [('declined', 0.9), ('freeze', 0.8)]),
    ("Okay, real money is a bit much.", [('pull_out', 1.5)]),
    ("So we made scrolling cost focus.", [('shield', 1.0), ('purple_face', 0.8)]),
    ("Earn coins by focusing. Spend them to scroll.", [('hero_read', 1.5), ('tilt', 1.2)]),
    ("Scrollwall: your scroll paywall.", [('endcard', 2.4)]),
]


def fit(cap, seq):
    """beat length = line length + GAP (+ the one pause), shots scaled to fill it (shrink or stretch)."""
    if not PLAN or any(sid in FIXED for sid, _ in seq):
        return seq
    need = json.load(open(PLAN)).get(cap)
    if need is None:
        return seq
    have = sum(d for _, d in seq)
    k = (need + GAP) / have
    out = [(sid, max(MIN_SHOT, d * k)) for sid, d in seq]
    if cap in PAUSE_AFTER:
        sid, d = out[-1]
        out[-1] = (sid, d + PAUSE_AFTER[cap])
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    shots, caps, t, i = [], [], 0.0, 0
    for cap, seq in BEATS:
        caps.append((t, cap))
        for sid, d in fit(cap, seq):
            n = int(round(d * FPS))
            shots.append({'i': i, 'id': sid, 'start': t, 'dur': n / FPS, 'frames': n, 'line': ''})
            t += n / FPS
            i += 1
    json.dump({'fps': FPS, 'total_frames': int(round(t * FPS)), 'shots': shots, 'captions': caps},
              open(os.path.join(OUT, 'timings.json'), 'w'), indent=1)
    for s_ in shots:
        print(f"{s_['i']:02d} {s_['id']:12s} {s_['start']:5.2f}s +{s_['dur']:.2f}s")
    print('total', round(t, 2), 's,', len(shots), 'shots')


if __name__ == '__main__':
    main()
