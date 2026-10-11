"""Post-FX pass for THE FEED: grain, chromatic aberration, lens distortion,
slice glitch, bloom, vignette, flash, shake. Driven per frame by fx.json.

Usage: python3 post.py <thefeed_dir> <out_dir> <width>
Holds the last rendered frame when the render used STEP > 1.
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageFilter

src, dst, W = sys.argv[1], sys.argv[2], int(sys.argv[3])
H = W * 16 // 9
os.makedirs(dst, exist_ok=True)
meta = json.load(open(os.path.join(src, 'fx.json')))
total = meta['total']
fx = {int(k): v for k, v in meta['frames'].items()}
frames_dir = os.path.join(src, 'frames')
K = W / 1080  # effect sizes are authored at 1080 wide

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
cx, cy = (W - 1) / 2, (H - 1) / 2
nx, ny = (xx - cx) / cx, (yy - cy) / cy
r2 = nx * nx + ny * ny * 0.32  # elliptical falloff tuned for portrait
vig_mask = np.clip(1 - r2 * 0.75, 0, 1)


def sample(img, mx, my):
    mx = np.clip(mx, 0, W - 1).astype(np.int32)
    my = np.clip(my, 0, H - 1).astype(np.int32)
    return img[my, mx]


last = None
for g in range(1, total + 1):
    p = os.path.join(frames_dir, f'{g:04d}.png')
    if os.path.exists(p):
        last = Image.open(p).convert('RGB').resize((W, H), Image.BICUBIC)
    if last is None:
        continue
    f = fx.get(g, {})
    rnd = random.Random(g)
    img = np.asarray(last).astype(np.float32) / 255

    # shake
    sh = f.get('shake', 0)
    if sh:
        dx, dy = int((rnd.random() - 0.5) * 60 * K * sh), int((rnd.random() - 0.5) * 60 * K * sh)
        img = np.roll(img, (dy, dx), axis=(0, 1))

    # barrel distortion for the wide/POV angles
    lens = f.get('lens', 0)
    if lens:
        rr = nx * nx + ny * ny
        k = 1 + lens * rr
        img = sample(img, cx + nx * cx / k * (1 + lens * 0.3), cy + ny * cy / k * (1 + lens * 0.3))

    # chromatic aberration: radial split, stronger toward the edges
    ch = f.get('chroma', 0) * K
    if ch > 0.3:
        out = img.copy()
        out[..., 0] = sample(img, xx + nx * ch, yy + ny * ch)[..., 0]
        out[..., 2] = sample(img, xx - nx * ch, yy - ny * ch)[..., 2]
        img = out

    # glitch: displaced slices + channel tearing + repeated blocks
    gl = f.get('glitch', 0)
    if gl > 0 and rnd.random() < 0.35 + gl * 0.6:
        out = img.copy()
        for _ in range(int(3 + gl * 10)):
            y0 = rnd.randint(0, H - 1)
            hgt = rnd.randint(int(4 * K) + 1, int(90 * K) + 2)
            off = int((rnd.random() - 0.5) * 220 * K * gl)
            out[y0:y0 + hgt] = np.roll(out[y0:y0 + hgt], off, axis=1)
            if rnd.random() < 0.4:
                c = rnd.randint(0, 2)
                out[y0:y0 + hgt, :, c] = np.roll(out[y0:y0 + hgt, :, c], off // 2, axis=1)
        if rnd.random() < gl * 0.5:  # datamosh-ish smear: drag a block down
            x0 = rnd.randint(0, W // 2)
            y0 = rnd.randint(0, H // 2)
            bw, bh = rnd.randint(W // 6, W // 2), rnd.randint(H // 10, H // 4)
            region = out[y0:y0 + bh, x0:x0 + bw]
            blk = region[:4]
            region[:] = np.repeat(blk, math.ceil(region.shape[0] / 4), axis=0)[:region.shape[0]]
        img = out

    # bloom
    bright = np.clip(img - 0.65, 0, 1)
    if bright.max() > 0.01:
        b = Image.fromarray((bright * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28 * K))
        img = img + np.asarray(b).astype(np.float32) / 255 * 0.9

    # flash
    fl = f.get('flash', 0)
    if fl:
        img = img * (1 - fl) + fl

    # vignette
    v = f.get('vig', 0.5)
    img = img * (1 - v * (1 - vig_mask[..., None]))

    # film grain (monochrome, per frame), slightly coarse
    gr = f.get('grain', 0.4)
    if gr:
        gh, gw = max(1, int(H / 1.6)), max(1, int(W / 1.6))
        n = np.random.default_rng(g).normal(0, 1, (gh, gw)).astype(np.float32)
        n = np.asarray(Image.fromarray(n).resize((W, H), Image.BILINEAR))
        img = img + n[..., None] * 0.07 * gr

    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    out.save(os.path.join(dst, f'{g:04d}.png'))
print('post frames', total)
