"""Reel 2 renderer: subway, 'what if scrolling cost money?'.

Draft: RES=180 SPP=6 python render.py   (every frame, 30 fps)
ONLY=3,7 renders some shots; MID=1 one frame per shot.
Reads <REEL>/timings.json (script.py), writes <REEL>/<FRAMES>/NNNN.png + meta.json.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Quaternion, Vector

import cast as K

REEL = os.environ.get('REEL', '/home/user/reel4')
T = json.load(open(os.path.join(REEL, 'timings.json')))
FR = os.path.join(REEL, os.environ.get('FRAMES', 'frames'))
os.makedirs(FR, exist_ok=True)
RES = int(os.environ.get('RES', 180))
SPP = int(os.environ.get('SPP', 6))
ONLY = {int(x) for x in os.environ.get('ONLY', '').split(',') if x}
MID = os.environ.get('MID') == '1'
DRY = os.environ.get('DRY') == '1'  # compute meta.json only (for sound), no rendering
STEP = int(os.environ.get('STEP', 1))  # 2 = 15 fps scene-check drafts

C = K.load_cast()
import props as P  # noqa: E402
import subway  # noqa: E402

s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = SPP
s.cycles.use_denoising = True
s.cycles.max_bounces = 3
s.cycles.filter_width = 0.01
s.render.resolution_x, s.render.resolution_y = RES, RES * 16 // 9
s.render.resolution_percentage = 100
s.render.use_persistent_data = True
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'None'
s.view_settings.exposure = -0.3
S = subway.build()
subway.lights()

hero, office, worker, student, business = (C[k] for k in ('hero', 'office', 'worker', 'student', 'business'))
bg = [K.clone(worker, 'bg1'), K.clone(office, 'bg2'), K.clone(business, 'bg3')]
HERO_X, BUS_X, OFF_X, WRK_X = 0.55, -0.75, 0.15, 1.05

phone, ptex = P.phone('hero_phone', 'r2screens/paid/00')
P.hold_phone(phone, hero)
pl = bpy.data.lights.new('phone_light', 'POINT')
pl.energy, pl.color, pl.shadow_soft_size = 1.5, (0.7, 0.82, 1.0), 0.04
plo = bpy.data.objects.new('phone_light', pl)
s.collection.objects.link(plo)
plo.parent = phone
plo.location = (0, -0.12, 0.05)
book = P.book('office_book')
hbook = P.book('hero_book')
paper = P.newspaper()

cd = bpy.data.cameras.new('cam')
cd.sensor_fit = 'VERTICAL'
cd.clip_start = 0.01
cam = bpy.data.objects.new('cam', cd)
s.collection.objects.link(cam)
s.camera = cam


# ------------------------------------------------------------------ helpers
def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def sway(g, amt=0.006):
    """train rocking, applied to every camera."""
    return Vector((math.sin(g * 0.21) * amt, math.sin(g * 0.13 + 1) * amt, math.sin(g * 0.37) * amt * 0.6))


G = [0]


def place(loc, target, lens=24, roll=0.0):
    loc = Vector(loc) + sway(G[0])
    target = Vector(target)
    cam.location = loc
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (target - loc).normalized().to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), roll)
    cd.lens = lens


def place_up(loc, target, up, lens=30):
    loc, target, up = Vector(loc) + sway(G[0], 0.003), Vector(target), Vector(up).normalized()
    fwd = (target - loc).normalized()
    right = fwd.cross(up).normalized()
    up2 = right.cross(fwd).normalized()
    cam.rotation_mode = 'QUATERNION'
    cam.location = loc
    cam.rotation_quaternion = Matrix((right, up2, -fwd)).transposed().to_quaternion()
    cd.lens = lens


def move(k, a, b, lens=(24, 24), roll=(0, 0)):
    e = ease(k)
    place(Vector(a[0]).lerp(Vector(b[0]), e), Vector(a[1]).lerp(Vector(b[1]), e), lens[0] + (lens[1] - lens[0]) * e,
          roll[0] + (roll[1] - roll[0]) * e)


def wpos(obj):
    bpy.context.view_layer.update()
    return obj.matrix_world.translation.copy()


def phone_up():
    bpy.context.view_layer.update()
    return (phone.matrix_world.to_quaternion() @ Vector((0, 0, 1))).normalized()


def phone_normal():
    bpy.context.view_layer.update()
    return (phone.matrix_world.to_quaternion() @ Vector((0, -1, 0))).normalized()


def insert(k, a=0.78, b=0.66, lens=32):
    p, e = wpos(phone), K.eyes(hero)
    place_up(p + (e - p) * (a + (b - a) * ease(k)), p, phone_up(), lens)


def pov(k):
    e, p = K.eyes(hero), wpos(phone)
    d = (p - e).normalized()
    place_up(e + d * (0.04 + 0.07 * ease(k)) + Vector((0.0, 0, 0.03)), p, phone_up(), 28)


def screen(rel):
    ptex.image = P.img(rel)


def proj(pt):
    v = world_to_camera_view(s, cam, Vector(pt))
    return [v.x, 1 - v.y]


def head_dir_to(p, target):
    """yaw (radians) that turns a seated person's head toward a world point."""
    bpy.context.view_layer.update()
    h = p['rig'].matrix_world @ p['rig'].pose.bones['head'].head
    fwd = p['rig'].matrix_world.to_quaternion() @ Vector((0, -1, 0))
    to = (Vector(target) - h)
    a = math.atan2(fwd.x * to.y - fwd.y * to.x, fwd.x * to.x + fwd.y * to.y)
    return max(-1.3, min(1.3, a))


