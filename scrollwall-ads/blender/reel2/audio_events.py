"""meta.json with only the sound events (same rules as render.py), without rendering.
Usage: python3 audio_events.py <reel_dir>"""
import json
import os
import sys

REEL = sys.argv[1]
T = json.load(open(os.path.join(REEL, 'timings.json')))
frames, g = {}, 0
for sh in T['shots']:
    n, sid = sh['frames'], sh['id']
    for t in range(n):
        g += 1
        m = {}
        if sid == 'hook_pov':
            m['kaching'] = t == 14
        elif sid == 'ticker':
            m['kaching'] = t % 8 == 0
        elif sid == 'frantic':
            m['kaching'] = t % 3 == 0
        elif sid == 'judge':
            m['kaching'] = t % 4 == 0
        elif sid == 'eyes_away':
            m['whip'] = t == min(8, n - 4)
        elif sid == 'declined':
            m['buzz'] = t == 0
        elif sid == 'shield':
            m['whoosh'] = t == 0
        elif sid == 'hero_read':
            m['coin'] = t >= 4 and (t - 4) % 9 == 0
        elif sid == 'tilt':
            m['chime'] = t == int(0.55 * (n - 1)) + 1
        frames[g] = {k: v for k, v in m.items() if v}
json.dump({'total': T['total_frames'], 'frames': frames}, open(os.path.join(REEL, 'meta.json'), 'w'))
print('events', sum(len(v) for v in frames.values()))
