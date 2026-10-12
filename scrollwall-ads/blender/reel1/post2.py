"""Reel 1 v2 post: PS1 look, shake, hit flash, CCTV overlay, and (preview only)
TikTok-style caption boxes where the in-app text-to-speech lines will sit.

Usage: python3 post2.py <reel_dir> <frames_subdir> <out_dir> <width> [clean]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ps1v2'))
from v2post import look  # noqa: E402

REEL, SUB, OUT, W = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
CLEAN = len(sys.argv) > 5 and sys.argv[5] == 'clean'
H = W * 16 // 9
os.makedirs(OUT, exist_ok=True)
T = json.load(open(os.path.join(REEL, 'timings.json')))
META = {int(k): v for k, v in json.load(open(os.path.join(REEL, 'meta.json')))['frames'].items()}
FONTS = os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'fonts')
cap_font = ImageFont.truetype(os.path.join(FONTS, 'Inter-ExtraBold.otf'), max(12, int(W * 0.056)))
hud_font = ImageFont.truetype(os.path.join(FONTS, 'Inter-SemiBold.otf'), max(10, int(W * 0.05)))
FPS = T['fps']
END = T['total_frames'] / FPS
CAPS = [(c[0], (T['captions'][i + 1][0] if i + 1 < len(T['captions']) else END), c[1]) for i, c in enumerate(T['captions'])]


def cap_at(t):
    for a, b, txt in CAPS:
        if a <= t < b:
            return txt
    return None


def wrap(d, text, font, maxw):
    lines, cur = [], ''
    for w in text.split():
        nxt = (cur + ' ' + w).strip()
        if d.textlength(nxt, font=font) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = nxt
    return lines + [cur]


def tiktok_caption(img, text):
    """TikTok 'classic' text style: bold white, soft black outline, centered."""
    d = ImageDraw.Draw(img)
    lines = wrap(d, text, cap_font, W * 0.8)
    lh = int(cap_font.size * 1.25)
    y = int(H * 0.66) - lh * len(lines) // 2
    for ln in lines:
        d.text((W // 2, y), ln, font=cap_font, fill=(255, 255, 255), stroke_width=max(2, W // 180),
               stroke_fill=(0, 0, 0), anchor='mt')
        y += lh


def outlined(d, xy, text, font, fill=(255, 255, 255), stroke=2, anchor='mm'):
    d.text(xy, text, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0), anchor=anchor)


def tc(sec):
    f = int((sec % 1) * 30)
    sec = int(sec)
    return f'{sec // 3600:02d}:{sec // 60 % 60:02d}:{sec % 60:02d}:{f:02d}'


last, last_meta = None, {}
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
        a = np.asarray(img)
        dx = int(np.sin(g * 2.7) * 12 * m['shake'] * W / 540)
        dy = int(np.cos(g * 3.3) * 8 * m['shake'] * W / 540)
        img = Image.fromarray(np.roll(np.roll(a, dx, axis=1), dy, axis=0))
    if m.get('flash'):
        img = Image.blend(img, Image.new('RGB', img.size, (190, 160, 255)), min(0.8, m['flash']))
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
            outlined(d, (W // 2, int(H * 0.22)), cc['tag'], hud_font)
    if not CLEAN:
        txt = cap_at((g - 1) / FPS)
        if txt:
            tiktok_caption(img, txt)
    img.save(os.path.join(OUT, f'{g:04d}.png'))
print('post done', T['total_frames'], 'clean' if CLEAN else 'preview')