def everyone(t, judge=0.0, phones_down=True):
    """Default world state: nobody else on a phone; judge>0 turns heads toward the hero."""
    K.seat(business, BUS_X, 1, 'paper', t=t)
    K.seat(office, OFF_X, -1, 'read', t=t)
    K.seat(worker, WRK_X, -1, 'idle', t=t)
    K.stand(student, 2.3, -0.35, facing=math.pi / 2, t=t)
    K.seat(bg[0], -3.7, -1, 'phone_down', t=t)
    K.seat(bg[1], -4.2, 1, 'idle', t=t)
    K.stand(bg[2], -3.0, -0.3, facing=-math.pi / 2, t=t)
    hx = K.eyes(hero) if judge > 0 else None
    for p in (office, worker, bg[0], bg[1]):
        if judge > 0:
            K.turn_head(p, head_dir_to(p, hx) * judge, 0.0)
    place_props(paper_down=judge * 0.6)


def place_props(paper_down=0.0, book_down=0.0):
    P.between_hands(book, office, K.eyes(office), lift=0.07 - book_down * 0.12)
    P.between_hands(paper, business, K.eyes(business), lift=0.12 - paper_down * 0.25, push=-0.05)


def hero_pose(t, act='scroll', speed=1.0):
    K.seat(hero, HERO_X, 1, act, t=t * speed)


