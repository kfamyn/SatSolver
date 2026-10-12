"""Phone screens for Reel 2 (120x240 pixel UI, like the Reel 1 screens).
paid/NN.png   : the feed with a 'SCROLL COST' ticker (NN cents)
meter/NN.png  : the frantic guy's counter spinning $12 -> $43.12
declined.png  : CARD DECLINED
-> assets/ps1/r2screens/
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'ps1'))
import pixfont as P  # noqa: E402

A = os.path.join(HERE, '..', 'assets', 'ps1')
OUT = os.path.join(A, 'r2screens')
for d in ('paid', 'meter'):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)


def feed(i):
    return Image.open(os.path.join(A, 'feed', f'{i % 128 + 1:04d}.png')).convert('RGB').resize((120, 240), Image.NEAREST)


def bar(im, text, col, bg=(20, 16, 30), h=22):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 119, h], fill=bg)
    P.draw_centered(im, 60, (h - 7) // 2 + 1, text, col, 1)


for c in range(0, 61):
    im = feed(c * 2)
    bar(im, f'SCROLL COST ${c / 100:.2f}', (255, 120, 110))
    im.save(os.path.join(OUT, 'paid', f'{c:02d}.png'))

for k in range(0, 40):
    v = 12.0 + (43.12 - 12.0) * (k / 39) ** 1.6
    im = feed(k * 3)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 119, 40], fill=(60, 10, 10))
    P.draw_centered(im, 60, 4, 'SCROLL COST', (255, 200, 190), 1)
    P.draw_centered(im, 60, 16, f'${v:.2f}', (255, 70, 60), 2)
    im.save(os.path.join(OUT, 'meter', f'{k:02d}.png'))

im = Image.new('RGB', (120, 240), (90, 10, 14))
d = ImageDraw.Draw(im)
d.rounded_rectangle([20, 60, 100, 110], 6, fill=(255, 255, 255))
d.line([(44, 72), (76, 98)], fill=(200, 20, 30), width=5)
d.line([(76, 72), (44, 98)], fill=(200, 20, 30), width=5)
P.draw_centered(im, 60, 130, 'CARD', (255, 255, 255), 2)
P.draw_centered(im, 60, 150, 'DECLINED', (255, 255, 255), 2)
P.draw_centered(im, 60, 182, 'TODAY: $43.12', (255, 180, 170), 1)
im.save(os.path.join(OUT, 'declined.png'))
print('screens ->', OUT)
