"""Post for the PS1 'Day' short: grade per act, shake/flash, PS1 palette + Bayer
dither, nearest-neighbour upscale, pixel-font HUD.
Usage: python3 post_day.py <ps1day_dir> <out_dir> <width>"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import pixfont as pf
from ps1post import BAYER

src, dst, W = sys.argv[1], sys.argv[2], int(sys.argv[3])
H = W * 16 // 9
os.makedirs(dst, exist_ok=True)
meta = json.load(open(os.path.join(src, 'meta.json')))
total = meta['total']
M = {int(k): v for k, v in meta['frames'].items()}

GRADES = {
    # (saturation, rgb multiplier, lift)
    'trance': (0.45, (0.9, 1.0, 1.12), -0.04),
    'warm': (1.15, (1.06, 1.0, 0.93), 0.0),
    'golden': (1.2, (1.14, 1.0, 0.82), 0.03),
}


def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def grade(a, name):
    sat, mul, lift = GRADES.get(name, (1, (1, 1, 1), 0))
    lum = (a * np.array([0.299, 0.587, 0.114])).sum(-1, keepdims=True)
    a = lum + (a - lum) * sat
    return np.clip(a * np.array(mul) + lift, 0, 1)


def ps1(a, bits=5):
    h, w, _ = a.shape
    levels = 2 ** bits - 1
    th = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    return np.clip(np.floor(a * levels + 0.5 + th) / levels, 0, 1)


def hud(img, items):
    """Old-game HUD box, top-left inside the TikTok/Reels safe area."""
    k = W / 270  # 1 HUD pixel at 270w
    d = ImageDraw.Draw(img, 'RGBA')
    x0 = int(18 * k)
    y = int(H * 0.125)
    for label, value, col in items:
        ls, vs = max(1, round(1 * k)), max(2, round(3 * k))
        lw, lh = pf.text_size(label, ls)
        vw, vh = pf.text_size(value, vs)
        bw = max(lw, vw) + int(10 * k)
        bh = lh + vh + int(12 * k)
        d.rectangle([x0, y, x0 + bw, y + bh], fill=(10, 8, 18, 190), outline=(255, 255, 255, 230), width=max(1, int(k)))
        pf.draw(img, (x0 + int(5 * k), y + int(4 * k)), label, (200, 190, 230), ls)
        pf.draw(img, (x0 + int(5 * k), y + int(4 * k) + lh + int(3 * k)), value, hexrgb(col), vs, shadow=(0, 0, 0))
        y += bh + int(6 * k)


last = None
for g in range(1, total + 1):
    p = os.path.join(src, 'frames', f'{g:04d}.png')
    if os.path.exists(p):
        last = np.asarray(Image.open(p).convert('RGB')).astype(np.float32) / 255
    if last is None:
        continue
    m = M.get(g, {})
    a = grade(last, m.get('grade', 'warm'))
    sh = m.get('shake', 0)
    if sh:
        rnd = np.random.default_rng(g)
        dx, dy = (rnd.integers(-6, 7, 2) * sh).astype(int)
        a = np.roll(a, (dy, dx), axis=(0, 1))
    fl = m.get('flash', 0)
    if fl:
        a = a * (1 - fl) + fl
    a = ps1(a)
    img = Image.fromarray((a * 255).astype(np.uint8)).resize((W, H), Image.NEAREST)
    if m.get('hud'):
        hud(img, m['hud'])
    img.save(os.path.join(dst, f'{g:04d}.png'))
print('post', total)