# ------------------------------------------------------------------ shots
def shot(i, t, n, g):
    k = t / max(1, n - 1)
    sid = T['shots'][i]['id']
    meta = {}
    subway.set_tunnel(S, g / 30)
    phone.hide_render = plo.hide_render = False
    hbook.hide_render = True
    pl.color, pl.energy = (0.7, 0.82, 1.0), 1.5
    pops = []
    everyone(g)

    if sid == 'hook_pov':
        hero_pose(t, 'scroll', 2.0)
        sw = 14
        screen('r2screens/paid/' + ('01' if t >= sw else '00'))
        pov(k)
        if t >= sw:
            pops.append(('-$0.01', proj(wpos(phone) + phone_up() * 0.1), t - sw, 'red'))
        meta['kaching'] = t == sw
    elif sid == 'hook_face':
        hero_pose(t, 'phone')
        screen('r2screens/paid/01')
        e = K.eyes(hero)
        move(k, (e + Vector((0.38, -0.42, -0.02)), e), (e + Vector((0.32, -0.36, -0.02)), e), (32, 36))
    elif sid == 'ticker':
        hero_pose(t, 'scroll', 2.0)
        every = 8
        c = 1 + t // every
        screen(f'r2screens/paid/{min(60, c):02d}')
        insert(k, 0.75, 0.62)
        for j in range(1, c + 1):
            age = t - (j - 1) * every
            if 0 <= age < 14:
                pops.append(('-$0.01', proj(wpos(phone) + phone_up() * 0.09), age, 'red'))
        meta['kaching'] = t % every == 0
    elif sid == 'aisle':
        hero_pose(t, 'scroll')
        screen('r2screens/paid/09')
        move(k, ((4.5, 0.05, 1.5), (-1.0, 0.0, 1.0)), ((3.7, 0.0, 1.45), (-1.0, 0.0, 1.0)), (16, 17))
    elif sid == 'paper':
        hero_pose(t, 'scroll')
        pc = wpos(paper)
        move(k, (pc + Vector((0.05, -1.15, 0.0)), pc), (pc + Vector((0.04, -0.85, 0.0)), pc), (30, 32))
    elif sid == 'book':
        hero_pose(t, 'scroll')
        e = K.eyes(office)
        move(k, (e + Vector((0.25, 0.75, -0.1)), e + Vector((0, 0, -0.15))), (e + Vector((0.2, 0.6, -0.08)), e + Vector((0, 0, -0.15))), (28, 30))
    elif sid in ('eyes1', 'eyes2', 'eyes_away'):
        hero_pose(t, 'scroll')
        look = ease(k / 0.5) if sid == 'eyes1' else 1.0
        if sid == 'eyes_away':
            look = 1.0 if t < 8 else 0.0
        # office looks up from the book toward the businessman, who lowers his paper
        K.seat(office, OFF_X, -1, 'read' if look < 0.5 else 'look_up', t=g)
        K.seat(business, BUS_X, 1, 'paper' if sid == 'eyes1' else 'look_up', t=g)
        eo, eb = K.eyes(office), K.eyes(business)
        if look > 0:
            K.turn_head(office, head_dir_to(office, eb) * look)
        if sid != 'eyes1':
            K.turn_head(business, head_dir_to(business, eo) * (look if sid == 'eyes_away' else ease(k / 0.5)))
        if sid == 'eyes_away' and t >= 8:  # both snap away
            K.turn_head(office, 1.1 * ease((t - 8) / 3))
            K.turn_head(business, -1.1 * ease((t - 8) / 3))
            meta['whip'] = t == 8
        place_props(paper_down=0.0 if sid == 'eyes1' else 1.0, book_down=look)
        eo, eb = K.eyes(office), K.eyes(business)
        if sid == 'eyes1':  # close on her face, from his side of the aisle
            d = (eb - eo).normalized()
            place(eo + d * 0.6 + Vector((0.25, 0, 0.02)), eo, 32)
        elif sid == 'eyes2':  # close on his face, from her side
            d = (eo - eb).normalized()
            place(eb + d * 0.6 + Vector((-0.25, 0, 0.02)), eb, 32)
        else:
            mid = (eo + eb) / 2
            place(mid + Vector((1.3, 0.0, 0.1)), mid, 22)
    elif sid == 'judge':
        hero_pose(t, 'scroll', 3.0)
        screen(f'r2screens/meter/{min(39, t // 2):02d}')
        everyone(g, judge=ease(t / 10))
        e = K.eyes(hero)
        move(k, ((-2.2, 0.1, 1.35), e + Vector((0, 0, -0.2))), ((-1.9, 0.05, 1.3), e + Vector((0, 0, -0.2))), (20, 22))
    elif sid == 'frantic':
        hero_pose(t, 'scroll', 4.0)
        everyone(g, judge=1.0)
        q = min(39, 10 + t)
        screen(f'r2screens/meter/{q:02d}')
        e, p = K.eyes(hero), wpos(phone)
        mid = e.lerp(p, 0.5)
        move(k, (mid + Vector((0.35, -0.6, 0.05)), mid), (mid + Vector((0.28, -0.48, 0.05)), mid), (26, 30))
        for j in range(0, t + 1, 3):
            age = t - j
            if age < 10:
                pops.append(('-$0.01', proj(p + phone_up() * 0.1 + Vector(((j % 7 - 3) * 0.02, 0, 0))), age, 'red'))
        meta['kaching'] = t % 3 == 0
        meta['shake'] = 0.25
    elif sid == 'declined':
        hero_pose(t, 'phone')
        everyone(g, judge=1.0)
        screen('r2screens/declined')
        insert(k, 0.7, 0.6)
        meta['buzz'] = t == 0
    elif sid == 'freeze':
        hero_pose(0, 'phone')
        everyone(g, judge=1.0)
        screen('r2screens/declined')
        pl.color = (1.0, 0.3, 0.3)
        e = K.eyes(hero)
        move(k, (e + Vector((-0.32, -0.42, 0.0)), e), (e + Vector((-0.26, -0.34, 0.0)), e), (34, 40))
    elif sid == 'pull_out':
        hero_pose(0, 'phone_down')
        phone.hide_render = plo.hide_render = True
        e = K.eyes(hero)
        move(k, (e + Vector((0.1, -0.7, -0.05)), e), ((0.3, -1.1, 1.45), e + Vector((0, 0, -0.25))), (30, 18))
    elif sid == 'shield':
        hero_pose(t, 'phone')
        screen(f'screens/shield_{min(12, t):02d}')
        pl.color, pl.energy = (0.6, 0.4, 1.0), 2.5
        insert(k, 0.72, 0.6)
        meta['whoosh'] = t == 0
    elif sid == 'purple_face':
        hero_pose(t, 'phone')
        screen('screens/shield_12')
        pl.color, pl.energy = (0.6, 0.4, 1.0), 3.0
        e = K.eyes(hero)
        move(k, (e + Vector((-0.1, -0.5, -0.05)), e), (e + Vector((-0.08, -0.4, -0.05)), e), (32, 36))
    elif sid == 'hero_read':
        hero_pose(t, 'read')
        phone.hide_render = plo.hide_render = True
        hbook.hide_render = False
        P.between_hands(hbook, hero, K.eyes(hero))
        e = K.eyes(hero)
        move(k, (e + Vector((0.3, -0.75, -0.05)), e + Vector((0, 0, -0.1))), (e + Vector((0.25, -0.62, -0.05)), e + Vector((0, 0, -0.1))), (28, 30))
        for j in range(4, n, 9):
            age = t - j
            if 0 <= age < 14:
                pops.append(('+1', proj(e + Vector(((j % 5 - 2) * 0.04, 0, 0.18))), age, 'gold'))
            meta['coin'] = meta.get('coin') or age == 0
    elif sid == 'tilt':
        tilt = ease(k / 0.45) * (1 - ease((k - 0.7) / 0.25))
        hero_pose(t, 'phone')
        r = hero['rig']
        K.point(r, 'lowerarm01.L', (-0.45, -1.0, 0.75 - tilt * 1.2))
        done = k > 0.55
        screen('screens/unlock_done' if done else 'screens/unlock_tilt')
        pl.color = (0.6, 0.4, 1.0)
        insert(k, 0.72, 0.62)
        meta['chime'] = t == int(0.55 * (n - 1)) + 1
    elif sid == 'endcard':
        hero_pose(0, 'phone_down')
        phone.hide_render = plo.hide_render = True
        place((4.5, 0.05, 1.5), (-1.0, 0.0, 1.0), 16)
        meta['endcard'] = True
    if pops:
        meta['pops'] = pops
    return meta


def main():
    meta = {}
    g = 0
    for sh in T['shots']:
        i, n = sh['i'], sh['frames']
        for t in range(n):
            g += 1
            if ONLY and i not in ONLY:
                continue
            if MID and t != n // 2:
                continue
            if sh['id'] == 'endcard' and t > 0 and not MID:
                continue
            if not MID and (g - 1) % STEP:
                continue
            G[0] = g
            s.frame_set(g)
            m = shot(i, t, n, g) or {}
            m['shot'] = i
            meta[g] = m
            if DRY:
                continue
            s.render.filepath = os.path.join(FR, f'{g:04d}.png')
            bpy.ops.render.render(write_still=True)
            print(f'shot {i:02d} {sh["id"]} frame {g}', flush=True)
    if MID:
        return
    old = {}
    mp = os.path.join(REEL, 'meta.json')
    if os.path.exists(mp) and ONLY:
        old = {int(k): v for k, v in json.load(open(mp))['frames'].items()}
    old.update(meta)
    json.dump({'total': T['total_frames'], 'frames': old}, open(mp, 'w'))
    print('TOTAL', T['total_frames'], flush=True)


main()
