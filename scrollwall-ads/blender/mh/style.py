"""The character's PS1 proportions: oversized head and hands, narrow
shoulders, short legs, like late-90s game characters.

PROP (default 1.25) scales the head/hands look; LEGS (default 0.8) is the leg
length factor. PROP=1.0 LEGS=1.0 = realistic.
"""
import os


def apply_style(rig, amount=None, legs=None):
    k = float(os.environ.get('PROP', 1.25)) if amount is None else amount
    lg = float(os.environ.get('LEGS', 0.8)) if legs is None else legs
    pb = rig.pose.bones
    pb['head'].scale = (k, k, k)
    for side in ('L', 'R'):
        h = 1 + (k - 1) * 1.3
        pb[f'wrist.{side}'].scale = (h, h, h)
        s = 1 - (k - 1) * 0.4
        pb[f'clavicle.{side}'].scale = (s, s, s)
        # shorten along the bone (Y); the foot undoes it so shoes keep their shape
        pb[f'upperleg01.{side}'].scale = (1.0, lg, 1.0)
        pb[f'foot.{side}'].scale = (1.0, 1.0 / lg, 1.0)
