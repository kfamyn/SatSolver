"""PS1 look for v2: bloom on bright bits, light 6-bit Bayer dither, nearest x2
then a soft upscale (like the reference's low-res video).
Usage: python3 v2post.py in.png out.png [out_width]"""
import sys
import numpy as np
from PIL import Image, ImageFilter

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16 - 0.5


def look(im, out_w=540, bloom=0.8, bits=6):
    a = np.asarray(im.convert('RGB')).astype(np.float32) / 255
    h, w, _ = a.shape
    br = np.clip(a - 0.7, 0, 1)
    if br.max() > 0:
        b = np.asarray(Image.fromarray((br * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(w / 40))).astype(np.float32) / 255
        b2 = np.asarray(Image.fromarray((br * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(w / 12))).astype(np.float32) / 255
        a = a + (b * 1.2 + b2 * 0.8) * bloom
    levels = 2 ** bits - 1
    th = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    a = np.clip(np.floor(a * levels + 0.5 + th) / levels, 0, 1)
    img = Image.fromarray((a * 255).astype(np.uint8)).resize((w * 2, h * 2), Image.NEAREST)
    return img.resize((out_w, out_w * h // w), Image.BILINEAR)


if __name__ == '__main__':
    out_w = int(sys.argv[3]) if len(sys.argv) > 3 else 540
    look(Image.open(sys.argv[1]), out_w).save(sys.argv[2])
