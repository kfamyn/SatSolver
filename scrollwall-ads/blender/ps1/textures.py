"""Pixel-art textures for the PS1-style Scrollwall short. Everything is drawn
here at tiny resolutions and shown with nearest-neighbour filtering, so it reads
as an early-3D game. Usage: python3 textures.py <out_dir>"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import pixfont as pf

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
os.makedirs(f'{OUT}/feed', exist_ok=True)
os.makedirs(f'{OUT}/screens', exist_ok=True)
R = random.Random(11)


def C(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def noise_fill(img, base, amt=10, rnd=R):
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            d = rnd.randint(-amt, amt)
            px[x, y] = tuple(max(0, min(255, c + d)) for c in base[:3]) + (base[3] if len(base) > 3 else 255,)


def save(img, name):
    img.save(f'{OUT}/{name}.png')


# ------------------------------------------------------------------ room

def wallpaper():
    im = Image.new('RGBA', (64, 64))
    noise_fill(im, C('#F2C9A8'), 6)
    d = ImageDraw.Draw(im)
    for x in range(0, 64, 16):
        d.rectangle([x, 0, x + 5, 63], fill=C('#EAB894'))
    for y in range(4, 64, 16):
        for x in range(10, 64, 16):
            d.point((x, y), fill=C('#D98F6E'))
            d.point((x + 1, y + 8), fill=C('#C77E9E'))
    save(im, 'wallpaper')


def floor():
    im = Image.new('RGBA', (64, 64))
    d = ImageDraw.Draw(im)
    for i, y in enumerate(range(0, 64, 8)):
        base = C(['#A36A43', '#8F5B39', '#B07650'][i % 3])
        sub = Image.new('RGBA', (64, 8))
        noise_fill(sub, base, 8)
        im.paste(sub, (0, y))
        d.line([0, y, 63, y], fill=C('#5E3A22'))
        off = (i * 23) % 64
        d.line([off, y, off, y + 7], fill=C('#5E3A22'))
    save(im, 'floor')


def rug():
    im = Image.new('RGBA', (64, 64), C('#5B3F8F'))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 3, 60, 60], outline=C('#F0B55C'), width=2)
    d.rectangle([9, 9, 54, 54], outline=C('#E8914A'))
    for k in range(4):
        cx, cy = 32, 32
        r = 6 + k * 6
        d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=C(['#F0B55C', '#C98BD0', '#E8914A', '#A98BDF'][k]))
    save(im, 'rug')


def sheet():
    im = Image.new('RGBA', (32, 32))
    px = im.load()
    for y in range(32):
        for x in range(32):
            px[x, y] = C('#DCE9F7') if ((x // 4) + (y // 4)) % 2 else C('#BFD3EE')
    save(im, 'sheet')


def blanket():
    im = Image.new('RGBA', (64, 64))
    noise_fill(im, C('#E8914A'), 8)
    d = ImageDraw.Draw(im)
    for y in range(0, 64, 12):
        d.line([0, y, 63, y], fill=C('#C96F30'))
        for x in range(0, 64, 4):
            d.point((x, y + 6), fill=C('#F7C08A'))
    for x in range(0, 64, 16):
        d.line([x, 0, x, 63], fill=C('#C96F30'))
    save(im, 'blanket')


def solid(name, col, amt=8, size=16):
    im = Image.new('RGBA', (size, size))
    noise_fill(im, C(col), amt)
    save(im, name)


def wood(name, col, dark):
    im = Image.new('RGBA', (32, 32))
    noise_fill(im, C(col), 6)
    d = ImageDraw.Draw(im)
    for y in range(2, 32, 5):
        xs = R.randint(0, 31)
        d.line([0, y, 31, y + R.choice([0, 1])], fill=C(dark))
        d.line([xs, y + 2, xs + 6, y + 2], fill=C(dark))
    save(im, name)


def poster(name, kind):
    im = Image.new('RGBA', (32, 48), C('#1B1A2E'))
    d = ImageDraw.Draw(im)
    if kind == 'game':
        im.paste(Image.new('RGBA', (32, 48), C('#20184A')))
        for _ in range(20):
            d.point((R.randint(0, 31), R.randint(0, 30)), fill=C('#FFFFFF'))
        d.polygon([(16, 12), (22, 26), (16, 23), (10, 26)], fill=C('#A98BDF'))
        d.rectangle([14, 26, 18, 29], fill=C('#F0B55C'))
        pf.draw(im, (2, 36), 'ZOOM', C('#F0B55C'))
    elif kind == 'band':
        im.paste(Image.new('RGBA', (32, 48), C('#E8574C')))
        d.ellipse([6, 8, 26, 28], fill=C('#1B1A2E'))
        d.ellipse([13, 15, 19, 21], fill=C('#E8574C'))
        pf.draw(im, (2, 34), 'LOUD', C('#FFFFFF'))
    else:  # cat
        im.paste(Image.new('RGBA', (32, 48), C('#7EC8E3')))
        d.polygon([(8, 14), (11, 8), (14, 14)], fill=C('#F2A65A'))
        d.polygon([(18, 14), (21, 8), (24, 14)], fill=C('#F2A65A'))
        d.ellipse([7, 12, 25, 28], fill=C('#F2A65A'))
        d.point((12, 19), fill=C('#000000'))
        d.point((20, 19), fill=C('#000000'))
        d.line([14, 23, 18, 23], fill=C('#000000'))
        pf.draw(im, (4, 36), 'MEOW', C('#1B1A2E'))
    d.rectangle([0, 0, 31, 47], outline=C('#FFFFFF'))
    save(im, f'poster_{name}')


def books():
    im = Image.new('RGBA', (64, 32))
    x = 0
    cols = ['#8E6BD4', '#E8914A', '#4CD98B', '#E8574C', '#5C7CFF', '#F0B55C', '#C98BD0']
    while x < 64:
        w = R.randint(4, 8)
        col = C(R.choice(cols))
        ImageDraw.Draw(im).rectangle([x, R.randint(0, 6), x + w - 1, 31], fill=col)
        ImageDraw.Draw(im).line([x + 1, 12, x + w - 2, 12], fill=C('#FFFFFF'))
        x += w
    save(im, 'books')


def sky(name, top, bottom, sun=None):
    im = Image.new('RGBA', (32, 48))
    px = im.load()
    t, b = C(top), C(bottom)
    for y in range(48):
        k = y / 47
        for x in range(32):
            px[x, y] = tuple(int(t[i] + (b[i] - t[i]) * k) for i in range(3)) + (255,)
    d = ImageDraw.Draw(im)
    for cx, cy in [(8, 12), (22, 20)]:
        d.ellipse([cx - 6, cy - 2, cx + 6, cy + 3], fill=C('#FFFFFF'))
        d.ellipse([cx - 3, cy - 5, cx + 4, cy + 1], fill=C('#FFFFFF'))
    if sun:
        d.ellipse([20, 32, 28, 40], fill=C(sun))
    save(im, name)


def clock_face():
    im = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([1, 1, 62, 62], fill=C('#FFFFFF'), outline=C('#2A2733'), width=3)
    for k in range(12):
        a = k / 12 * math.tau
        x, y = 32 + math.sin(a) * 25, 32 - math.cos(a) * 25
        d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=C('#2A2733'))
    save(im, 'clock_face')


def misc():
    # pizza box lid
    im = Image.new('RGBA', (32, 32), C('#E3C7A0'))
    d = ImageDraw.Draw(im)
    d.ellipse([8, 6, 24, 22], fill=C('#E8574C'))
    pf.draw(im, (2, 24), 'PIZZA', C('#E8574C'))
    save(im, 'pizza')
    # soda can
    im = Image.new('RGBA', (16, 32), C('#E8574C'))
    ImageDraw.Draw(im).rectangle([0, 12, 15, 18], fill=C('#FFFFFF'))
    save(im, 'can')
    # leaves (alpha)
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _ in range(14):
        x, y = R.randint(2, 28), R.randint(2, 28)
        d.ellipse([x - 4, y - 2, x + 4, y + 2], fill=C(R.choice(['#3FA34D', '#2E7D3A', '#5CC46A'])))
    save(im, 'leaves')
    # laundry
    for n, col in [('cloth_a', '#5C7CFF'), ('cloth_b', '#F2F2F2'), ('cloth_c', '#3B3550')]:
        im = Image.new('RGBA', (16, 16))
        noise_fill(im, C(col), 14)
        d = ImageDraw.Draw(im)
        for y in range(0, 16, 5):
            d.line([0, y, 15, y + 2], fill=C(col)[:3] + (200,))
        save(im, n)


# ------------------------------------------------------------------ Doug

def doug_textures():
    # hoodie: violet-grey with blocky folds
    im = Image.new('RGBA', (32, 32))
    noise_fill(im, C('#6B5FA8'), 6)
    d = ImageDraw.Draw(im)
    for y in range(0, 32, 7):
        d.line([0, y, 31, y + 1], fill=C('#584D90'))
    save(im, 'hoodie')
    im = Image.new('RGBA', (32, 32))
    noise_fill(im, C('#6B5FA8'), 6)
    d = ImageDraw.Draw(im)
    d.rectangle([8, 20, 23, 28], fill=C('#584D90'))  # pocket
    d.line([13, 2, 13, 12], fill=C('#FFFFFF'))
    d.line([18, 2, 18, 12], fill=C('#FFFFFF'))
    d.rectangle([14, 8, 17, 12], fill=C('#F0B55C'))  # tiny logo
    save(im, 'hoodie_front')
    solid('skin', '#F2C29B', 5)
    solid('pants', '#2F3A5A', 6)
    im = Image.new('RGBA', (32, 32))
    noise_fill(im, C('#3A2618'), 8)
    d = ImageDraw.Draw(im)
    for x in range(0, 32, 3):
        d.line([x, 0, x + R.randint(-2, 2), 31], fill=C('#2A1A10'))
    save(im, 'hair')


def face(name, eyes='normal', mouth='flat', bags=False, blush=False, glow=False):
    """32x32 face decal with alpha, laid over the head (chunky, readable)."""
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    INK = C('#1A1220')
    for cx in (10, 21):
        top, bot = {'normal': (12, 18), 'trance': (11, 19), 'surprised': (10, 19), 'focus': (14, 18)}.get(eyes, (12, 18))
        if eyes in ('normal', 'trance', 'surprised', 'focus'):
            d.rectangle([cx - 3, top, cx + 3, bot], fill=C('#FFFFFF'), outline=INK)
            if eyes == 'trance':
                d.point((cx, 15), fill=INK)
                d.rectangle([cx - 2, top + 1, cx - 1, top + 2], fill=C('#5CE1FF'))
                d.rectangle([cx + 1, bot - 2, cx + 2, bot - 1], fill=C('#FF5C9A'))
            elif eyes == 'surprised':
                d.rectangle([cx - 1, 14, cx, 15], fill=INK)
            elif eyes == 'focus':
                d.rectangle([cx - 1, 15, cx + 1, 17], fill=INK)
            else:
                d.rectangle([cx - 1, 14, cx + 1, 17], fill=INK)
                d.point((cx - 1, 14), fill=C('#FFFFFF'))
        elif eyes == 'blink':
            d.line([cx - 3, 16, cx + 3, 16], fill=INK)
        elif eyes == 'happy':
            d.line([cx - 3, 17, cx, 14], fill=INK)
            d.line([cx, 14, cx + 3, 17], fill=INK)
        # brows
        if eyes == 'focus':
            d.line([cx - 3, 11 + (1 if cx < 16 else 0), cx + 3, 11 + (0 if cx < 16 else 1)], fill=INK)
        elif eyes == 'surprised':
            d.line([cx - 3, 8, cx + 3, 8], fill=INK)
        else:
            d.line([cx - 3, 10, cx + 3, 10], fill=INK)
        if bags:
            d.line([cx - 3, bot + 2, cx + 3, bot + 2], fill=C('#9A6E8E'))
        if blush:
            d.rectangle([cx - 4, 20, cx - 2, 21], fill=C('#F08FA0'))
    if mouth == 'flat':
        d.line([14, 25, 17, 25], fill=INK)
    elif mouth == 'open':
        d.rectangle([14, 24, 17, 27], fill=INK)
    elif mouth == 'smile':
        d.line([12, 24, 13, 25], fill=INK)
        d.line([13, 25, 18, 25], fill=INK)
        d.line([18, 25, 19, 24], fill=INK)
    elif mouth == 'o':
        d.rectangle([14, 24, 16, 27], fill=INK)
    save(im, f'face_{name}')


# ------------------------------------------------------------------ phone screens (120x240)

SW, SH = 120, 240
FEED_COLS = ['#FF5C8A', '#5CE1FF', '#FFD25C', '#9D6BFF', '#4CD98B', '#FF8A4C', '#5C7CFF', '#FFFFFF']


def feed_clip(i):
    rnd = random.Random(100 + i)
    im = Image.new('RGBA', (SW, SH), C(FEED_COLS[i % len(FEED_COLS)]))
    d = ImageDraw.Draw(im)
    kind = i % 4
    if kind == 0:  # a "face" video
        d.ellipse([30, 50, 90, 120], fill=C('#F2C29B'))
        d.rectangle([45, 75, 52, 82], fill=C('#000000'))
        d.rectangle([68, 75, 75, 82], fill=C('#000000'))
        d.rectangle([50, 100, 70, 106], fill=C('#000000'))
    elif kind == 1:  # a cat
        d.polygon([(35, 70), (45, 45), (55, 70)], fill=C('#F2A65A'))
        d.polygon([(65, 70), (75, 45), (85, 70)], fill=C('#F2A65A'))
        d.ellipse([30, 60, 90, 120], fill=C('#F2A65A'))
        d.rectangle([46, 82, 50, 86], fill=C('#000000'))
        d.rectangle([70, 82, 74, 86], fill=C('#000000'))
    elif kind == 2:  # food
        d.ellipse([20, 60, 100, 130], fill=C('#FFFFFF'))
        d.ellipse([32, 70, 88, 120], fill=C('#E8574C'))
        for _ in range(6):
            x, y = rnd.randint(40, 80), rnd.randint(78, 112)
            d.rectangle([x, y, x + 4, y + 4], fill=C('#FFD25C'))
    else:  # meme text
        pf.draw_centered(im, SW // 2, 70, 'POV:', C('#000000'), 2)
        pf.draw_centered(im, SW // 2, 95, 'ME AT 3AM', C('#000000'), 1)
    # side buttons + caption bars = "short-form video" at a glance
    for k in range(4):
        d.rectangle([SW - 16, 120 + k * 22, SW - 6, 130 + k * 22], fill=C('#FFFFFF'))
    d.rectangle([8, SH - 40, 70, SH - 34], fill=C('#FFFFFF'))
    d.rectangle([8, SH - 28, 50, SH - 23], fill=C('#EEEEEE'))
    return im


def feed_frames():
    clips = [feed_clip(i) for i in range(16)]
    FR = 8
    n = 0
    for f in range(len(clips) * FR):
        ci, t = divmod(f, FR)
        t /= FR
        e = 1 - (1 - min(1, t / 0.5)) ** 3
        frame = Image.new('RGBA', (SW, SH))
        frame.paste(clips[ci], (0, int(-e * SH)))
        frame.paste(clips[(ci + 1) % len(clips)], (0, int(SH - e * SH)))
        n += 1
        frame.save(f'{OUT}/feed/{n:04d}.png')
    return n


def wally_sprite(im, cx, cy, scale=1, eyes=True):
    """Scrollwall's pill on a screen: white capsule with two eyes."""
    d = ImageDraw.Draw(im)
    w, h = 16 * scale, 40 * scale
    d.rounded_rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2], radius=w // 2, fill=C('#F5F2FB'), outline=C('#B9A5E8'))
    if eyes:
        for s in (-1, 1):
            d.rectangle([cx + s * 3 * scale - scale, cy - 10 * scale, cx + s * 3 * scale + scale, cy - 5 * scale], fill=C('#16141C'))


