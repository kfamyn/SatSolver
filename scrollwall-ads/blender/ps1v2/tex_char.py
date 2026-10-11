"""Painted PS1-era textures for the main character (realistic-ish proportions,
hand-painted face wrapped around a low-poly head). Usage: python3 tex_char.py <out>"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
R = random.Random(4)


def C(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,)


def noise_layer(w, h, amt, seed):
    rng = np.random.default_rng(seed)
    return rng.normal(0, amt, (h, w, 1))


def add_noise(im, amt=6, seed=1):
    a = np.asarray(im).astype(np.float32)
    a[..., :3] += noise_layer(im.width, im.height, amt, seed)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ------------------------------------------------------------------ head
# Cylindrical wrap: x = angle around the head (front at the centre, x=128 of
# 256), y = height (0 = crown, 255 = neck). Painted at 256 then reduced to 128
# so it keeps a soft, hand-painted PS1 feel.
HW, HH = 256, 256
FX = HW // 2
SKIN = C('#DDA88A')
SKIN_SH = C('#B9846A')
SKIN_HI = C('#EEC2A6')
HAIR = C('#2B1E17')
HAIR_HI = C('#4A3426')

EYE_Y = 120
BROW_Y = 104
NOSE_Y = 150
MOUTH_Y = 178
CHIN_Y = 206
HAIRLINE_Y = 66


def head_base():
    im = Image.new('RGBA', (HW, HH), SKIN)
    px = im.load()
    for y in range(HH):
        for x in range(HW):
            ang = abs(x - FX) / (HW / 2)  # 0 front .. 1 back
            side = min(1, ang / 0.5)
            c = mix(SKIN_HI, SKIN, min(1, side * 1.4))
            c = mix(c, SKIN_SH, max(0, side - 0.55) * 1.5)
            if y > CHIN_Y + 8:  # under the jaw / neck shadow
                c = mix(c, SKIN_SH, min(1, (y - CHIN_Y - 8) / 30) * 0.8)
            px[x, y] = c
    d = ImageDraw.Draw(im)
    # hair: crown, back and sides, messy fringe
    d.rectangle([0, 0, HW, HAIRLINE_Y], fill=HAIR)
    d.rectangle([0, 0, FX - 70, 175], fill=HAIR)
    d.rectangle([FX + 70, 0, HW, 175], fill=HAIR)
    for i in range(22):
        x = FX - 66 + i * 6 + R.randint(-2, 2)
        L = R.randint(8, 26)
        d.polygon([(x, HAIRLINE_Y - 4), (x + 8, HAIRLINE_Y - 4), (x + 3 + R.randint(-4, 4), HAIRLINE_Y + L)], fill=HAIR)
    for s in (-1, 1):  # sideburns
        x0 = FX + s * 66
        d.rectangle([min(x0, x0 + s * 10), HAIRLINE_Y, max(x0, x0 + s * 10), 150], fill=HAIR)
    for _ in range(160):
        x, y = R.randint(0, HW - 1), R.randint(0, HAIRLINE_Y)
        d.line([x, y, x + R.randint(-3, 3), y + R.randint(4, 12)], fill=HAIR_HI)
    # ears hint (darker patch where the ears sit)
    for s in (-1, 1):
        d.ellipse([FX + s * 64 - 8, 118, FX + s * 64 + 8, 152], fill=SKIN_SH)
    # nose: bridge highlight + shadowed sides + nostrils
    d.polygon([(FX - 4, EYE_Y + 6), (FX + 4, EYE_Y + 6), (FX + 7, NOSE_Y), (FX - 7, NOSE_Y)], fill=SKIN_HI)
    d.line([FX - 9, EYE_Y + 14, FX - 11, NOSE_Y], fill=SKIN_SH, width=3)
    d.line([FX + 9, EYE_Y + 14, FX + 11, NOSE_Y], fill=SKIN_SH, width=2)
    d.ellipse([FX - 12, NOSE_Y - 2, FX - 4, NOSE_Y + 4], fill=C('#8C5A48'))
    d.ellipse([FX + 4, NOSE_Y - 2, FX + 12, NOSE_Y + 4], fill=C('#8C5A48'))
    # cheekbone shadow + chin
    for s in (-1, 1):
        d.ellipse([FX + s * 44 - 14, 150, FX + s * 44 + 14, 190], fill=mix(SKIN, SKIN_SH, 0.4))
    d.ellipse([FX - 20, CHIN_Y - 10, FX + 20, CHIN_Y + 6], fill=SKIN_HI)
    # stubble
    for _ in range(900):
        x = R.randint(FX - 46, FX + 46)
        y = R.randint(MOUTH_Y - 18, CHIN_Y + 10)
        if abs(x - FX) < 46 - max(0, (y - MOUTH_Y) * 0.3):
            px[x, y] = mix(px[x, y], C('#6E5A55'), 0.35)
    return im


def eyes(im, kind):
    d = ImageDraw.Draw(im)
    INK = C('#1C1214')
    for s in (-1, 1):
        cx = FX + s * 30
        # dark circles: the doomscroller tax
        d.ellipse([cx - 18, EYE_Y + 4, cx + 18, EYE_Y + 20], fill=mix(SKIN, C('#7E5A6E'), 0.45))
        if kind in ('blink', 'closed'):
            d.line([cx - 15, EYE_Y + 2, cx + 15, EYE_Y + 4], fill=INK, width=3)
            continue
        open_h = {'glazed': 6, 'neutral': 9, 'shock': 14, 'focus': 6, 'smile': 5}[kind]
        d.ellipse([cx - 15, EYE_Y - open_h, cx + 15, EYE_Y + open_h], fill=C('#F2EEE8'))
        ir = 7 if kind != 'shock' else 6
        icol = C('#5A3B28')
        ix = cx + (0 if kind != 'glazed' else s * -1)
        iy = EYE_Y + (2 if kind == 'glazed' else 0)
        d.ellipse([ix - ir, iy - ir, ix + ir, iy + ir], fill=icol)
        pr = 3 if kind != 'shock' else 2
        d.ellipse([ix - pr, iy - pr, ix + pr, iy + pr], fill=INK)
        if kind == 'glazed':  # the feed reflected in his eyes
            d.rectangle([ix - 6, iy - 6, ix - 2, iy - 2], fill=C('#9FE6FF'))
            d.rectangle([ix + 2, iy + 1, ix + 4, iy + 3], fill=C('#FF8FC0'))
        else:
            d.ellipse([ix - 5, iy - 5, ix - 2, iy - 2], fill=C('#FFFFFF'))
        # upper lid (heavy when glazed)
        lid = {'glazed': 4, 'neutral': 1, 'shock': 0, 'focus': 3, 'smile': 2}[kind]
        d.chord([cx - 16, EYE_Y - open_h - 2, cx + 16, EYE_Y + open_h + 2], 180, 360, fill=None)
        d.rectangle([cx - 16, EYE_Y - open_h - 2, cx + 16, EYE_Y - open_h + lid * 2], fill=mix(SKIN, SKIN_SH, 0.3))
        d.arc([cx - 16, EYE_Y - open_h - 1, cx + 16, EYE_Y + open_h + 1], 190, 350, fill=INK, width=3)
        if kind == 'smile':
            d.arc([cx - 14, EYE_Y + 2, cx + 14, EYE_Y + 14], 200, 340, fill=mix(SKIN, SKIN_SH, 0.6), width=2)


def brows(im, kind):
    d = ImageDraw.Draw(im)
    for s in (-1, 1):
        cx = FX + s * 30
        if kind == 'shock':
            pts = [(cx - 17, BROW_Y - 8), (cx + 17, BROW_Y - 10)]
        elif kind == 'focus':
            pts = [(cx - s * 17, BROW_Y - 2), (cx + s * 17, BROW_Y + 5)]
        elif kind == 'glazed':
            pts = [(cx - 17, BROW_Y + 2), (cx + 17, BROW_Y + 3)]
        else:
            pts = [(cx - 17, BROW_Y), (cx + 17, BROW_Y - 1)]
        d.line(pts, fill=HAIR, width=6)


def mouth(im, kind):
    d = ImageDraw.Draw(im)
    LIP = C('#A0605A')
    INK = C('#3A1A1E')
    if kind == 'open':
        d.ellipse([FX - 12, MOUTH_Y - 6, FX + 12, MOUTH_Y + 12], fill=INK)
        d.rectangle([FX - 8, MOUTH_Y - 5, FX + 8, MOUTH_Y - 2], fill=C('#EEE6DC'))
    elif kind == 'slack':  # mouth hanging a little open
        d.ellipse([FX - 12, MOUTH_Y - 3, FX + 12, MOUTH_Y + 6], fill=INK)
        d.line([FX - 13, MOUTH_Y - 3, FX + 13, MOUTH_Y - 3], fill=LIP, width=2)
    elif kind == 'smile':
        d.chord([FX - 18, MOUTH_Y - 12, FX + 18, MOUTH_Y + 10], 10, 170, fill=INK)
        d.rectangle([FX - 12, MOUTH_Y - 1, FX + 12, MOUTH_Y + 2], fill=C('#EEE6DC'))
    elif kind == 'tight':
        d.line([FX - 12, MOUTH_Y + 1, FX + 12, MOUTH_Y], fill=INK, width=3)
    else:
        d.line([FX - 14, MOUTH_Y, FX + 14, MOUTH_Y + 1], fill=INK, width=3)
        d.line([FX - 10, MOUTH_Y + 4, FX + 10, MOUTH_Y + 4], fill=LIP, width=2)


def head(name, eye_kind, mouth_kind):
    im = head_base()
    eyes(im, eye_kind)
    brows(im, eye_kind)
    mouth(im, mouth_kind)
    im = add_noise(im, 5, 7).filter(ImageFilter.SMOOTH)
    im.resize((128, 128), Image.LANCZOS).save(f'{OUT}/head_{name}.png')


# ------------------------------------------------------------------ clothes

def hoodie():
    """Wraps the torso: x = around (front centre at 64 of 128), y = top..bottom."""
    W, H = 128, 128
    im = Image.new('RGBA', (W, H), C('#8C8E96'))
    im = add_noise(im, 7, 11)
    d = ImageDraw.Draw(im)
    for _ in range(26):  # baked folds
        x = R.randint(0, W)
        y = R.randint(10, H - 20)
        d.line([x, y, x + R.randint(-12, 12), y + R.randint(8, 22)], fill=C('#73757E'), width=2)
        d.line([x + 2, y, x + 2 + R.randint(-10, 10), y + R.randint(6, 18)], fill=C('#A2A4AB'), width=1)
    # kangaroo pocket
    d.polygon([(42, 84), (86, 84), (92, 112), (36, 112)], fill=C('#7E8088'), outline=C('#62646C'))
    d.line([40, 86, 36, 110], fill=C('#5A5C64'), width=2)
    d.line([88, 86, 92, 110], fill=C('#5A5C64'), width=2)
    # ribbed hem + collar
    for x in range(0, W, 3):
        d.line([x, H - 10, x, H - 1], fill=C('#74767E'))
    d.rectangle([0, 0, W, 6], fill=C('#74767E'))
    # drawstrings
    for s in (-1, 1):
        d.line([64 + s * 8, 4, 64 + s * 9, 46], fill=C('#E8E6E0'), width=3)
        d.rectangle([64 + s * 9 - 2, 44, 64 + s * 9 + 2, 50], fill=C('#C8C6C0'))
    # tiny chest logo + a coffee stain (relatable)
    d.rectangle([74, 26, 86, 32], fill=C('#5A5C64'))
    d.ellipse([46, 60, 54, 66], fill=C('#6E6458'))
    # back seam darker
    d.line([0, 0, 0, H], fill=C('#6C6E76'), width=4)
    d.line([W - 1, 0, W - 1, H], fill=C('#6C6E76'), width=4)
    im.save(f'{OUT}/hoodie.png')
    # sleeves: same fabric, cuff ribbing at the bottom
    im = Image.new('RGBA', (64, 128), C('#8C8E96'))
    im = add_noise(im, 7, 12)
    d = ImageDraw.Draw(im)
    for _ in range(12):
        y = R.randint(10, 110)
        d.line([0, y, 63, y + R.randint(-6, 6)], fill=C('#76787F'), width=2)
    for x in range(0, 64, 3):
        d.line([x, 116, x, 127], fill=C('#74767E'))
    im.save(f'{OUT}/sleeve.png')


def pants():
    im = Image.new('RGBA', (64, 128), C('#4A4C55'))
    im = add_noise(im, 6, 13)
    d = ImageDraw.Draw(im)
    for _ in range(14):
        y = R.randint(0, 120)
        d.line([0, y, 63, y + R.randint(4, 14)], fill=C('#3C3E46'), width=2)
    d.line([32, 0, 32, 127], fill=C('#3A3C44'))
    for x in range(0, 64, 3):
        d.line([x, 118, x, 127], fill=C('#3E4048'))
    im.save(f'{OUT}/pants.png')


def socks():
    im = Image.new('RGBA', (32, 32), C('#ECEAE6'))
    im = add_noise(im, 5, 14)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 26, 31, 31], fill=C('#C9C6BF'))  # grubby soles
    d.line([0, 4, 31, 4], fill=C('#8E6BD4'), width=2)
    im.save(f'{OUT}/socks.png')


def hand():
    im = Image.new('RGBA', (32, 32), SKIN)
    im = add_noise(im, 5, 15)
    d = ImageDraw.Draw(im)
    for x in (8, 15, 22):  # finger gaps
        d.line([x, 0, x, 14], fill=SKIN_SH, width=1)
    d.rectangle([0, 28, 31, 31], fill=SKIN_SH)
    im.save(f'{OUT}/hand.png')


def hair_tex():
    im = Image.new('RGBA', (64, 64), HAIR)
    d = ImageDraw.Draw(im)
    for _ in range(220):
        x, y = R.randint(0, 63), R.randint(0, 63)
        d.line([x, y, x + R.randint(-4, 4), y + R.randint(3, 9)], fill=HAIR_HI if R.random() < 0.6 else C('#1A120E'))
    im.save(f'{OUT}/hair.png')


def phone_back():
    im = Image.new('RGBA', (32, 64), C('#1E2A3A'))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3, 3, 14, 18], radius=3, fill=C('#11161E'))
    for cx, cy in [(7, 8), (11, 13)]:
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=C('#05070A'), outline=C('#5A6678'))
    im.save(f'{OUT}/phone_back.png')


for name, e, m in [('glazed', 'glazed', 'slack'), ('neutral', 'neutral', 'flat'), ('shock', 'shock', 'open'),
                   ('focus', 'focus', 'tight'), ('smile', 'smile', 'smile'), ('blink', 'blink', 'flat'),
                   ('glazed_blink', 'blink', 'slack')]:
    head(name, e, m)
hoodie(); pants(); socks(); hand(); hair_tex(); phone_back()
print('char textures ok')
