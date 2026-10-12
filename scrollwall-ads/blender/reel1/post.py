"""Reel 1 post: PS1 look (bloom, dither, chunky upscale), reference-style
subtitles, CCTV overlay for the front-camera shots, slam shake.

Usage: python3 post.py <reel_dir> <frames_subdir> <out_dir> <width>
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ps1v2'))
from v2post import look  # noqa: E402

REEL, SUB, OUT, W = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
H = W * 16 // 9
os.makedirs(OUT, exist_ok=True)
T = json.load(open(os.path.join(REEL, 'timings.json')))
META = {int(k): v for k, v in json.load(open(os.path.join(REEL, 'meta.json')))['frames'].items()}
FONT = os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'fonts', 'Inter-SemiBold.otf')
sub_font = ImageFont.truetype(FONT, max(12, int(W * 0.042)))
hud_font = ImageFont.truetype(FONT, max(10, int(W * 0.05)))
FPS = T['fps']


def chunks(line, n=3):
    words = line.split()
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= n or w.endswith(('.', ',', '?')):
            out.append(' '.join(cur))
            cur = []
    if cur:
        out.append(' '.join(cur))
    return out


# subtitle timeline: chunks spread over each line's spoken length
SUBS = []
for sh in T['shots']:
    parts = chunks(sh['line'])
    total = sum(len(p) for p in parts)
    t0 = sh['start'] + 0.05
    for p in parts:
        d = sh['vo_len'] * len(p) / total
        SUBS.append((t0, t0 + d + 0.12, p.rstrip('.,')))
        t0 += d


def sub_at(t):
    for a, b, txt in SUBS:
        if a <= t < b:
            return txt
    return None


def outlined(d, xy, text, font, fill=(255, 255, 255), stroke=2, anchor='mm'):
    d.text(xy, text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0), anchor=anchor)


def tc(sec):
    f = int((sec % 1) * 30)
    sec = int(sec)
    return f'{sec // 3600:02d}:{sec // 60 % 60:02d}:{sec % 60:02d}:{f:02d}'


last = None
for g in range(1, T['total_frames'] + 1):
    p = os.path.join(REEL, SUB, f'{g:04d}.png')
    if os.path.exists(p):
        last = look(Image.open(p), W)
        last_meta = META.get(g, {})
    if last is None:
        continue
    m = META.get(g, last_meta)
    img = last.copy()
    if m.get('shake'):
        dx = int(np.sin(g * 2.7) * 10 * m['shake'] * W / 540)
        img = Image.fromarray(np.roll(np.asarray(img), dx, axis=1))
    d = ImageDraw.Draw(img)
    cc = m.get('cctv')
    if cc:
        outlined(d, (int(W * 0.07), int(H * 0.13)), cc['cam'], hud_font, anchor='lm')
        outlined(d, (int(W * 0.93), int(H * 0.13)), tc(cc['clock'] + (g % 30) / 30), hud_font, anchor='rm')
        bx, by, bs = cc['box']
        side = int(bs * H)
        x, y = int(bx * W), int(by * H)
        d.rectangle([x - side // 2, y - side // 2, x + side // 2, y + side // 2], outline=(255, 255, 255), width=max(2, W // 270))
        if cc.get('tag'):
            outlined(d, (x + side // 2 + 6, y - side // 2), cc['tag'], sub_font, anchor='lt')
    txt = sub_at((g - 1) / FPS)
    if txt:
        outlined(d, (W // 2, int(H * 0.585)), txt.lower(), sub_font, stroke=max(2, W // 270))
    img.save(os.path.join(OUT, f'{g:04d}.png'))
print('post done', T['total_frames'])
