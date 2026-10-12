"""The character's PS1 proportions: a slightly oversized head and hands, like
late-90s game characters. One knob (PROP, default 1.15) scales the look up or
down; 1.0 = realistic."""
import os


def apply_style(rig, amount=None):
    k = float(os.environ.get('PROP', 1.15)) if amount is None else amount
    pb = rig.pose.bones
    pb['head'].scale = (k, k, k)
    for side in ('L', 'R'):
        h = 1 + (k - 1) * 1.3
        pb[f'wrist.{side}'].scale = (h, h, h)
    # a little narrower in the shoulders sells the big head
    for side in ('L', 'R'):
        s = 1 - (k - 1) * 0.4
        pb[f'clavicle.{side}'].scale = (s, s, s)
