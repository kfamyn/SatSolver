"""Decal textures for the bedroom: posters, sticky notes, book spines, screens,
can label, pizza box, window view, clock face. Usage: python3 tex_room.py <out>"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ps1'))
import pixfont as pf

OUT = sys.argv[1]
R = random.Random(21)


def C(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def grad(w, h, top, bot):
    a = np.zeros((h, w, 4), np.uint8)
    t, b = np.array(C(top)), np.array(C(bot))
    for y in range(h):
        a[y] = (t + (b - t) * (y / max(1, h - 1))).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


def grain(im, amt=8, seed=0):
    a = np.asarray(im).astype(np.float32)
    a[..., :3] += np.random.default_rng(seed).normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def poster_movie():
    im = grad(96, 144, '#0B1730', '#C2452D')
    d = ImageDraw.Draw(im)
    d.ellipse([18, 40, 78, 100], fill=C('#F2B35A'))  # sun
    for i in range(6):
        d.polygon([(0, 110 + i * 3), (40, 92 + i * 2), (96, 112 + i * 3), (96, 144), (0, 144)], fill=C('#1A1020'))
    d.rectangle([30, 70, 34, 110], fill=C('#1A1020'))  # silhouette
    d.ellipse([27, 62, 37, 72], fill=C('#1A1020'))
    pf.draw_centered(im, 48, 10, 'NIGHT', C('#F7E6C4'), 2)
    pf.draw_centered(im, 48, 28, 'DRIVE', C('#F7E6C4'), 1)
    pf.draw_centered(im, 48, 132, 'IN CINEMAS', C('#F7E6C4'), 1)
    grain(im, 6, 1).save(f'{OUT}/poster_movie.png')


def poster_band():
    im = Image.new('RGBA', (96, 128), C('#E9E2D2'))
    d = ImageDraw.Draw(im)
    for r in range(40, 4, -6):
        d.ellipse([48 - r, 56 - r, 48 + r, 56 + r], outline=C('#151515'), width=2)
    d.rectangle([0, 0, 95, 18], fill=C('#151515'))
    pf.draw_centered(im, 48, 6, 'NO SIGNAL', C('#E9E2D2'), 1)
    pf.draw_centered(im, 48, 106, 'WORLD TOUR', C('#151515'), 1)
    grain(im, 7, 2).save(f'{OUT}/poster_band.png')


def poster_game():
    im = grad(96, 128, '#2A1F55', '#0E0A1E')
    d = ImageDraw.Draw(im)
    for _ in range(40):
        d.point((R.randint(0, 95), R.randint(0, 80)), fill=C('#FFFFFF'))
    d.polygon([(48, 28), (66, 80), (48, 70), (30, 80)], fill=C('#C9C3E6'))
    d.polygon([(42, 80), (54, 80), (48, 98)], fill=C('#F0B55C'))
    pf.draw_centered(im, 48, 106, 'STARFALL', C('#F0B55C'), 2)
    grain(im, 6, 3).save(f'{OUT}/poster_game.png')


def sticky(col, seed):
    im = Image.new('RGBA', (16, 16), C(col))
    d = ImageDraw.Draw(im)
    r = random.Random(seed)
    for y in range(4, 14, 3):
        d.line([2, y, r.randint(8, 13), y], fill=C('#4A4A60'))
    return im


def stickies():
    for i, col in enumerate(['#FFE66B', '#FF9EC4', '#9EE6A8', '#8FD3FF']):
        sticky(col, i).save(f'{OUT}/sticky_{i}.png')


def spines():
    im = Image.new('RGBA', (128, 64), C('#222222'))
    d = ImageDraw.Draw(im)
    x = 0
    cols = ['#7A2E2E', '#2E4A7A', '#D8C9A8', '#2E6A4A', '#B8862E', '#4A2E6A', '#1E1E1E', '#C9C9C9', '#8E3B6E']
    while x < 128:
        w = R.randint(5, 11)
        top = R.randint(0, 12)
        col = C(R.choice(cols))
        d.rectangle([x, top, x + w - 1, 63], fill=col)
        d.line([x + 1, top + 8, x + w - 2, top + 8], fill=C('#E8D9A8'))
        d.line([x + 1, top + 30, x + w - 2, top + 30], fill=C('#E8D9A8'))
        d.line([x + w - 1, top, x + w - 1, 63], fill=C('#111111'))
        x += w
    grain(im, 6, 4).save(f'{OUT}/spines.png')


def screens():
    # laptop: code editor
    im = Image.new('RGBA', (96, 60), C('#1E1F29'))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 95, 5], fill=C('#2B2D3A'))
    for y in range(9, 58, 4):
        x = R.randint(4, 16)
        for _ in range(R.randint(1, 4)):
            w = R.randint(4, 18)
            d.line([x, y, x + w, y], fill=C(R.choice(['#C792EA', '#82AAFF', '#C3E88D', '#F78C6C', '#A6ACCD'])), width=1)
            x += w + 3
    im.save(f'{OUT}/screen_laptop.png')
    # monitor: paused game
    im = grad(128, 72, '#3A6EA5', '#C9E3F2')
    d = ImageDraw.Draw(im)
    d.polygon([(0, 50), (40, 30), (80, 46), (128, 28), (128, 72), (0, 72)], fill=C('#3E6B3A'))
    d.rectangle([40, 24, 88, 46], fill=C('#000000'))
    pf.draw_centered(im, 64, 31, 'PAUSED', C('#FFFFFF'), 1)
    im.save(f'{OUT}/screen_monitor.png')


def can():
    im = Image.new('RGBA', (32, 64), C('#151A22'))
    d = ImageDraw.Draw(im)
    d.polygon([(0, 20), (32, 12), (32, 28), (0, 36)], fill=C('#7CFF3A'))
    pf.draw(im, (3, 40), 'VOLT', C('#7CFF3A'))
    d.rectangle([0, 0, 31, 3], fill=C('#B9BEC6'))
    d.rectangle([0, 60, 31, 63], fill=C('#B9BEC6'))
    im.save(f'{OUT}/can_volt.png')


def pizza():
    im = Image.new('RGBA', (64, 64), C('#C9A36E'))
    d = ImageDraw.Draw(im)
    d.ellipse([10, 10, 54, 54], outline=C('#B33A2E'), width=3)
    pf.draw_centered(im, 32, 26, 'PIZZA', C('#B33A2E'), 1)
    d.ellipse([20, 40, 30, 46], fill=C('#8E6A42'))  # grease stain
    grain(im, 7, 5).save(f'{OUT}/pizza_lid.png')
    im = Image.new('RGBA', (64, 64), C('#C9A36E'))
    d = ImageDraw.Draw(im)
    d.pieslice([6, 6, 58, 58], 200, 340, fill=C('#E8B04A'))
    for _ in range(8):
        x, y = R.randint(18, 46), R.randint(10, 26)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=C('#A8322A'))
    grain(im, 7, 6).save(f'{OUT}/pizza_inside.png')


def window_view():
    im = grad(96, 96, '#7FB6E6', '#DCEBF5')
    d = ImageDraw.Draw(im)
    for i in range(7):  # buildings across the street
        x = i * 15 - 4
        h = R.randint(30, 60)
        d.rectangle([x, 96 - h, x + 13, 96], fill=C(R.choice(['#B9A48E', '#9C8E84', '#C7B9A6', '#857A74'])))
        for wy in range(96 - h + 4, 92, 7):
            for wx in range(x + 2, x + 12, 4):
                d.rectangle([wx, wy, wx + 1, wy + 2], fill=C('#5C6B7E'))
    for _ in range(5):  # tree
        x, y = R.randint(50, 80), R.randint(50, 80)
        d.ellipse([x - 12, y - 10, x + 12, y + 10], fill=C('#4E7A3A'))
    grain(im, 5, 7).filter(ImageFilter.SMOOTH).save(f'{OUT}/window_view.png')


def clock_face():
    im = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([1, 1, 62, 62], fill=C('#F4F1EA'), outline=C('#2A2733'), width=3)
    for k in range(12):
        a = k / 12 * math.tau
        x, y = 32 + math.sin(a) * 25, 32 - math.cos(a) * 25
        d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=C('#2A2733'))
    im.save(f'{OUT}/clock_face.png')


def photos():
    for i in range(4):
        im = grad(16, 20, R.choice(['#E8A87C', '#7CB8E8', '#A8E87C', '#E87CB8']), '#3A3A4A')
        d = ImageDraw.Draw(im)
        d.ellipse([5, 5, 11, 11], fill=C('#E8C4A8'))
        d.rectangle([0, 0, 15, 19], outline=C('#FFFFFF'))
        im.save(f'{OUT}/photo_{i}.png')


def sneaker():
    im = Image.new('RGBA', (32, 16), C('#F2F2F2'))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 12, 31, 15], fill=C('#D9D9D9'))
    d.line([8, 4, 24, 9], fill=C('#1A1A1A'), width=2)  # swoosh-ish stripe
    im.save(f'{OUT}/sneaker.png')


poster_movie(); poster_band(); poster_game(); stickies(); spines(); screens(); can(); pizza()
window_view(); clock_face(); photos(); sneaker()
print('room decals ok')
