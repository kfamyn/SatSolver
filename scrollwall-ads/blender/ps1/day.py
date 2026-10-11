"""SCROLLWALL — "Day" (PS1 style). Shot-by-shot renderer.

Draft:  python day.py                      (tiny, low spp, every 2nd frame)
Final:  RES=270 SPP=24 STEP=1 python day.py
Only some shots:  ONLY=A1,B1 python day.py   |   one frame per shot: MID=1

Writes raw frames to out/ps1day/frames and per-frame HUD/grade/fx data to
out/ps1day/meta.json for post.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector

import rig
import scene as S

OUT = os.path.join(S.HERE, '..', '..', 'out', 'ps1day')
FR = os.path.join(OUT, 'frames')
os.makedirs(FR, exist_ok=True)
RESW = int(os.environ.get('RES', 135))
SPP = int(os.environ.get('SPP', 8))
STEP = int(os.environ.get('STEP', 2))
ONLY = {x for x in os.environ.get('ONLY', '').split(',') if x}
MID = os.environ.get('MID') == '1'

s = rig.setup((RESW, RESW * 16 // 9), SPP)
clock = S.room()
hour_hand = bpy.data.objects['clock_hour']
min_hand = bpy.data.objects['clock_min']
sky = bpy.data.objects['window_sky']
SKIES = {k: S.tmat(f'sky_{k}', emission=2.0) for k in ('morning', 'noon', 'evening')}
sun = rig.sun()
rig.bounce()
doug = S.Doug()
doug.root.scale = (1.2, 1.2, 1.2)
cam = rig.Cam()
FEED = [S.img(f'feed/{i:04d}') for i in range(1, 129)]
SHIELD = [S.img(f'screens/shield_{i:02d}') for i in range(13)]
BAL = {n: S.img(f'screens/balance_{n:02d}') for n in range(0, 51, 5)}
UNLOCK = {k: S.img(f'screens/unlock_{k}') for k in ('offer', 'tilt', 'done')}

# '!' balloon above Doug's head
bang = S.plane('bang', 0.22, 0.28, (0, -0.05, 0.55), S.tmat('bang', alpha=True, emission=0.6), par=doug.neck)
bang.hide_render = True

# desk props: open book + a second phone lying face-up showing the balance
book = S.empty('book', (1.4, 0.62, 0.78))
S.box('book_l', (0.22, 0.3, 0.02), (-0.11, 0, 0), S.tmat('book_pages'), par=book, rot=(0, 0.08, 0))
S.box('book_r', (0.22, 0.3, 0.02), (0.11, 0, 0), S.tmat('book_pages'), par=book, rot=(0, -0.08, 0))
page = S.empty('page', (0, 0, 0.012), book)
S.box('page_flip', (0.21, 0.29, 0.004), (0.105, 0, 0), S.tmat('book_pages'), par=page)
desk_phone = S.empty('desk_phone', (0.98, 0.72, 0.79))
S.box('dp_body', (0.24, 0.46, 0.025), (0, 0, 0), S.tmat('black_plastic'), par=desk_phone)
dp_mat = bpy.data.materials.new('m_dp')
dp_mat.use_nodes = True
_nt = dp_mat.node_tree
_nt.nodes.clear()
_o = _nt.nodes.new('ShaderNodeOutputMaterial')
_e = _nt.nodes.new('ShaderNodeEmission')
dp_tex = _nt.nodes.new('ShaderNodeTexImage')
dp_tex.interpolation = 'Closest'
_nt.links.new(dp_tex.outputs['Color'], _e.inputs['Color'])
_e.inputs['Strength'].default_value = 2.2
_nt.links.new(_e.outputs['Emission'], _o.inputs['Surface'])
S.plane('dp_screen', 0.215, 0.43, (0, 0, 0.0135), dp_mat, rot=(0, 0, math.pi), par=desk_phone)
coins = [S.cyl(f'coin{i}', 0.035, 0.01, (0, 0, -5), S.tmat('coin'), seg=8) for i in range(14)]

BED = ((-0.55, 1.0, 0.42), 0.0)
DESK = ((1.35, 0.1, 0.37), math.pi)


def place_doug(where):
    loc, rz = where
    doug.root.location = loc
    doug.root.rotation_euler = (0, 0, rz)


def set_time(hour):
    hour_hand.rotation_euler = (0, math.radians((hour % 12) * 30), 0)
    min_hand.rotation_euler = (0, math.radians((hour % 1) * 360), 0)
    rig.set_sun(sun, hour)
    key = 'morning' if hour < 11.5 else ('noon' if hour < 15.5 else 'evening')
    sky.data.materials[0] = SKIES[key]


def hide_coins():
    for c in coins:
        c.location = (0, 0, -5)


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


STATE = {'feed': 0.0}


def feed_tick(speed=1.0):
    STATE['feed'] += speed
    doug.set_screen(FEED[int(STATE['feed']) % len(FEED)], 2.4)


def wasted(g):
    """TIME WASTED counter: accelerates with the cuts."""
    secs = int(2 * 3600 + 14 * 60 + (g ** 1.6) * 9)
    return f'{secs // 3600:02d}:{(secs // 60) % 60:02d}:{secs % 60:02d}'


# ------------------------------------------------------------------ cameras (bed)

def cam_wide(k):
    cam.set(Vector((1.75, -2.4, 1.7)).lerp(Vector((0.85, -1.25, 1.4)), k), (-0.4, 0.65, 0.85), lens=lerp(18, 22, k))


def head():
    return rig.world(doug.head)


def phone_pos():
    return rig.world(doug.phone)


def cam_face(roll=0.1):
    h = head()
    cam.set(h + Vector((0.35, -1.0, 0.25)), h + Vector((0.02, -0.2, -0.15)), lens=32, roll=roll)


def cam_low():
    cam.set((0.05, -0.85, 0.66), head() + Vector((0, 0, -0.05)), lens=14, roll=-0.25)


def cam_top():
    h = head()
    cam.set(h + Vector((0.1, -0.45, 1.9)), h + Vector((0, -0.3, -0.4)), lens=22, roll=0.6)


def cam_clock():
    c = rig.world(clock)
    cam.set(c + Vector((0.06, -0.75, -0.04)), c, lens=40, roll=-0.12)


def cam_eye():
    h = head()
    cam.set(h + Vector((-0.32, -0.72, 0.2)), h + Vector((0.0, -0.18, 0.0)), lens=55, roll=-0.25)


def cam_ots():
    h = head()
    p = phone_pos()
    cam.set(h + Vector((0.6, 0.1, 0.55)), p, lens=26, roll=0.08)


def cam_swipe():
    p = phone_pos()
    cam.set(p + Vector((0.55, -0.1, 0.05)), p + Vector((0.0, 0.12, 0.05)), lens=22, roll=0.3)


def cam_phone(dist=0.62, roll=0.0, lens=40):
    doug.screen_front.hide_render = False
    p = phone_pos()
    f = rig.forward(doug.phone)
    cam.set(p + f * dist, p, lens=lens, roll=roll)


# ------------------------------------------------------------------ shots

SHOTS = []


def shot(name, n):
    def reg(fn):
        SHOTS.append((name, n, fn))
        return fn
    return reg


def trance_base(t, g, hour, speed=1.0, face=True):
    place_doug(BED)
    set_time(hour)
    hide_coins()
    bang.hide_render = True
    doug.screen_front.hide_render = True
    ta = t - (t % 2)  # character animation on twos
    doug.pose_scroll((ta % 12) / 12)
    if face:
        doug.set_face('trance_blink' if (g % 47) < 3 else 'trance')
    feed_tick(speed)
    return {'hud': [['TIME WASTED', wasted(g), '#FF6B5E']], 'grade': 'trance', 'tick': t == 0}


# ACT 1 — the trance: every tick cuts to a new angle; we keep returning to the wide.
@shot('A1', 30)
def a1(t, n, g):
    m = trance_base(t, g, 10)
    cam_wide(0.0 + t / n * 0.12)
    return m


@shot('A2', 18)
def a2(t, n, g):
    m = trance_base(t, g, 11)
    cam_low()
    return m


@shot('A3', 24)
def a3(t, n, g):
    m = trance_base(t, g, 12)
    cam_wide(0.15 + t / n * 0.12)
    return m


@shot('A4', 16)
def a4(t, n, g):
    m = trance_base(t, g, 13)
    cam_face()
    return m


@shot('A5', 18)
def a5(t, n, g):
    m = trance_base(t, g, 14, 1.3)
    cam_wide(0.3 + t / n * 0.12)
    return m


@shot('A6', 12)
def a6(t, n, g):
    m = trance_base(t, g, 15, 1.3)
    cam_top()
    return m


@shot('A7', 14)
def a7(t, n, g):
    m = trance_base(t, g, 15.5, 1.5)
    cam_wide(0.48 + t / n * 0.1)
    return m


@shot('A8', 10)
def a8(t, n, g):
    m = trance_base(t, g, 16, 1.5)
    cam_clock()
    return m


@shot('A9', 10)
def a9(t, n, g):
    m = trance_base(t, g, 16.5, 1.8)
    cam_eye()
    return m


@shot('A10', 10)
def a10(t, n, g):
    m = trance_base(t, g, 17, 1.8)
    cam_ots()
    return m


@shot('A11', 8)
def a11(t, n, g):
    m = trance_base(t, g, 17.2, 2.0)
    cam_wide(0.7)
    return m


@shot('A12', 8)
def a12(t, n, g):
    m = trance_base(t, g, 17.5, 2.2)
    cam_swipe()
    return m


@shot('A13', 8)
def a13(t, n, g):
    m = trance_base(t, g, 18, 2.2)
    cam_clock()
    return m


@shot('A14', 16)
def a14(t, n, g):
    m = trance_base(t, g, 18.2, 2.5)
    cam_phone(dist=0.7 - t * 0.006)
    return m


# ACT 2 — the wall
@shot('B1', 46)
def b1(t, n, g):
    m = trance_base(t, g, 18.3, 2.5 if t < 4 else 0)
    drop_i = max(0, min(12, t - 3))
    if t >= 3:
        doug.set_screen(SHIELD[drop_i], 2.4)
    cam_phone(dist=0.58, roll=0.0)
    slam = 3 + 8
    m['tick'] = False
    m['slam'] = t == slam
    m['shake'] = max(0.0, 1 - (t - slam) / 10) if t >= slam else 0
    m['flash'] = 0.8 if t == slam else 0
    if t >= slam:
        m['hud'] = [['TIME WASTED', wasted(g - t + slam), '#FF6B5E']]
    return m


@shot('B2', 44)
def b2(t, n, g):
    place_doug(BED)
    set_time(18.3)
    hide_coins()
    doug.screen_front.hide_render = True
    doug.set_screen(SHIELD[12], 2.4)
    doug.pose_scroll(0.0, head_pitch=lerp(0.45, 0.05, ease((t - 10) / 8)), phone=(0.0, -0.45, lerp(0.56, 0.3, ease((t - 10) / 8))))
    face = 'trance' if t < 6 else ('blink' if t < 12 else ('surprised' if t < 30 else 'normal'))
    doug.set_face(face)
    bang.hide_render = not (14 <= t < 34)
    h = head()
    cam.set(h + Vector((0.2, -1.25, 0.05)), h + Vector((0, 0, 0.05)), lens=lerp(30, 36, t / n))
    return {'hud': [['FOCUSCOINS', '0', '#F0B55C']], 'grade': 'trance' if t < 10 else 'warm', 'alert': t == 14, 'blink': t == 6}


# ACT 3 — focus: coins pile into his balance
def desk_base(t, hour, face='focus'):
    place_doug(DESK)
    set_time(hour)
    bang.hide_render = True
    doug.screen_front.hide_render = True
    doug.phone.location = (0, 0, -5)  # his own phone is down on the desk now
    for s_ in (-1, 1):
        doug.aim_arm(s_, Vector((s_ * 0.16, -0.42, 0.33)))
    ta = t - (t % 2)
    doug.neck.rotation_euler = (0.45 + math.sin(ta / 6) * 0.04, 0, 0)
    doug.set_face(face)
    for o in doug.legs:
        o.hide_render = False


def coins_fall(t, start=0, every=3, target=(0.98, 0.72, 0.81)):
    for i, c in enumerate(coins):
        tt = (t - start - i * every) / 8
        if tt < 0:
            c.location = (0, 0, -5)
            continue
        tt = min(1, tt)
        x = target[0] + ((i * 37) % 7 - 3) * 0.06
        y = target[1] + ((i * 53) % 5 - 2) * 0.11
        c.location = (x, y, lerp(target[2] + 0.9, target[2] + 0.005 * i, tt * tt))
        c.rotation_euler = ((1 - tt) * 9 + i, 0, i)


def balance_for(t, n, lo=0, hi=50):
    v = int(lo + (hi - lo) * min(1, t / max(1, n - 1)))
    return v - v % 5


def timer_txt(k):
    secs = int((1 - k) * 25 * 60)
    return f'{secs // 60:02d}:{secs % 60:02d}'


@shot('C1', 40)
def c1(t, n, g):
    desk_base(t, 18.5)
    bal = balance_for(t, 120, 0, 50)
    dp_tex.image = BAL[bal]
    coins_fall(t, 6, 6)
    page.rotation_euler = (0, -math.pi * ease(((t % 20) - 10) / 6), 0)
    cam.set((0.85, 1.45, 1.4), (1.35, 0.1, 0.95), lens=22, roll=-0.05)
    return {'hud': [['FOCUS', timer_txt(t / 120), '#FFFFFF'], ['FOCUSCOINS', str(bal), '#F0B55C']], 'grade': 'warm', 'music': True,
            'coin': t >= 14 and (t - 14) % 6 == 0}


@shot('C2', 30)
def c2(t, n, g):
    T = t + 40
    desk_base(T, 18.5)
    bal = balance_for(T, 120, 0, 50)
    dp_tex.image = BAL[bal]
    coins_fall(T, 6, 6)
    p = rig.world(desk_phone)
    cam.set(p + Vector((0.12, -0.35, 0.85)), p, lens=26, roll=0.2)
    return {'hud': [['FOCUS', timer_txt(T / 120), '#FFFFFF'], ['FOCUSCOINS', str(bal), '#F0B55C']], 'grade': 'warm', 'music': True,
            'coin': (T - 14) % 6 == 0}


@shot('C3', 30)
def c3(t, n, g):
    T = t + 70
    desk_base(T, 18.5)
    bal = balance_for(T, 120, 0, 50)
    dp_tex.image = BAL[bal]
    coins_fall(T, 6, 6)
    page.rotation_euler = (0, -math.pi * ease(((T % 20) - 10) / 6), 0)
    h = head()
    cam.set(h + Vector((-1.15, 0.45, 0.05)), h + Vector((0, 0.15, -0.1)), lens=30, roll=-0.1)
    return {'hud': [['FOCUS', timer_txt(T / 120), '#FFFFFF'], ['FOCUSCOINS', str(bal), '#F0B55C']], 'grade': 'warm', 'music': True,
            'coin': (T - 14) % 6 == 0}


@shot('C4', 20)
def c4(t, n, g):
    T = t + 100
    desk_base(T, 18.5, 'happy' if t > 8 else 'focus')
    if t > 6:  # little cheer
        for s_ in (-1, 1):
            doug.aim_arm(s_, Vector((s_ * 0.38, -0.05, 0.95 + 0.04 * math.sin(t))))
    dp_tex.image = BAL[50]
    coins_fall(T, 6, 6)
    p = rig.world(desk_phone)
    cam.set(p + Vector((0.0, -0.05, 0.75)), p, lens=30, roll=0.0)
    return {'hud': [['FOCUS', '00:00', '#4CD98B'], ['FOCUSCOINS', '50', '#F0B55C']], 'grade': 'warm', 'music': True, 'ding': t == 4}


# ACT 4 — spend: tilt to pay with the FocusCard
def hold_phone(t, tilt=0.0):
    place_doug(BED)
    set_time(18.6)
    hide_coins()
    bang.hide_render = True
    for o in doug.legs:
        o.hide_render = True
    doug.pose_scroll(0.0, head_pitch=0.3)
    P = Vector((0.0, -0.5, 0.56))
    doug.set_phone(P, tilt=0.35 + tilt)
    doug.aim_arm(-1, P + Vector((-0.13, 0.03, -0.1)))
    doug.aim_arm(1, P + Vector((0.13, 0.03, -0.1)))


@shot('D1', 30)
def d1(t, n, g):
    hold_phone(t)
    doug.set_face('normal')
    doug.set_screen(UNLOCK['offer'], 2.4)
    cam_phone(dist=0.6)
    return {'hud': [['FOCUSCOINS', '50', '#F0B55C']], 'grade': 'warm', 'music': True, 'tap': t == 16}


@shot('D2', 30)
def d2(t, n, g):
    k = ease((t - 4) / 14) * (1 - ease((t - 22) / 6))
    hold_phone(t, tilt=-1.0 * k)  # whole-arm tilt away
    doug.set_face('focus' if t < 18 else 'happy')
    doug.set_screen(UNLOCK['tilt'] if t < 18 else UNLOCK['done'], 2.4)
    h = head()
    cam.set(h + Vector((0.95, -0.9, -0.1)), h + Vector((0.1, -0.4, -0.2)), lens=26, roll=0.05)
    return {'hud': [['FOCUSCOINS', '50' if t < 18 else '10', '#F0B55C']], 'grade': 'warm', 'music': True, 'chime': t == 18}


@shot('D3', 24)
def d3(t, n, g):
    hold_phone(t)
    doug.set_face('happy')
    doug.set_screen(UNLOCK['done'], 2.4)
    cam_phone(dist=0.55 - t * 0.003)
    return {'hud': [['FOCUSCOINS', '10', '#F0B55C']], 'grade': 'warm', 'music': True}


# ACT 5 — present: relaxed scroll, timer running, golden hour
@shot('E1', 90)
def e1(t, n, g):
    place_doug(BED)
    set_time(18.8)
    hide_coins()
    bang.hide_render = True
    doug.screen_front.hide_render = True
    ta = t - (t % 2)
    doug.pose_scroll((ta % 30) / 30, head_pitch=0.3)  # slow, chill swipes
    doug.set_face('blink' if 40 <= t < 43 else 'happy')
    feed_tick(0.5)
    secs = 300 - t // 30 - 1
    cam_wide(0.55 + t / n * 0.15)
    return {'hud': [['SCREEN TIME', f'{secs // 60}:{secs % 60:02d}', '#4CD98B']], 'grade': 'golden', 'music': True}


# ------------------------------------------------------------------ render loop

def main():
    meta = {}
    g = 0
    for name, n, fn in SHOTS:
        for t in range(n):
            g += 1
            if ONLY and name not in ONLY:
                continue
            s.frame_set(g)
            m = fn(t, n, g) or {}
            m['shot'] = name
            meta[g] = m
            if MID:
                if t != n // 2:
                    continue
            elif (g - 1) % STEP:
                continue
            s.render.filepath = os.path.join(FR, f'{g:04d}.png')
            bpy.ops.render.render(write_still=True)
            print(f'{name} {g}', flush=True)
    with open(os.path.join(OUT, 'meta.json'), 'w') as f:
        json.dump({'total': g, 'frames': meta}, f)
    print('TOTAL', g, flush=True)


main()