def screen_bg():
    im = Image.new('RGBA', (SW, SH))
    px = im.load()
    for y in range(SH):
        k = y / SH
        c = (int(42 - 30 * k), int(27 - 17 * k), int(82 - 67 * k), 255)
        for x in range(SW):
            px[x, y] = c
    return im


def shield(drop=1.0, balance=0, coin_line=True):
    """'You hit a scrollwall' — the pill drops in from the top (drop 0..1)."""
    im = screen_bg()
    y = int(-60 + (95 + 60) * drop)
    wally_sprite(im, SW // 2, y, 2)
    if drop >= 1:
        pf.draw_centered(im, SW // 2, 150, 'YOU HIT A', C('#FFFFFF'), 1)
        pf.draw_centered(im, SW // 2, 160, 'SCROLLWALL', C('#F0B55C'), 2, shadow=C('#000000'))
        if coin_line:
            pf.draw_centered(im, SW // 2, 186, f'BALANCE: {balance}', C('#FF6B5E' if balance == 0 else '#FFFFFF'), 1)
            pf.draw_centered(im, SW // 2, 200, 'FOCUS TO EARN', C('#A98BDF'), 1)
    return im


def balance_screen(n, timer=None):
    im = screen_bg()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 30, SW - 10, 100], radius=8, fill=C('#16141C'), outline=C('#A98BDF'))
    pf.draw(im, (18, 38), 'FOCUSCARD', C('#FFFFFF'))
    pf.draw_centered(im, SW // 2, 58, str(n), C('#F0B55C'), 4, shadow=C('#000000'))
    pf.draw_centered(im, SW // 2, 90, 'COINS', C('#A98BDF'))
    if timer:
        pf.draw_centered(im, SW // 2, 130, 'FOCUS', C('#FFFFFF'))
        pf.draw_centered(im, SW // 2, 142, timer, C('#FFFFFF'), 3)
    wally_sprite(im, SW // 2, 205, 1)
    return im


def unlock_screen(stage, balance=50):
    """stage: 'offer' | 'tilt' | 'done'"""
    im = screen_bg()
    d = ImageDraw.Draw(im)
    pf.draw_centered(im, SW // 2, 22, 'UNLOCK', C('#FFFFFF'), 2)
    d.rounded_rectangle([12, 48, SW - 12, 108], radius=8, fill=C('#16141C'), outline=C('#F0B55C'))
    pf.draw_centered(im, SW // 2, 58, '5 MIN', C('#FFFFFF'), 3)
    pf.draw_centered(im, SW // 2, 88, '40 COINS', C('#F0B55C'), 1)
    pf.draw_centered(im, SW // 2, 120, f'BALANCE {balance}', C('#A98BDF'))
    if stage == 'offer':
        d.rounded_rectangle([14, 190, SW - 14, 212], radius=10, fill=C('#FFFFFF'))
        pf.draw_centered(im, SW // 2, 198, 'FOCUSCARD PAY', C('#16141C'))
    elif stage == 'tilt':
        pf.draw_centered(im, SW // 2, 160, 'TILT TO SPEND', C('#FFFFFF'), 1)
        d.rounded_rectangle([50, 175, 70, 210], radius=4, outline=C('#FFFFFF'), width=2)
    else:
        d.rounded_rectangle([6, 150, SW - 6, 212], radius=10, fill=C('#4CD98B'))
        pf.draw_centered(im, SW // 2, 160, 'UNLOCKED', C('#16141C'), 2)
        pf.draw_centered(im, SW // 2, 186, '5:00', C('#16141C'), 2)
    return im


def screens():
    for i in range(13):
        shield(min(1, i / 8) if i < 9 else 1).save(f'{OUT}/screens/shield_{i:02d}.png')
    for n in range(0, 51, 5):
        balance_screen(n).save(f'{OUT}/screens/balance_{n:02d}.png')
    for st in ('offer', 'tilt', 'done'):
        unlock_screen(st, 50 if st != 'done' else 10).save(f'{OUT}/screens/unlock_{st}.png')


def extras():
    # '!' alert balloon, old-RPG style
    im = Image.new('RGBA', (16, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([1, 0, 14, 15], fill=C('#FFFFFF'), outline=C('#1A1220'))
    d.polygon([(5, 15), (8, 19), (10, 15)], fill=C('#FFFFFF'))
    d.rectangle([7, 3, 8, 9], fill=C('#E8574C'))
    d.rectangle([7, 11, 8, 12], fill=C('#E8574C'))
    save(im, 'bang')
    # open book pages
    im = Image.new('RGBA', (32, 24), C('#FBF7EE'))
    d = ImageDraw.Draw(im)
    d.line([16, 0, 16, 23], fill=C('#C9BFA8'))
    for y in range(4, 22, 3):
        d.line([3, y, 13, y], fill=C('#8A8AA0'))
        d.line([19, y, 29, y], fill=C('#8A8AA0'))
    save(im, 'book_pages')
    # coin face
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, 15, 15], fill=C('#F0B55C'), outline=C('#B86E1E'))
    d.ellipse([4, 4, 11, 11], outline=C('#FFE3A3'))
    save(im, 'coin')


wallpaper(); floor(); rug(); sheet(); blanket(); extras()
solid('pillow', '#F4F1EA', 4)
wood('wood_dark', '#6A4A3A', '#4E3428')
wood('wood_light', '#C99B6E', '#A87C52')
solid('white_plastic', '#EDEAF2', 4)
solid('black_plastic', '#1C1A22', 4)
solid('metal', '#9AA0AE', 6)
for k in ('game', 'band', 'cat'):
    poster(k, k)
books(); clock_face(); misc()
sky('sky_morning', '#7EC8F2', '#CDEBFF')
sky('sky_noon', '#4FA8F0', '#A9DBFF')
sky('sky_evening', '#F08A5C', '#FFD39A', sun='#FFF2B0')
doug_textures()
face('trance', 'trance', 'open', bags=True)
face('trance_blink', 'blink', 'open', bags=True)
face('surprised', 'surprised', 'o', bags=True)
face('normal', 'normal', 'flat')
face('blink', 'blink', 'flat')
face('focus', 'focus', 'flat')
face('happy', 'happy', 'smile', blush=True)
print('feed frames', feed_frames())
screens()
print('textures ok')
