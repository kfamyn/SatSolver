"""Reel 1 v2 renderer: 23 short shots, 30 fps, Scrollwall force field.

Built as _head.py (shared setup) + _tail2.py (wall, shots): cat _head.py _tail2.py > render2.py
Draft:  RES=180 SPP=8 python render2.py        (STEP=1 = every frame, 30 fps)
Only some shots: ONLY=3,7 ; one frame per shot: MID=1
Reads /home/user/reel2/timings.json (script2.py), writes frames + meta.json there.
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

REEL = os.environ.get('REEL', '/home/user/reel2')
T = json.load(open(os.path.join(REEL, 'timings.json')))
FR = os.path.join(REEL, os.environ.get('FRAMES', 'frames'))
os.makedirs(FR, exist_ok=True)
RES = int(os.environ.get('RES', 180))
SPP = int(os.environ.get('SPP', 10))
STEP = int(os.environ.get('STEP', 1))
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
desk_phone.rotation_euler = (math.radians(-90), 0, math.radians(90))
desk_phone.location = (1.42, 0.86, 0.78)
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




# ------------------------------------------------------------------ v2 extras
# overscroll bounce: the phone screen texture can slide (CLIP leaves a dark gap)
_snt = phone_tex.id_data
_tc = _snt.nodes.new('ShaderNodeTexCoord')
_map = _snt.nodes.new('ShaderNodeMapping')
_snt.links.new(_tc.outputs['UV'], _map.inputs['Vector'])
_snt.links.new(_map.outputs['Vector'], phone_tex.inputs['Vector'])
phone_tex.extension = 'CLIP'


def screen_offset(v):
    _map.inputs['Location'].default_value[1] = v


# the Scrollwall: a translucent violet force field that rises at the foot of the bed
WALL_W, WALL_H, WALL_Y, WALL_X = 1.75, 2.1, -0.6, -0.85
wme = bpy.data.meshes.new('scrollwall')
wme.from_pydata([(-WALL_W / 2, 0, 0), (WALL_W / 2, 0, 0), (WALL_W / 2, 0, WALL_H), (-WALL_W / 2, 0, WALL_H)], [], [(0, 1, 2, 3)])
wme.uv_layers.new(name='UVMap')
for li, uv in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
    wme.uv_layers['UVMap'].data[li].uv = uv
wall = bpy.data.objects.new('scrollwall', wme)
s.collection.objects.link(wall)
wall.location = (WALL_X, WALL_Y, -3.0)
wall.visible_shadow = False
wm = bpy.data.materials.new('scrollwall')
wm.use_nodes = True
nt = wm.node_tree
nt.nodes.clear()
_o = nt.nodes.new('ShaderNodeOutputMaterial')
_mix = nt.nodes.new('ShaderNodeMixShader')
_tr = nt.nodes.new('ShaderNodeBsdfTransparent')
_em = nt.nodes.new('ShaderNodeEmission')
_em.inputs['Strength'].default_value = 2.2
_wt = nt.nodes.new('ShaderNodeTexImage')
_wt.image = img('screens/forcefield')
_wt.interpolation = 'Closest'
_noise = nt.nodes.new('ShaderNodeTexNoise')
_noise.inputs['Scale'].default_value = 7.0
_gt = nt.nodes.new('ShaderNodeMath')
_gt.operation = 'GREATER_THAN'  # noise > dissolve threshold keeps the pixel
_m1 = nt.nodes.new('ShaderNodeMath')
_m1.operation = 'MULTIPLY'
_m2 = nt.nodes.new('ShaderNodeMath')
_m2.operation = 'MULTIPLY'
nt.links.new(_wt.outputs['Color'], _em.inputs['Color'])
nt.links.new(_noise.outputs['Fac'], _gt.inputs[0])
nt.links.new(_wt.outputs['Alpha'], _m1.inputs[0])
nt.links.new(_gt.outputs[0], _m1.inputs[1])
nt.links.new(_m1.outputs[0], _m2.inputs[0])
nt.links.new(_m2.outputs[0], _mix.inputs['Fac'])
nt.links.new(_tr.outputs[0], _mix.inputs[1])
nt.links.new(_em.outputs[0], _mix.inputs[2])
nt.links.new(_mix.outputs[0], _o.inputs['Surface'])
# readable from both sides: mirror u on back faces
_uv = nt.nodes.new('ShaderNodeTexCoord')
_geo = nt.nodes.new('ShaderNodeNewGeometry')
_sep = nt.nodes.new('ShaderNodeSeparateXYZ')
_comb = nt.nodes.new('ShaderNodeCombineXYZ')
_fu = nt.nodes.new('ShaderNodeMath')
_fu.operation = 'MULTIPLY_ADD'  # u * (1 - 2b) + b
_fb = nt.nodes.new('ShaderNodeMath')
_fb.operation = 'MULTIPLY_ADD'
_fb.inputs[1].default_value = -2.0
_fb.inputs[2].default_value = 1.0
nt.links.new(_uv.outputs['UV'], _sep.inputs[0])
nt.links.new(_geo.outputs['Backfacing'], _fb.inputs[0])
nt.links.new(_sep.outputs[0], _fu.inputs[0])
nt.links.new(_fb.outputs[0], _fu.inputs[1])
nt.links.new(_geo.outputs['Backfacing'], _fu.inputs[2])
nt.links.new(_fu.outputs[0], _comb.inputs[0])
nt.links.new(_sep.outputs[1], _comb.inputs[1])
nt.links.new(_comb.outputs[0], _wt.inputs['Vector'])
wme.materials.append(wm)
wl = bpy.data.lights.new('wall_light', 'AREA')
wl.color, wl.size, wl.size_y = (0.6, 0.4, 1.0), WALL_W, WALL_H
wl.shape = 'RECTANGLE'
wlo = bpy.data.objects.new('wall_light', wl)
s.collection.objects.link(wlo)
wlo.parent = wall
wlo.location = (0, 0.05, WALL_H / 2)
wlo.rotation_euler = (math.radians(90), 0, 0)  # faces +Y, toward the bed


def set_wall(h=1.0, fade=1.0, dissolve=0.0):
    """h: 0 = sunk below the floor, 1 = fully up (may overshoot). dissolve 0..1 eats it in patches."""
    wall.location.z = -WALL_H * 1.05 * (1 - h)
    on = h > 0.02 and fade > 0.01 and dissolve < 0.99
    wall.hide_render = not on
    wlo.hide_render = not on
    _gt.inputs[1].default_value = -0.05 + 1.1 * dissolve
    _m2.inputs[1].default_value = fade
    wl.energy = 70 * fade * (1 - dissolve) * min(1.0, max(0.0, h))


def rise(x):
    """0->1 with a springy overshoot (back-out ease)."""
    x = max(0.0, min(1.0, x))
    c = 2.2
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def spring(x):
    """overscroll: snaps out, wobbles back to 0."""
    if x <= 0:
        return 0.0
    return math.exp(-x * 5) * math.sin(x * 14) * 1.0


WALL_C = Vector((WALL_X, WALL_Y, 1.05))
_reset_pose0 = reset_pose
FING = os.environ.get('FING', '2345')
THUMB = False


def reset_pose():
    """also tuck the phone hand's fingers so they don't cover the screen in inserts."""
    _reset_pose0()
    for f in FING:
        sc = 0.35
        rig.pose.bones[f'finger{f}-1.L'].scale = (sc, sc, sc)
    if not THUMB:  # thumb off the screen unless it's tapping
        rig.pose.bones['metacarpal1.L'].scale = (0.3, 0.3, 0.3)
    bpy.context.view_layer.update()


def recoil(r):
    """head and torso jerk back from the wall (after pose_bed)."""
    if r <= 0:
        return
    for nm in ('spine02', 'spine01'):
        point_bone(nm, (0, 0.28 + 0.35 * r, 1.0))
    point_bone('head', (0, 0.25 * r, 1.0))


def front_face(t, k, dist=(0.42, 0.34), lens=(34, 38), side=0.36):
    f = eyes() + Vector((0, 0, -0.03))
    a = Vector((side, -1.0, 0.05)).normalized()
    move(k, (f + a * dist[0], f), (f + a * dist[1], f), lens)


def insert(k, a=0.8, b=0.72, lens=32):
    p, e = wpos(obj=phone), eyes()
    place_up(p + (e - p) * (a + (b - a) * ease(k)), p, phone_up(phone), lens)


# ------------------------------------------------------------------ shots
def shot(i, t, n):
    k = t / max(1, n - 1)
    sid = T['shots'][i]['id']
    meta = {}
    hide_coins()
    desk_phone.hide_render = True
    show_phone(True)
    screen_offset(0.0)
    set_wall(0.0)
    if sid == 'wide':
        set_time(15.0)
        pose_bed(t * 1.6, scroll=2.0)
        feed(t, 2)
        move(k, ((1.35, -1.55, 1.75), (-0.6, 0.9, 0.85)), ((1.05, -1.2, 1.6), (-0.65, 0.9, 0.85)), (16, 19))
    elif sid == 'swipe_pov':
        set_time(15.1)
        pose_bed(t * 1.6 + 40, scroll=2.0)
        feed(t + 40, 3)
        e, p = eyes(), wpos(obj=phone)
        d = (p - e).normalized()
        place_up(e + d * (0.04 + 0.08 * ease(k)) + Vector((0.02, 0, 0.03)), p, phone_up(phone), 28)
    elif sid == 'clock':
        set_time(15.3 + k * 3.0)
        pose_bed(t)
        c = wpos(obj=clock_root)
        move(k, (c + Vector((0.14, -0.95, -0.08)), c), (c + Vector((0.08, -0.6, -0.05)), c), (32, 38))
        meta['tick'] = True
    elif sid == 'overhead':
        set_time(16.5 + k * 2.0)
        pose_bed(t * 1.6, scroll=2.0)
        feed(t, 2)
        cc = Vector((-0.85, 0.75, 0.6))
        place(cc + Vector((0, 0, 1.85)), cc, 15 + 3 * ease(k), roll=math.radians(10 + 45 * ease(k)))
        cam.location.z = 2.45
    elif sid == 'limit':
        set_time(18.4)
        pose_bed(t, scroll=0.0, free_arm_down=True)
        phone_tex.image = img('screens/limit')
        insert(k, 0.85, 0.7)
    elif sid == 'face_blank':
        set_time(18.4)
        pose_bed(t, scroll=0.0, free_arm_down=True, look=0.6)
        phone_tex.image = img('screens/limit')
        front_face(t, k)
    elif sid == 'ignore_tap':
        set_time(18.4)
        pose_bed(t, scroll=0.0, free_arm_down=True)
        if k < 0.4:
            phone_tex.image = img('screens/limit')
        elif k < 0.6:
            phone_tex.image = img('screens/limit_tap')
        else:
            feed(t, 3)
        meta['tap'] = t == int(0.4 * (n - 1)) + 1
        insert(k, 0.75, 0.68)
    elif sid == 'swipe_bounce':
        set_time(18.5)
        x = (t - 9) / 30
        pose_bed(t * 1.6 if t < 9 else 14, scroll=2.5 if t < 9 else 0.0)
        if t < 9:
            feed(t, 3)
        else:
            feed(9, 3)
            screen_offset(-0.35 * spring(x))
        meta['thud'] = t == 9
        insert(k, 0.72, 0.62)
        if 9 <= t < 13:
            meta['shake'] = 0.5 * (1 - (t - 9) / 4)
    elif sid == 'wall_rise':
        set_time(18.6)
        pose_bed(t, scroll=0.0)
        feed(9, 3)
        set_wall(rise(t / 10))
        meta['wall_hit'] = t == 6
        if 6 <= t < 14:
            meta['shake'] = 1 - (t - 6) / 8
            meta['flash'] = max(0.0, 0.6 - (t - 6) * 0.2)
        move(k, ((0.75, -1.6, 0.45), (-0.75, 0.0, 1.05)), ((0.7, -1.5, 0.5), (-0.78, 0.0, 1.1)), (17, 18), roll=(0.06, 0.02))
    elif sid == 'face_recoil':
        set_time(18.6)
        pose_bed(t, scroll=0.0, look=0.3)
        recoil(ease(t / 4))
        feed(9, 3)
        set_wall(1.0)
        front_face(t, k, (0.36, 0.33), (32, 34), side=0.15)
        if t < 5:
            meta['shake'] = 0.4
    elif sid == 'wall_hero':
        set_time(18.6)
        pose_bed(t, scroll=0.0, look=0.25)
        recoil(1.0)
        phone_tex.image = img('screens/shield_12')
        set_wall(1.0)
        h = wpos('head')
        move(k, (h + Vector((0.3, 0.2, 0.2)), WALL_C), (h + Vector((0.2, 0.1, 0.12)), WALL_C + Vector((0, 0, -0.05))), (20, 24))
    elif sid == 'shield':
        set_time(18.6)
        pose_bed(t, scroll=0.0, free_arm_down=True)
        set_wall(1.0)
        phone_tex.image = img(f'screens/shield_{min(12, t):02d}')
        insert(k, 0.72, 0.6)
    elif sid == 'face_stare':
        set_time(18.6)
        pose_bed(t, scroll=0.0, look=0.65)
        phone_tex.image = img('screens/shield_12')
        set_wall(1.0, 0.85)
        front_face(t, k, (0.4, 0.32), (36, 42), side=-0.25)
    elif sid == 'desk':
        set_time(18.7)
        pose_desk(t * 2)
        show_phone(False)
        set_wall(1.0, 0.7)
        desk_phone.hide_render = False
        desk_tex.image = img('screens/balance_00')
        move(k, ((-0.15, -0.95, 1.45), (1.25, 0.45, 0.85)), ((0.2, -0.6, 1.35), (1.25, 0.45, 0.85)), (20, 24))
    elif sid == 'desk_top':
        set_time(18.8 + k * 0.6)
        pose_desk(t * 3)
        show_phone(False)
        desk_phone.hide_render = False
        desk_tex.image = img(f'screens/balance_{min(20, int(k * 5) * 5):02d}')
        for ci, c in enumerate(coins):
            tt = (t - ci * 1.5) / 6
            if tt < 0:
                continue
            tt = min(1.0, tt)
            c.location = (1.12 + (ci % 4) * 0.05, 0.45 + (ci // 4) * 0.06, 1.3 - 0.52 * tt * tt)
            c.rotation_euler = ((1 - tt) * 9 + ci, 0, ci)
        cc = Vector((1.25, 0.5, 0.76))
        place(cc + Vector((0, 0, 1.6 - 0.3 * ease(k))), cc, 18, roll=math.radians(90 + 30 * ease(k)))
        meta['coins'] = True
    elif sid == 'coins':
        set_time(19.0 + k * 0.2)
        pose_desk(t * 3)
        show_phone(False)
        desk_phone.hide_render = False
        desk_tex.image = img(f'screens/balance_{min(45, 20 + int(k * 6) * 5):02d}')
        p = wpos(obj=desk_phone)
        for ci, c in enumerate(coins):
            tt = (t - ci * 2) / 7
            if tt < 0:
                continue
            tt = min(1.0, tt)
            ang = ci * 2.4
            land = p + Vector((math.cos(ang) * (0.12 + 0.01 * ci), math.sin(ang) * (0.1 + 0.01 * ci), -0.005 + 0.004 * (ci % 3)))
            c.location = land + Vector((0, 0, 0.5 * (1 - tt * tt)))
            c.rotation_euler = ((1 - tt) * 11 + ci, 0, ci)
        a, b = p + Vector((-0.08, -0.4, 0.38)), p + Vector((-0.06, -0.3, 0.28))
        place_up(a.lerp(b, ease(k)), p, phone_up(desk_phone), 26 + 4 * ease(k))
        meta['coins'] = True
    elif sid == 'balance':
        set_time(19.3)
        pose_desk(t)
        show_phone(False)
        desk_phone.hide_render = False
        desk_tex.image = img('screens/balance_50')
        p = wpos(obj=desk_phone)
        move(k, (p + Vector((0.0, -0.01, 0.42)), p), (p + Vector((0.0, -0.01, 0.3)), p), (34, 38), roll=(math.pi / 2, math.pi / 2))
        meta['ding'] = t == 3
    elif sid == 'pay_pov':
        set_time(19.4)
        pose_desk(t, holding=True)
        phone_tex.image = img('screens/unlock_offer' if k < 0.55 else 'screens/unlock_tilt')
        meta['tap'] = t == int(0.55 * (n - 1)) + 1
        e, p = eyes(), wpos(obj=phone)
        d = (p - e).normalized()
        place_up(e + d * (0.04 + 0.08 * ease(k)), p, phone_up(phone), 28)
    elif sid == 'tilt':
        set_time(19.5)
        tilt = ease(k / 0.45) * (1 - ease((k - 0.7) / 0.25))
        pose_desk(t, holding=True, tilt=tilt)
        phone_tex.image = img('screens/unlock_done' if k > 0.55 else 'screens/unlock_tilt')
        p, nrm = wpos(obj=phone), screen_normal(phone)
        place(p + nrm * 0.07, p + nrm * 1.0, 18)
        meta['cctv'] = {'cam': 'FRONT CAM', 'box': face_box(), 'clock': 19.5 * 3600 + t / 30,
                        'tag': 'PAID 40 COINS' if k > 0.55 else 'TILT TO SPEND'}
        meta['chime'] = t == int(0.55 * (n - 1)) + 1
    elif sid == 'unlocked':
        set_time(19.5)
        pose_desk(t, holding=True)
        phone_tex.image = img('screens/unlock_done')
        p, e = wpos(obj=phone), eyes()
        place_up(p + (e - p) * (0.7 - 0.12 * ease(k)), p, phone_up(phone), 32)
    elif sid == 'wall_open':
        set_time(19.6)
        pose_desk(t, holding=True)
        phone_tex.image = img('screens/unlock_done')
        dz = ease((k - 0.12) / 0.6)
        set_wall(1.0, 1.0, dz)
        meta['dissolve'] = t == int(0.12 * (n - 1))
        move(k, ((1.45, 0.05, 1.35), WALL_C), ((1.2, -0.1, 1.3), WALL_C + Vector((0, 0.3, -0.1))), (18, 20))
    elif sid == 'golden':
        set_time(19.0)
        pose_bed(t, scroll=0.5, look=0.45)
        feed(t, 0.6)
        move(k, ((-0.35, -1.2, 1.3), (-0.85, 1.0, 0.85)), ((-0.4, -1.5, 1.35), (-0.85, 1.0, 0.88)), (19, 18))
    elif sid == 'wall_back':
        set_time(19.1)
        pose_bed(t + 33, scroll=0.5 if k < 0.45 else 0.0, look=0.45)
        if k > 0.5:
            recoil(ease((t - 0.5 * n) / 4))
        feed(t + 33, 0.6 if k < 0.45 else 0.0)
        hit = int(0.45 * n)
        set_wall(rise((t - hit + 6) / 10) if t >= hit - 6 else 0.0)
        meta['wall_hit'] = t == hit
        if hit <= t < hit + 8:
            meta['shake'] = 1 - (t - hit) / 8
            meta['flash'] = max(0.0, 0.6 - (t - hit) * 0.2)
        move(k, ((-0.4, -1.5, 1.35), (-0.85, 1.0, 0.88)), ((-0.5, -1.62, 1.2), (-0.85, 0.2, 0.85)), (18, 15))
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
