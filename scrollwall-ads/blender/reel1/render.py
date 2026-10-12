"""Reel 1 renderer (Blender/Cycles, PS1 look).

Draft:  python render.py                       (RES=180 SPP=10 STEP=2)
Final:  RES=270 SPP=40 STEP=1 python render.py
Only some shots: ONLY=3,7 ; one frame per shot: MID=1
Reads /home/user/reel1/timings.json, writes frames + meta.json there.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in ('../room2', '../mh', '../ps1v2'):
    sys.path.insert(0, os.path.join(HERE, p))
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Quaternion, Vector

REEL = os.environ.get('REEL', '/home/user/reel1')
T = json.load(open(os.path.join(REEL, 'timings.json')))
FR = os.path.join(REEL, os.environ.get('FRAMES', 'frames'))
os.makedirs(FR, exist_ok=True)
RES = int(os.environ.get('RES', 180))
SPP = int(os.environ.get('SPP', 10))
STEP = int(os.environ.get('STEP', 2))
ONLY = {int(x) for x in os.environ.get('ONLY', '').split(',') if x}
MID = os.environ.get('MID') == '1'
SCREENS = os.path.join(HERE, '..', 'assets', 'ps1')

bpy.ops.wm.open_mainfile(filepath='/home/user/mh/scroller_lp.blend')
import room2  # noqa: E402
from ps1fy import ps1fy  # noqa: E402
from style import apply_style  # noqa: E402

s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = SPP
s.cycles.use_denoising = True
s.cycles.max_bounces = 4
s.cycles.volume_bounces = 0
s.cycles.volume_step_rate = 6.0
s.cycles.filter_width = 0.01
s.render.resolution_x, s.render.resolution_y = RES, RES * 16 // 9
s.render.resolution_percentage = 100
s.render.use_persistent_data = True
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'AgX - Punchy'
s.view_settings.exposure = 0.4
if s.world is None:
    s.world = bpy.data.worlds.new('w')
s.world.use_nodes = True
s.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.65, 0.9, 1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.05

body = bpy.data.objects['Human.proxy741']
ps1fy([body], decimate=1.0, tex_px=224)
ps1fy([o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Human') and o is not body], decimate=1.0, tex_px=64)
for sl in body.material_slots:
    for n in sl.material.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            n.inputs['Roughness'].default_value = 0.9
rig = bpy.data.objects['Human.rig']
S = room2.build()
sun = room2.lights(14.0, float(os.environ.get('HAZE', 0.03)))
lamp = bpy.data.objects['lamp_desk']

# ------------------------------------------------------------------ props
_imgs = {}


def img(rel):
    if rel not in _imgs:
        _imgs[rel] = bpy.data.images.load(os.path.join(SCREENS, rel + '.png'))
    return _imgs[rel]


def make_phone(name):
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.075
        v.co.y *= 0.009
        v.co.z *= 0.155
    bm.normal_update()
    for f in bm.faces:
        if f.normal.y < -0.5:
            f.material_index = 1
        for l in f.loops:
            c = l.vert.co
            l[uvl].uv = (c.x / 0.075 + 0.5, c.z / 0.155 + 0.5)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    s.collection.objects.link(ob)
    body_m = bpy.data.materials.new(name + '_body')
    body_m.use_nodes = True
    b = body_m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.02, 0.02, 0.025, 1)
    b.inputs['Roughness'].default_value = 0.3
    scr = bpy.data.materials.new(name + '_screen')
    scr.use_nodes = True
    nt = scr.node_tree
    nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    t = nt.nodes.new('ShaderNodeTexImage')
    t.interpolation = 'Closest'
    t.image = img('feed/0001')
    e.inputs['Strength'].default_value = 3.0
    nt.links.new(t.outputs['Color'], e.inputs['Color'])
    nt.links.new(e.outputs['Emission'], o.inputs['Surface'])
    ob.data.materials.append(body_m)
    ob.data.materials.append(scr)
    return ob, t


phone, phone_tex = make_phone('phone')
phone.parent = rig
phone.parent_type = 'BONE'
phone.parent_bone = 'wrist.L'
phone.location = (0.0, float(os.environ.get('PH_Y', 0.13)), float(os.environ.get('PH_Z', 0.0)))
phone.rotation_euler = (math.radians(float(os.environ.get('PH_RX', -70))), 0, math.radians(float(os.environ.get('PH_RZ', 0))))
pl = bpy.data.lights.new('phone_light', 'POINT')
pl.energy, pl.color, pl.shadow_soft_size = 2.0, (0.7, 0.82, 1.0), 0.04
plo = bpy.data.objects.new('phone_light', pl)
s.collection.objects.link(plo)
plo.parent = phone
plo.location = (0, -0.12, 0.05)
# the second phone lies face-up on the desk during the focus session
desk_phone, desk_tex = make_phone('desk_phone')
desk_phone.rotation_euler = (math.radians(90), 0, math.radians(90))
desk_phone.location = (1.5, 0.95, 0.765)
coins = []
coin_m = bpy.data.materials.new('coin')
coin_m.use_nodes = True
cb = coin_m.node_tree.nodes['Principled BSDF']
cb.inputs['Base Color'].default_value = (1.0, 0.62, 0.15, 1)
cb.inputs['Metallic'].default_value = 1.0
cb.inputs['Roughness'].default_value = 0.3
for i in range(12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.022, depth=0.005)
    c = bpy.context.active_object
    c.data.materials.append(coin_m)
    c.location = (0, 0, -5)
    coins.append(c)

clock_root = S['clock']
hands = {n: o for o in bpy.data.objects if o.name.startswith('wall_clock_') for n in [o.name] if 'hand' in o.name}
_hand_q0 = {}


def set_clock(hour):
    bpy.context.view_layer.update()
    for name, h in hands.items():
        if name not in _hand_q0:
            h.rotation_mode = 'QUATERNION'
            _hand_q0[name] = h.rotation_quaternion.copy()
        axis = (h.parent.matrix_world.inverted().to_3x3() @ Vector((0, 1, 0))).normalized() if h.parent else Vector((0, 1, 0))
        if 'hours' in name:
            ang = (hour % 12) / 12 * 2 * math.pi
        elif 'minute' in name:
            ang = (hour % 1) * 2 * math.pi
        else:
            ang = (hour * 60 % 1) * 2 * math.pi
        h.rotation_quaternion = Quaternion(axis, ang) @ _hand_q0[name]


def set_time(hour):
    """Sun through the window: high and gold at 15:00, low and orange at 19:00."""
    k = max(0.0, min(1.0, (hour - 15) / 4))
    d = Vector((1.0, 0.18 + 0.2 * k, -0.62 + 0.38 * k)).normalized()
    sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sun.data.color = tuple(Vector((1.0, 0.8, 0.58)).lerp(Vector((1.0, 0.5, 0.25)), k))
    sun.data.energy = 14.0 - 6.0 * k
    lamp.data.energy = 25 + 40 * k
    set_clock(hour)


# ------------------------------------------------------------------ posing
def point_bone(name, direction):
    pb = rig.pose.bones[name]
    bpy.context.view_layer.update()
    head = pb.head.copy()
    cur = (pb.tail - pb.head).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    pb.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ pb.matrix


def reset_pose():
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    apply_style(rig)
    bpy.context.view_layer.update()


def ground_lowest(z):
    bpy.context.view_layer.update()
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    zmin = min((ev.matrix_world @ v.co).z for v in ev.data.vertices)
    rig.location.z += z - zmin
    bpy.context.view_layer.update()


def ground_hips(z):
    bpy.context.view_layer.update()
    hz = (rig.matrix_world @ rig.pose.bones['pelvis.L'].head).z
    rig.location.z += z - hz
    bpy.context.view_layer.update()


def pose_bed(t, scroll=1.0, look=0.55, free_arm_down=False):
    """Sitting up against the headboard, legs out, phone up, thumbing the feed."""
    reset_pose()
    rig.location = (-0.85, 1.12, 0.0)
    rig.rotation_euler = (0, 0, 0)
    for side, sg in (('L', 1), ('R', -1)):
        point_bone(f'upperleg01.{side}', (sg * 0.06, -1.0, 0.0))
        point_bone(f'lowerleg01.{side}', (sg * 0.04, -1.0, -0.08))
    for nm in ('spine05', 'spine04', 'spine03', 'spine02', 'spine01'):
        point_bone(nm, (0, 0.28, 1.0))
    point_bone('neck01', (0, -0.1, 1.0))
    nod = math.sin(t * 0.21) * 0.04
    point_bone('head', (0, -look - nod, 1.0))
    point_bone('upperarm01.L', (0.22, -0.45, -1.0))
    point_bone('lowerarm01.L', (-0.45, -1.0, 0.75))
    flick = max(0.0, math.sin(t * 0.9)) * 0.25 * scroll  # thumb-scroll pulses
    if free_arm_down:
        point_bone('upperarm01.R', (-0.3, 0.05, -1.0))
        point_bone('lowerarm01.R', (-0.1, -0.6, -1.0))
    else:
        point_bone('upperarm01.R', (-0.22, -0.45, -1.0))
        point_bone('lowerarm01.R', (0.4, -1.0, 0.7 + flick))
    ground_lowest(0.57)


def pose_desk(t, holding=False, tilt=0.0):
    """Seated at the desk (facing +X), short legs dangling; studying or holding the phone."""
    reset_pose()
    rig.location = (0.95, 0.45, 0.0)
    rig.rotation_euler = (0, 0, math.pi / 2)
    for side, sg in (('L', 1), ('R', -1)):
        point_bone(f'upperleg01.{side}', (sg * 0.1, -1.0, 0.05))
        point_bone(f'lowerleg01.{side}', (sg * 0.05, -0.25, -1.0))
    for nm in ('spine05', 'spine04', 'spine03', 'spine02', 'spine01'):
        point_bone(nm, (0, -0.12, 1.0))
    point_bone('neck01', (0, -0.3, 1.0))
    if holding:
        point_bone('head', (0, -0.7, 1.0))
        point_bone('upperarm01.L', (0.22, -0.45, -1.0))
        point_bone('lowerarm01.L', (-0.45, -1.0, 0.75 - tilt * 1.2))
        point_bone('upperarm01.R', (-0.22, -0.45, -1.0))
        point_bone('lowerarm01.R', (0.4, -1.0, 0.5))
    else:
        bob = math.sin(t * 0.12) * 0.05
        point_bone('head', (0, -0.95 - bob, 1.0))
        point_bone('upperarm01.L', (0.3, -0.55, -1.0))
        point_bone('lowerarm01.L', (-0.15, -1.0, 0.12))
        write = math.sin(t * 0.5) * 0.08
        point_bone('upperarm01.R', (-0.3, -0.55, -1.0))
        point_bone('lowerarm01.R', (0.15 + write, -1.0, 0.1))
    ground_hips(0.6)


def show_phone(on):
    phone.hide_render = not on
    plo.hide_render = not on


def hide_coins():
    for c in coins:
        c.location = (0, 0, -5)


# ------------------------------------------------------------------ camera
cd = bpy.data.cameras.new('cam')
cd.sensor_fit = 'VERTICAL'
cd.clip_start = 0.01
cam = bpy.data.objects.new('cam', cd)
s.collection.objects.link(cam)
s.camera = cam


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def place(loc, target, lens=24, roll=0.0):
    loc, target = Vector(loc), Vector(target)
    cam.location = loc
    q = (target - loc).normalized().to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), roll)
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = q
    cd.lens = lens


def place_up(loc, target, up, lens=30):
    """Like place(), but the frame's 'up' follows a given world vector (e.g. the phone's top)."""
    loc, target, up = Vector(loc), Vector(target), Vector(up).normalized()
    fwd = (target - loc).normalized()
    right = fwd.cross(up).normalized()
    up2 = right.cross(fwd).normalized()
    m = Matrix((right, up2, -fwd)).transposed()
    cam.rotation_mode = 'QUATERNION'
    cam.location = loc
    cam.rotation_quaternion = m.to_quaternion()
    cd.lens = lens


def phone_up(ob):
    bpy.context.view_layer.update()
    return (ob.matrix_world.to_quaternion() @ Vector((0, 0, 1))).normalized()


def move(k, a, b, lens=(24, 24), roll=(0, 0)):
    """Slow, steady move between two (loc, target) keys."""
    e = ease(k)
    place(Vector(a[0]).lerp(Vector(b[0]), e), Vector(a[1]).lerp(Vector(b[1]), e), lens[0] + (lens[1] - lens[0]) * e,
          roll[0] + (roll[1] - roll[0]) * e)


def wpos(bone=None, obj=None):
    bpy.context.view_layer.update()
    if bone:
        return rig.matrix_world @ rig.pose.bones[bone].head
    return obj.matrix_world.translation.copy()


def screen_normal(ob):
    bpy.context.view_layer.update()
    return (ob.matrix_world.to_quaternion() @ Vector((0, -1, 0))).normalized()


eyes_obj = bpy.data.objects.get('Human.low-poly')


def eyes():
    bpy.context.view_layer.update()
    ev = eyes_obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    return sum(pts, Vector()) / len(pts)


def face_box():
    """Head position in normalised screen space (for the CCTV face box)."""
    bpy.context.view_layer.update()
    h = rig.matrix_world @ rig.pose.bones['head'].head
    top = rig.matrix_world @ rig.pose.bones['head'].tail
    c = world_to_camera_view(s, cam, (h + top) / 2)
    a = world_to_camera_view(s, cam, h)
    b = world_to_camera_view(s, cam, top)
    size = max(0.06, abs(b.y - a.y) * 1.6)
    return [c.x, 1 - c.y, size]


FEED = [f'feed/{i:04d}' for i in range(1, 129)]


def feed(frame, speed=1.0):
    phone_tex.image = img(FEED[int(frame * speed) % len(FEED)])


# ------------------------------------------------------------------ shots
def shot(i, t, n):
    """t = local frame, n = shot length in frames. Returns meta for post."""
    k = t / max(1, n - 1)
    sid = T['shots'][i]['id']
    meta = {}
    hide_coins()
    desk_phone.hide_render = True
    show_phone(True)
    if sid == 'wide':
        set_time(15.0)
        pose_bed(t)
        feed(t)
        move(k, ((1.35, -1.55, 1.75), (-0.6, 0.9, 0.85)), ((1.18, -1.32, 1.68), (-0.6, 0.9, 0.85)), (16, 17))
    elif sid == 'phone_pov':
        set_time(15.1)
        pose_bed(t + 40)
        feed(t + 40)
        e, p = eyes(), wpos(obj=phone)
        d = (p - e).normalized()
        place_up(e + d * (0.04 + 0.05 * ease(k)) + Vector((0.02, 0, 0.03)), p, phone_up(phone), 28)
    elif sid == 'ots':
        set_time(15.2)
        pose_bed(t + 80)
        feed(t + 80)
        h, p = wpos('head'), wpos(obj=phone)
        move(k, (h + Vector((0.38, 0.32, 0.26)), p), (h + Vector((0.26, 0.22, 0.17)), p), (22, 24))
    elif sid == 'clock':
        set_time(15.3 + k * 2.6)  # time-lapse
        pose_bed(t)
        feed(t)
        c = wpos(obj=clock_root) + Vector((0, 0, 0.0))
        move(k, (c + Vector((0.14, -0.95, -0.08)), c), (c + Vector((0.1, -0.75, -0.06)), c), (32, 35))
    elif sid == 'face':
        set_time(17.9)
        pose_bed(t)
        feed(t, 1.5)
        f = eyes() + Vector((0, 0, -0.03))
        move(k, (f + Vector((0.36, -0.42, 0.02)), f), (f + Vector((0.3, -0.34, 0.01)), f), (34, 36))
    elif sid == 'overhead':
        set_time(16.0 + k * 2.5)
        pose_bed(t)
        feed(t, 1.5)
        cc = Vector((-0.85, 0.75, 0.6))
        place(cc + Vector((0, 0, 1.85)), cc, 15, roll=math.radians(10 + 25 * ease(k)))
        cam.location.z = 2.45
    elif sid in ('ignore', 'wall'):
        set_time(18.4)
        pose_bed(t, scroll=0.0, free_arm_down=True)
        p, nrm = wpos(obj=phone), screen_normal(phone)
        if sid == 'ignore':
            phone_tex.image = img('screens/limit_tap' if k > 0.55 else 'screens/limit')
            if k > 0.8:
                feed(t)
            meta['tap'] = abs(k - 0.55) < 1.0 / n
        else:
            phone_tex.image = img(f'screens/shield_{min(12, int(t / 2)):02d}')
            meta['slam'] = t == 16
            if 16 <= t < 24:
                meta['shake'] = 1 - (t - 16) / 8
        e = eyes()
        place_up(p + (e - p) * (0.8 - 0.1 * ease(k)), p, phone_up(phone), 32)
    elif sid == 'frontcam':
        set_time(18.5)
        pose_bed(t, scroll=0.0, free_arm_down=True)
        feed(t)
        p, nrm, h = wpos(obj=phone), screen_normal(phone), wpos('head')
        place(p + nrm * 0.07, eyes(), 18)
        meta['cctv'] = {'cam': 'FRONT CAM', 'box': face_box(), 'clock': 18.5 * 3600 + t / 30}
    elif sid == 'face2':
        set_time(18.6)
        pose_bed(t, scroll=0.0, look=0.3)
        phone_tex.image = img('screens/shield_12')
        f = eyes() + Vector((0, 0, -0.03))
        move(k, (f + Vector((-0.1, -0.6, -0.1)), f), (f + Vector((-0.07, -0.42, -0.07)), f), (36, 40))
    elif sid == 'desk':
        set_time(18.7)
        pose_desk(t)
        show_phone(False)
        desk_phone.hide_render = False
        desk_tex.image = img('screens/balance_00')
        move(k, ((-0.15, -0.95, 1.45), (1.25, 0.45, 0.85)), ((0.1, -0.72, 1.38), (1.25, 0.45, 0.85)), (20, 22))
    elif sid == 'desk_top':
        set_time(18.8 + k * 0.6)
        pose_desk(t)
        show_phone(False)
        desk_phone.hide_render = False
        bal = min(50, int(k * 11) * 5)
        desk_tex.image = img(f'screens/balance_{bal:02d}')
        for ci, c in enumerate(coins):
            tt = (t - ci * (n / 14)) / 10
            if tt < 0:
                continue
            tt = min(1.0, tt)
            c.location = (1.12 + (ci % 4) * 0.05, 0.45 + (ci // 4) * 0.06, 1.3 - 0.52 * tt * tt)
            c.rotation_euler = ((1 - tt) * 9 + ci, 0, ci)
            meta['coin'] = meta.get('coin', False) or abs(tt - 1.0) < 1e-6 and (t - ci * (n / 14)) == 10
        cc = Vector((1.25, 0.5, 0.76))
        place(cc + Vector((0, 0, 1.6)), cc, 18, roll=math.radians(90 + 20 * ease(k)))
    elif sid == 'balance':
        set_time(19.3)
        pose_desk(t)
        show_phone(False)
        desk_phone.hide_render = False
        desk_tex.image = img('screens/balance_50')
        p = wpos(obj=desk_phone)
        move(k, (p + Vector((0.0, -0.01, 0.42)), p), (p + Vector((0.0, -0.01, 0.34)), p), (34, 36), roll=(math.pi / 2, math.pi / 2))
        meta['ding'] = t == 3
    elif sid == 'pay_pov':
        set_time(19.4)
        pose_desk(t, holding=True)
        phone_tex.image = img('screens/unlock_offer' if k < 0.7 else 'screens/unlock_tilt')
        e, p = eyes(), wpos(obj=phone)
        d = (p - e).normalized()
        place_up(e + d * (0.04 + 0.05 * ease(k)) + Vector((0.0, 0, 0.03)), p, phone_up(phone), 28)
    elif sid == 'tilt':
        set_time(19.5)
        tilt = ease((k - 0.15) / 0.45) * (1 - ease((k - 0.75) / 0.2))
        pose_desk(t, holding=True, tilt=tilt)
        phone_tex.image = img('screens/unlock_done' if k > 0.6 else 'screens/unlock_tilt')
        p, nrm, h = wpos(obj=phone), screen_normal(phone), wpos('head')
        place(p + nrm * 0.07, p + nrm * 1.0, 18)
        meta['cctv'] = {'cam': 'FRONT CAM', 'box': face_box(), 'clock': 19.5 * 3600 + t / 30,
                        'tag': 'PAID 40 COINS' if k > 0.6 else 'TILT TO SPEND'}
        meta['chime'] = abs(k - 0.6) < 1.0 / n
    elif sid == 'end':
        set_time(19.0)
        pose_bed(t, scroll=0.5, look=0.45)
        feed(t, 0.6)
        move(k, ((0.95, -1.05, 1.5), (-0.65, 0.95, 0.85)), ((1.38, -1.58, 1.78), (-0.6, 0.9, 0.85)), (18, 16))
        meta['timer'] = 300 - int(t / 30) - 1
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
            if MID:
                if t != n // 2:
                    continue
            elif (g - 1) % STEP:
                continue
            s.frame_set(g)
            m = shot(i, t, n) or {}
            m['shot'] = i
            meta[g] = m
            s.render.filepath = os.path.join(FR, f'{g:04d}.png')
            bpy.ops.render.render(write_still=True)
            print(f'shot {i:02d} {sh["id"]} frame {g}', flush=True)
    old = {}
    mp = os.path.join(REEL, 'meta.json')
    if os.path.exists(mp) and ONLY:
        old = {int(k): v for k, v in json.load(open(mp))['frames'].items()}
    old.update(meta)
    json.dump({'total': T['total_frames'], 'frames': old}, open(mp, 'w'))
    print('TOTAL', T['total_frames'], flush=True)


main()
