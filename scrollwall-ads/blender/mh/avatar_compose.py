"""Compose the profile pictures: violet force-field background + ghost peeking over
his shoulder + the rendered character, cropped on his head, PS1 dither, 1080x1080.
Also writes a circle-cropped preview sheet (how TikTok / Instagram show it).

Usage: python3 avatar_compose.py [in_dir] [out_dir]
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ps1v2'))
from v2post import look  # noqa: E402

IN = sys.argv[1] if len(sys.argv) > 1 else '/home/user/avatar'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/home/user/SatSolver/scrollwall-ads/out/avatar'
os.makedirs(OUT, exist_ok=True)
S = 320  # working resolution (PS1-ish), upscaled at the end


def head_box(a):
    """top row, chin-ish row and centre column of the head from the alpha matte."""
    rows = np.where(a.max(1) > 128)[0]
    top = rows[0]
    # head width per row: the neck is the narrowest point below the head
    widths = [(a[r] > 128).sum() for r in range(top, a.shape[0])]
    lo, hi = int(len(widths) * 0.25), int(len(widths) * 0.6)
    neck = top + lo + int(np.argmin(widths[lo:hi]))
    band = a[top:neck] > 128
    cols = np.where(band.any(0))[0]
    return top, neck, (cols[0] + cols[-1]) / 2


def background(variant):
    bg = Image.new('RGB', (S, S))
    d = ImageDraw.Draw(bg)
    for y in range(S):  # vertical violet gradient
        k = y / S
        d.line([(0, y), (S, y)], fill=(int(70 - 40 * k), int(40 - 25 * k), int(170 - 90 * k)))
    if variant == 'glow':
        bg = Image.eval(bg, lambda v: int(v * 0.45))
        d = ImageDraw.Draw(bg)
    r = 14
    hexc = (150, 120, 255) if variant != 'glow' else (80, 60, 150)
    for row in range(-1, int(S / (r * 1.5)) + 2):
        for col in range(-1, int(S / (r * math.sqrt(3))) + 2):
            cx = col * r * math.sqrt(3) + (row % 2) * r * math.sqrt(3) / 2
            cy = row * r * 1.5
            pts = [(cx + r * math.cos(math.radians(60 * k + 30)), cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)]
            d.polygon(pts, outline=hexc)
    for y in range(0, S, 4):
        d.line([(0, y), (S, y)], fill=tuple(int(c * 0.8) for c in bg.getpixel((0, y))))
    return bg


def ghost(img, cx, cy, w, h, alpha=255):
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2], radius=w // 2, fill=(240, 236, 255, alpha))
    for ex in (-w // 5, w // 5):
        d.rectangle([cx + ex - w // 14, cy - h // 6, cx + ex + w // 14, cy + h // 30], fill=(25, 20, 45, alpha))
    glow = lay.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(glow)
    img.alpha_composite(lay)


def compose(variant, ghost_side=1):
    ch = Image.open(os.path.join(IN, f'char_{variant}.png')).convert('RGBA')
    a = np.asarray(ch)[:, :, 3]
    top, neck, cx = head_box(a)
    head_h = neck - top
    side = int(head_h * 2.05)
    x0 = int(cx - side / 2)
    y0 = int(top - side * 0.13)
    crop = ch.crop((x0, y0, x0 + side, y0 + side)).resize((S, S), Image.BILINEAR)
    img = background(variant).convert('RGBA')
    # ghost peeking from behind his shoulder, inside the circle
    gx = S // 2 + ghost_side * int(S * 0.31)
    ghost(img, gx, int(S * 0.58), int(S * 0.19), int(S * 0.32), 255 if variant != 'glow' else 200)
    # soft violet rim glow around him
    halo = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    halo.putalpha(crop.split()[3].filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.6)))
    tint = Image.new('RGBA', (S, S), (170, 140, 255, 0))
    tint.putalpha(halo.split()[3])
    img.alpha_composite(tint)
    img.alpha_composite(crop)
    out = look(img.convert('RGB'), 1080, bloom=0.5)
    out.save(os.path.join(OUT, f'avatar_{variant}.png'))
    return out


def circle_preview(ims):
    n = len(ims)
    sheet = Image.new('RGB', (n * 360 + (n + 1) * 20, 400), (18, 18, 22))
    mask = Image.new('L', (360, 360), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 359, 359], fill=255)
    for i, im in enumerate(ims):
        sheet.paste(im.resize((360, 360), Image.LANCZOS), (20 + i * 380, 20), mask)
    sheet.save(os.path.join(OUT, 'avatar_preview.png'))


ims = [compose('wall', 1), compose('front', -1), compose('glow', 1)]
circle_preview(ims)
print('saved to', OUT)
