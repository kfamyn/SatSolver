"""Pixel textures for the 'what if scrolling cost money' subway world:
ad posters, a newspaper, line map, door sticker. -> assets/ps1/subway/*.png
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'ps1'))
import pixfont as P  # noqa: E402

OUT = os.path.join(HERE, '..', 'assets', 'ps1', 'subway')
os.makedirs(OUT, exist_ok=True)


def card(w, h, bg):
    im = Image.new('RGB', (w, h), bg)
    return im, ImageDraw.Draw(im)


def centered(im, y, text, col, scale=1):
    P.draw_centered(im, im.width // 2, y, text, col, scale)


# --- ad 1: the new law
im, d = card(192, 64, (250, 210, 60))
centered(im, 6, 'NEW!', (20, 20, 20), 1)
centered(im, 18, '$0.01', (200, 30, 30), 3)
centered(im, 44, 'PER SWIPE', (20, 20, 20), 1)
centered(im, 54, 'SCROLL RESPONSIBLY.', (60, 50, 20), 1)
im.save(os.path.join(OUT, 'ad_law.png'))

# --- ad 2: top-up kiosk
im, d = card(192, 64, (40, 90, 200))
centered(im, 6, 'LOW ON SCROLL CREDIT?', (255, 255, 255), 1)
d.rounded_rectangle([56, 18, 136, 44], 4, fill=(255, 255, 255))
centered(im, 25, 'TOP UP', (40, 90, 200), 2)
centered(im, 52, 'AT ANY STATION KIOSK', (210, 225, 255), 1)
im.save(os.path.join(OUT, 'ad_topup.png'))

# --- ad 3: thumb insurance (joke)
im, d = card(192, 64, (235, 235, 230))
centered(im, 6, 'THUMB INSURANCE', (30, 30, 30), 1)
d.rectangle([84, 18, 108, 46], fill=(230, 180, 150))  # a very pixel thumb
d.rectangle([86, 14, 106, 22], fill=(240, 200, 175))
centered(im, 52, 'FROM $9.99/MONTH', (180, 40, 40), 1)
im.save(os.path.join(OUT, 'ad_thumb.png'))

# --- ad 4: books are free
im, d = card(192, 64, (30, 120, 70))
centered(im, 8, 'BOOKS:', (255, 255, 255), 2)
centered(im, 28, 'STILL FREE.', (255, 230, 120), 2)
centered(im, 52, 'CITY LIBRARY', (200, 240, 210), 1)
im.save(os.path.join(OUT, 'ad_books.png'))

# --- line map strip
im, d = card(256, 32, (245, 245, 240))
d.rectangle([8, 14, 248, 18], fill=(230, 60, 40))
for i, x in enumerate(range(16, 250, 46)):
    d.ellipse([x - 4, 12, x + 4, 20], fill=(255, 255, 255), outline=(230, 60, 40))
P.draw(im, (6, 2), 'LINE 7', (230, 60, 40), 1)
P.draw(im, (6, 23), 'FEED ST   LIKE AVE   SCROLL SQ', (40, 40, 40), 1)
im.save(os.path.join(OUT, 'linemap.png'))

# --- newspaper (front page, readable in a close-up)
im, d = card(128, 176, (226, 222, 210))
centered(im, 4, 'THE DAILY FEED', (20, 20, 20), 1)
d.line([(4, 13), (124, 13)], fill=(40, 40, 40))
centered(im, 18, 'SCROLLING', (10, 10, 10), 2)
centered(im, 36, 'NOW COSTS', (10, 10, 10), 2)
centered(im, 54, 'MONEY', (180, 20, 20), 3)
centered(im, 80, '1 CENT PER SWIPE', (40, 40, 40), 1)
d.rectangle([6, 94, 60, 134], fill=(150, 150, 145))  # photo block
for y in range(94, 170, 6):  # columns of 'text'
    d.line([(66, y), (122, y)], fill=(120, 118, 110))
for y in range(140, 170, 6):
    d.line([(6, y), (60, y)], fill=(120, 118, 110))
im.save(os.path.join(OUT, 'newspaper.png'))

# --- door sticker
im, d = card(64, 32, (255, 200, 0))
centered(im, 6, 'MIND', (20, 20, 20), 1)
centered(im, 18, 'THE GAP', (20, 20, 20), 1)
im.save(os.path.join(OUT, 'door_sticker.png'))
print('subway textures ->', OUT)
