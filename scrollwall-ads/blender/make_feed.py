"""Generates the looping 'feed' image sequence shown on Doug's phone (and in his eyes)."""
import math, random, sys, os
from PIL import Image, ImageDraw, ImageFilter

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
W, H = 270, 585
random.seed(7)
clips = []
pal = [(255, 72, 120), (90, 220, 255), (255, 190, 60), (150, 100, 255), (60, 230, 140), (255, 120, 60), (80, 110, 255), (255, 255, 255)]
for i in range(24):
    bg = pal[i % len(pal)]
    im = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(im)
    # loud shapes: faces, blobs, text bars — reads as "content" at a glance
    for _ in range(4):
        c = random.choice(pal)
        x, y, r = random.randint(0, W), random.randint(0, H), random.randint(30, 120)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    d.rectangle([14, H - 120, 200, H - 100], fill=(255, 255, 255))
    d.rectangle([14, H - 90, 150, H - 74], fill=(230, 230, 230))
    for k in range(4):
        d.ellipse([W - 46, 230 + k * 70, W - 14, 262 + k * 70], fill=(255, 255, 255))
    clips.append(im.filter(ImageFilter.GaussianBlur(1.2)))
FR = 10  # frames per clip
for f in range(len(clips) * FR):
    ci, t = divmod(f, FR)
    t /= FR
    e = 1 - (1 - min(1, t / 0.4)) ** 3
    frame = Image.new('RGB', (W, H))
    frame.paste(clips[ci], (0, int(-e * H)))
    frame.paste(clips[(ci + 1) % len(clips)], (0, int(H - e * H)))
    frame.save(f'{out}/feed_{f + 1:04d}.png')
print('frames', len(clips) * FR)
