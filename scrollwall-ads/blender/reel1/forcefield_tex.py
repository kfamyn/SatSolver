"""Scrollwall force-field texture: translucent violet hex grid, glowing frame,
the ghost from the shield screen and pixel 'SCROLLWALL' lettering.
Writes assets/ps1/screens/forcefield.png (RGBA; alpha drives the wall's opacity).
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'ps1'))
import pixfont  # noqa: E402

W, H = 240, 288
OUT = os.path.join(HERE, '..', 'assets', 'ps1', 'screens', 'forcefield.png')

im = Image.new('RGBA', (W, H), (120, 70, 255, 55))
d = ImageDraw.Draw(im)
r = 10
for row in range(-1, int(H // (r * 1.5)) + 2):
    for col in range(-1, int(W // (r * math.sqrt(3))) + 2):
        cx = col * r * math.sqrt(3) + (row % 2) * r * math.sqrt(3) / 2
        cy = row * r * 1.5
        pts = [(cx + r * math.cos(math.radians(60 * k + 30)), cy + r * math.sin(math.radians(60 * k + 30))) for k in range(6)]
        d.polygon(pts, outline=(190, 160, 255, 150))
for y in range(0, H, 4):
    d.line([(0, y), (W, y)], fill=(170, 140, 255, 80))
d.rectangle([0, 0, W - 1, H - 1], outline=(255, 255, 255, 255), width=4)
d.rectangle([6, 6, W - 7, H - 7], outline=(200, 170, 255, 200), width=1)
# ghost (same as the app's shield screen)
gx, gy, gw, gh = W // 2, 92, 46, 80
d.rounded_rectangle([gx - gw // 2, gy - gh // 2, gx + gw // 2, gy + gh // 2], radius=gw // 2, fill=(240, 236, 255, 245))
for ex in (-9, 9):
    d.rectangle([gx + ex - 3, gy - 12, gx + ex + 3, gy + 2], fill=(25, 20, 45, 255))
txt = Image.new('RGBA', (W, H), (0, 0, 0, 0))
pixfont.draw_centered(txt, W // 2, 160, 'YOU HIT A', (255, 255, 255, 255), 2)
pixfont.draw_centered(txt, W // 2, 182, 'SCROLLWALL', (255, 196, 90, 255), 3, shadow=(90, 40, 20, 255))
pixfont.draw_centered(txt, W // 2, 222, 'FOCUS TO EARN', (210, 190, 255, 255), 2)
im.alpha_composite(txt)
glow = im.filter(ImageFilter.GaussianBlur(4))
out = Image.alpha_composite(glow, im)
out.save(OUT)
print('saved', OUT, out.size)
