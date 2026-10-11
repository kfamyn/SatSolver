"""PS1 post: palette reduction with 4x4 Bayer dithering + nearest upscale.
Usage: python3 ps1post.py in.png out.png [scale] [bits]"""
import sys
import numpy as np
from PIL import Image

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16 - 0.5


def ps1(im, scale=4, bits=5, dither=1.0):
    a = np.asarray(im.convert('RGB')).astype(np.float32) / 255
    h, w, _ = a.shape
    levels = 2 ** bits - 1
    th = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    q = np.floor(a * levels + 0.5 + th * dither) / levels
    out = Image.fromarray((np.clip(q, 0, 1) * 255).astype(np.uint8))
    return out.resize((w * scale, h * scale), Image.NEAREST)


if __name__ == '__main__':
    scale = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    bits = int(sys.argv[4]) if len(sys.argv) > 4 else 5
    ps1(Image.open(sys.argv[1]), scale, bits).save(sys.argv[2])
