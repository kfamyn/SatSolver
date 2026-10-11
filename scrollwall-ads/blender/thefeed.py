"""THE FEED — shot-by-shot renderer.

Usage:  python thefeed.py            (draft: tiny, low samples, every 2nd frame)
        PCT=100 SPP=64 STEP=1 python thefeed.py   (final)
        ONLY=10,11 python thefeed.py  (render only those shot numbers)

Writes frames to out/thefeed/frames/ and per-frame post-FX settings to
out/thefeed/fx.json (consumed by post.py).
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Quaternion, Vector

from characters import Doug, Wally, bedroom
from lib import camera, hexc, point_light, reset

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out', 'thefeed')
FRAMES = os.path.join(OUT, 'frames')
os.makedirs(FRAMES, exist_ok=True)
PCT = int(os.environ.get('PCT', 20))
SPP = int(os.environ.get('SPP', 6))
STEP = int(os.environ.get('STEP', 2))
ONLY = {int(x) for x in os.environ.get('ONLY', '').split(',') if x}
MID = os.environ.get('MID') == '1'  # contact sheet: one frame per shot

s = reset()
s.render.resolution_percentage = PCT
s.cycles.samples = SPP
s.view_settings.exposure = 0.8
s.render.use_persistent_data = True
clock_txt = bedroom('11:58')
doug = Doug(origin=(0, 0.45, 0.5), feed_dir=os.path.join(HERE, 'assets', 'feed'))
wally = Wally(origin=(0, -0.25, -5), height=0.8)
wally_glow = point_light('wally_glow', (0, 0, 0), 0, color=hexc('#C9B2FF'), radius=0.25)
cam = camera('cam', lens=35)
sky_mat = bpy.data.materials['window_sky']
moon = bpy.data.objects['moonlight']
fill = bpy.data.objects['fill']
porcelain = bpy.data.materials['wally_porcelain']


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def world(obj):
    bpy.context.view_layer.update()
    return obj.matrix_world.translation.copy()


def place_cam(loc, target, lens=35, roll=0.0, fstop=2.8, focus=None, fisheye=False):
    cam.location = loc
    d = (Vector(target) - Vector(loc)).normalized()
    q = d.to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), roll)
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = q
    c = cam.data
    if fisheye:
        c.type = 'PANO'
        c.panorama_type = 'FISHEYE_EQUISOLID'
        c.fisheye_lens = 7.5
        c.fisheye_fov = math.radians(170)
        c.dof.use_dof = False
    else:
        c.type = 'PERSP'
        c.lens = lens
        c.dof.use_dof = True
        c.dof.aperture_fstop = fstop
        c.dof.focus_distance = focus if focus else (Vector(target) - Vector(loc)).length


# ------------------------------------------------------------------ state helpers

STATE = {'feed': 0.0}


def feed_speed(k):
    """Advance the phone feed; k = clips per second-ish multiplier."""
    STATE['feed'] += k
    doug.screen_tex.image_user.frame_offset = int(STATE['feed']) % 240 - s.frame_current


def spiral_lights(k):
    """k 0..1: how deep into the spiral we are (colder, darker room)."""
    moon.data.energy = lerp(220, 60, k)
    fill.data.energy = lerp(40, 8, k)
    doug.screen_em.inputs['Strength'].default_value = lerp(2.2, 4.0, k)
    doug.phone_light.data.energy = lerp(4.0, 7.0, k)
    sky_mat.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (*hexc('#1B2350'), 1)


def eye_cam(dist=0.13, side=0.015, up=0.004, lens=100, which=1, roll=0.0):
    eye = doug.eyes[which]
    p = world(eye)
    fwd = eye.matrix_world.to_quaternion() @ Vector((0, -1, 0))
    loc = p + fwd * dist + Vector((side, 0, up))
    place_cam(loc, p, lens=lens, roll=roll, fstop=4.0, focus=dist - 0.02)


def thumb_cam(lens=70, roll=0.3):
    p = world(doug.nail)
    loc = p + Vector((0.09, -0.16, 0.03))
    place_cam(loc, p, lens=lens, roll=roll, fstop=5.6)


def clock_cam(lens=90, roll=-0.15):
    p = world(clock_txt)
    place_cam(p + Vector((-0.06, -0.3, 0.04)), p, lens=lens, roll=roll, fstop=2.0)


def phone_pov(lens=16, roll=0.0):
    p = world(doug.phone_pivot)
    h = world(doug.head)
    d = (h - p).normalized()
    place_cam(p + d * 0.02, h, lens=lens, roll=roll, fstop=5.6)


def topdown():
    h = world(doug.head)
    place_cam(h + Vector((0.0, -0.05, 0.9)), h + Vector((0, -0.05, 0)), fisheye=True)


def wide(roll=0.35, lens=20, back=0.0):
    place_cam((0.9 + back * 0.3, -1.35 - back, 1.55), (0.05, 0.3, 1.0), lens=lens, roll=roll, fstop=5.6)


def set_clock(t):
    clock_txt.data.body = t


def hide_wally():
    wally.root.location = (0, -0.25, -5)
    wally_glow.data.energy = 0


# ------------------------------------------------------------------ shots
# Each shot: (frames, fn(t, n) -> fx dict). Frames at 30fps.

def spiral(k):
    def deco(fn):
        def run(t, n):
            spiral_lights(k)
            hide_wally()
            return fn(t, n) or {}
        return run
    return deco


SHOTS = []


def shot(n):
    def reg(fn):
        SHOTS.append((n, fn))
        return fn
    return reg


@shot(14)
@spiral(0.0)
def s01_eye(t, n):
    doug.set_pose(lid=0.4, pupil=0.42)
    feed_speed(1)
    set_clock('11:58')
    eye_cam(dist=0.14 - t * 0.002)
    return {'grain': 0.5, 'chroma': 1, 'vig': 0.6}


@shot(12)
@spiral(0.05)
def s02_top(t, n):
    doug.set_pose(lid=0.4, thumb=(t % 9) / 9)
    feed_speed(1)
    topdown()
    return {'grain': 0.5, 'chroma': 2, 'vig': 0.7}


@shot(10)
@spiral(0.1)
def s03_thumb(t, n):
    doug.set_pose(lid=0.4, thumb=math.sin(t / 10 * math.pi * 2) * 0.5 + 0.5)
    feed_speed(1.2)
    thumb_cam()
    return {'grain': 0.5, 'chroma': 2, 'vig': 0.6}


@shot(14)
@spiral(0.15)
def s04_pov(t, n):
    doug.set_pose(lid=0.45, pupil=0.45)
    feed_speed(1.2)
    phone_pov(roll=0.1 + t * 0.004)
    return {'grain': 0.55, 'chroma': 3, 'vig': 0.7, 'lens': 0.15}


@shot(10)
@spiral(0.2)
def s05_clock(t, n):
    set_clock('12:41')
    clock_cam()
    return {'grain': 0.6, 'chroma': 2, 'vig': 0.7}


@shot(14)
@spiral(0.25)
def s06_dutch(t, n):
    doug.set_pose(lid=0.5)
    feed_speed(1.4)
    wide(roll=0.4, lens=18, back=0.6)
    return {'grain': 0.6, 'chroma': 3, 'vig': 0.8, 'lens': 0.2}


@shot(10)
@spiral(0.3)
def s07_eye(t, n):
    doug.set_pose(lid=0.3, pupil=0.62)
    feed_speed(1.6)
    eye_cam(dist=0.12, side=-0.01, roll=0.2)
    return {'grain': 0.65, 'chroma': 3, 'vig': 0.7}


@shot(8)
@spiral(0.35)
def s08_thumb(t, n):
    doug.set_pose(lid=0.3, thumb=(t % 4) / 4)
    feed_speed(2.2)
    thumb_cam(roll=-0.4)
    return {'grain': 0.7, 'chroma': 4, 'vig': 0.7}


@shot(8)
@spiral(0.4)
def s09_clock(t, n):
    set_clock('2:13')
    clock_cam(roll=0.25)
    return {'grain': 0.7, 'chroma': 4, 'vig': 0.75}


@shot(36)
@spiral(0.5)
def s10_vertigo(t, n):
    k = ease(t / (n - 1))
    # neck creeps toward the phone, eyes widen
    doug.set_pose(lid=lerp(0.3, 0.0, k), pupil=lerp(0.6, 0.85, k), neck_len=lerp(1.0, 3.0, k), head_pitch=lerp(0.95, 1.25, k))
    feed_speed(2.5)
    # dolly zoom: pull back while zooming in, subject stays the same size
    h = world(doug.head)
    dist = lerp(0.9, 3.2, k)
    lens = 24 * dist / 0.9
    loc = h + Vector((0.25, -1, 0.15)).normalized() * dist
    place_cam(loc, h, lens=lens, fstop=4.0)
    return {'grain': 0.75, 'chroma': lerp(4, 8, k), 'vig': 0.85}


@shot(6)
@spiral(0.6)
def s11_thumb(t, n):
    doug.set_pose(lid=0.0, pupil=0.85, neck_len=3.0, head_pitch=1.25, thumb=(t % 3) / 3)
    feed_speed(3)
    thumb_cam(roll=0.6)
    return {'grain': 0.8, 'chroma': 6, 'vig': 0.8, 'glitch': 0.4}


@shot(6)
@spiral(0.65)
def s12_clock(t, n):
    set_clock('3:47')
    clock_cam(roll=-0.4, lens=120)
    return {'grain': 0.8, 'chroma': 7, 'vig': 0.8, 'glitch': 0.6}


@shot(24)
@spiral(0.75)
def s13_face(t, n):
    k = t / (n - 1)
    doug.set_pose(lid=0.0, pupil=0.97, neck_len=3.0, head_pitch=1.25, mouth_open=k)
    feed_speed(3.5)
    h = world(doug.head)
    fwd = doug.head.matrix_world.to_quaternion() @ Vector((0, -1, 0))
    jitter = Vector((math.sin(t * 1.7) * 0.006, 0, math.cos(t * 2.3) * 0.006))
    place_cam(h + fwd * 0.6 + Vector((0.08, 0, 0)) + jitter, h, lens=40, roll=0.15, fstop=2.8)
    return {'grain': 0.85, 'chroma': lerp(7, 11, k), 'vig': 0.9}


MICRO = ['eye', 'thumb', 'clock', 'pov', 'eye', 'top']


@shot(24)
@spiral(0.85)
def s14_micro(t, n):
    kind = MICRO[min(len(MICRO) - 1, t // 4)]
    doug.set_pose(lid=0.0, pupil=0.97, neck_len=3.0, head_pitch=1.25, thumb=(t % 2) * 1.0, mouth_open=1)
    feed_speed(4)
    set_clock('3:48')
    {'eye': lambda: eye_cam(dist=0.1, roll=0.5), 'thumb': lambda: thumb_cam(roll=-0.7), 'clock': lambda: clock_cam(roll=0.5),
     'pov': lambda: phone_pov(roll=-0.4), 'top': topdown}[kind]()
    return {'grain': 0.9, 'chroma': 12, 'vig': 0.9, 'glitch': 1.0}


@shot(24)
@spiral(1.0)
def s15_swallow(t, n):
    k = t / (n - 1)
    doug.set_pose(lid=0.0, pupil=0.97, neck_len=3.2, head_pitch=1.3, mouth_open=1)
    feed_speed(5)
    doug.screen_em.inputs['Strength'].default_value = lerp(4, 60, k ** 2)
    doug.phone_light.data.energy = lerp(7, 60, k ** 2)
    h = world(doug.head)
    p = world(doug.phone_pivot)
    # over the shoulder, pushing in toward the screen
    start = h + Vector((0.18, 0.25, 0.12))
    place_cam(start.lerp(p, k * 0.75), p, lens=lerp(28, 18, k), fstop=2.8)
    return {'grain': 0.95, 'chroma': lerp(12, 20, k), 'vig': 0.9, 'glitch': 0.3 + k * 0.7, 'flash': k ** 3 * 0.9}


@shot(30)
def s16_slam(t, n):
    # Wally drops onto the bed in front of Doug; the phone is knocked away.
    fall = min(1.0, t / 5)
    z = lerp(3.0, 0.5, fall ** 2)
    land = t - 5
    sq = 1 + (math.sin(min(1, land / 8) * math.pi) * 0.22 if land >= 0 else 0)
    wally.root.location = (0, -0.22, z)
    wally.root.scale = (sq, sq, 1 / sq)
    doug.set_pose(lid=0.0, pupil=0.35, neck_len=lerp(3.2, 1.0, ease(t / 6)), head_pitch=lerp(1.3, 0.3, ease(t / 6)), mouth_open=1)
    # phone flies off and lands face down; room goes dark except Wally
    kp = ease((t - 4) / 12)
    doug.phone_pivot.location = (lerp(0, 0.45, kp), lerp(-0.22, -0.75, kp), lerp(0.5, 0.0, kp) + math.sin(kp * math.pi) * 0.25)
    doug.phone_pivot.rotation_euler = (lerp(0.65, math.pi * 1.5, kp), lerp(0, 0.6, kp), 0)
    on = t < 5
    doug.screen_em.inputs['Strength'].default_value = 3.0 if on else 0.0
    doug.phone_light.data.energy = 6.0 if on else 0.0
    moon.data.energy = 60
    fill.data.energy = 8
    porcelain.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.25 if t < 5 else 1.2
    wally_glow.location = (0, 0.06, 1.0)
    wally_glow.data.energy = 0 if t < 5 else 18
    place_cam((0.95, -1.75, 0.75), (0, 0.0, 0.95), lens=20, roll=0.05, fstop=5.6)
    shake = max(0, 1 - (t - 5) / 8) if t >= 5 else 0
    return {'grain': 0.5, 'chroma': 6 * shake, 'vig': 0.6, 'flash': 1.0 if t == 5 else (0.5 if t == 6 else 0), 'shake': shake}


@shot(45)
def s17_still(t, n):
    blink = 1.0 if 18 <= t <= 21 else 0.15
    doug.set_pose(lid=blink, pupil=0.4, head_pitch=0.15, mouth_open=0.2 if t < 20 else 0)
    wally.root.location = (0, -0.22, 0.5)
    wally.root.scale = (1, 1, 1)
    wally.root.rotation_euler = (0, lerp(0, 0.22, ease((t - 22) / 14)), 0)  # head tilt: "hm?"
    porcelain.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.2
    wally_glow.data.energy = 18
    doug.screen_em.inputs['Strength'].default_value = 0
    doug.phone_light.data.energy = 0
    h = world(doug.head)
    place_cam(h + Vector((0.55, -1.35, -0.1)), h + Vector((0.15, -0.35, -0.2)), lens=45, fstop=2.8)
    return {'grain': 0.35, 'chroma': 0.5, 'vig': 0.5}


@shot(60)
def s18_dawn(t, n):
    k = ease(t / (n - 1))
    doug.set_pose(lid=0.25, pupil=0.38, head_pitch=0.0)
    wally.root.rotation_euler = (0, 0.22 * (1 - k), 0)
    sky = Vector(hexc('#1B2350')).lerp(Vector(hexc('#FFB27A')), k)
    sky_mat.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (*sky, 1)
    sky_mat.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = lerp(1.5, 6, k)
    moon.data.color = tuple(Vector(hexc('#8FA8FF')).lerp(Vector(hexc('#FFC48A')), k))
    moon.data.energy = lerp(60, 500, k)
    wally_glow.data.energy = lerp(18, 6, k)
    place_cam((0.6, -2.9, 1.3), (-0.2, 0.4, 1.0), lens=lerp(30, 34, k), fstop=5.6)
    return {'grain': 0.3, 'chroma': 0.3, 'vig': 0.45}


# ------------------------------------------------------------------ render loop

def main():
    fx = {}
    g = 0
    for i, (n, fn) in enumerate(SHOTS, start=1):
        for t in range(n):
            g += 1
            if ONLY and i not in ONLY:
                continue
            s.frame_set(g)
            info = fn(t, n) or {}
            info['shot'] = i
            fx[g] = info
            if MID:
                if t != n // 2:
                    continue
            elif (g - 1) % STEP:
                continue
            s.render.filepath = os.path.join(FRAMES, f'{g:04d}.png')
            bpy.ops.render.render(write_still=True)
            print(f'shot {i:02d} frame {g}', flush=True)
    with open(os.path.join(OUT, 'fx.json'), 'w') as f:
        json.dump({'total': g, 'step': STEP, 'frames': fx}, f)
    print('TOTAL', g)


main()
