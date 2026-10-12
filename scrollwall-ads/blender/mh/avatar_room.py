"""Profile pictures of the guy in everyday moments (no Scrollwall branding):
reuses the reel's room/character setup (reel1/_head.py) with portrait cameras.

Shots: bed (fairy lights), desk (monitor glow), selfie (high angle), read (armchair + book).
ONLY=read renders a single one.
Usage: python avatar_room.py  -> /home/user/avatar_room/raw_<name>.png
"""
import math
import os

os.environ.setdefault('REEL', '/home/user/reel2')
os.environ.setdefault('FRAMES', 'avatar_tmp')
AR = int(os.environ.get('ARES', 400))
OUT = os.environ.get('OUT', '/home/user/avatar_room')
HEAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reel1', '_head.py')
__file__ = os.path.abspath(HEAD)  # _head.py resolves its paths from its own location
exec(compile(open(HEAD).read(), HEAD, 'exec'))

os.makedirs(OUT, exist_ok=True)
s.render.resolution_x = s.render.resolution_y = AR
s.cycles.samples = int(os.environ.get('ASPP', 32))
cd = bpy.data.cameras.new('acam')
cd.sensor_fit = 'VERTICAL'
cd.clip_start = 0.01
acam = bpy.data.objects.new('acam', cd)
s.collection.objects.link(acam)
s.camera = acam


def aim(loc, target, lens):
    acam.location = Vector(loc)
    acam.rotation_mode = 'QUATERNION'
    acam.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    cd.lens = lens


ONLY = os.environ.get('ONLY_SHOT')


def snap(name):
    if ONLY and name != ONLY:
        return
    s.render.filepath = os.path.join(OUT, f'raw_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', name, flush=True)


show_phone(False)
desk_phone.hide_render = True
hide_coins()

# 1) chilling on the bed in the late-afternoon sun, fairy lights behind
set_time(17.6)
pose_bed(0, scroll=0.0, look=0.05, free_arm_down=True)
point_bone('upperarm01.L', (0.3, 0.05, -1.0))
point_bone('lowerarm01.L', (0.1, -0.6, -1.0))
e = eyes()
aim(e + Vector((0.28, -0.62, -0.02)), e + Vector((0, 0, -0.05)), 38)
snap('bed')

# 2) gaming / working at the desk, lit by the monitor and the lamp
set_time(19.3)
pose_desk(0)
point_bone('head', (0.0, -0.25, 1.0))
e = eyes()
aim(e + Vector((0.32, -0.42, 0.02)), e + Vector((0, 0, -0.05)), 30)
snap('desk')

# 3) the classic high-angle selfie on the bed, golden hour
set_time(18.4)
pose_bed(0, scroll=0.0, look=-0.15, free_arm_down=True)
point_bone('upperarm01.L', (0.3, 0.05, -1.0))
point_bone('lowerarm01.L', (0.1, -0.6, -1.0))
e = eyes()
aim(e + Vector((0.12, -0.42, 0.32)), e + Vector((0, 0, -0.06)), 30)
snap('selfie')

# 4) reading a book in the armchair by the window (clothes pile hidden)
for o in bpy.data.objects:
    if o.name.startswith('chair_clothes'):
        o.hide_render = True
CHAIR = Vector((-1.33, -1.18))
FACE = Vector((0.64, 0.77)).normalized()  # chair turned toward the room
import bmesh  # noqa: E402


def make_book():
    me = bpy.data.meshes.new('book')
    bm = bmesh.new()
    for side in (-1, 1):
        for part, (sx, sy, sz, z) in (('cover', (0.16, 0.24, 0.006, 0.0)), ('pages', (0.15, 0.23, 0.014, 0.01))):
            r = bmesh.ops.create_cube(bm, size=1.0)
            vs = r['verts']
            for v in vs:
                v.co.x = v.co.x * sx + side * sx / 2
                v.co.y *= sy
                v.co.z = v.co.z * sz + z
            # open V: tilt each half up from the spine
            bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-14 * side), 3, 'Y'))
            for f in {f for v in vs for f in v.link_faces}:
                f.material_index = 0 if part == 'cover' else 1
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new('book', me)
    s.collection.objects.link(ob)
    for nm, col in (('book_cover', (0.35, 0.05, 0.04, 1)), ('book_pages', (0.85, 0.8, 0.68, 1))):
        m = bpy.data.materials.new(nm)
        m.use_nodes = True
        m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = col
        m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
        me.materials.append(m)
    return ob


def pose_read():
    reset_pose()
    rig.location = (CHAIR.x, CHAIR.y, 0.0)
    rig.rotation_euler = (0, 0, math.atan2(FACE.y, FACE.x) + math.pi / 2)
    for side, sg in (('L', 1), ('R', -1)):
        point_bone(f'upperleg01.{side}', (sg * 0.12, -1.0, 0.1))
        point_bone(f'lowerleg01.{side}', (sg * 0.06, -0.3, -1.0))
    for nm in ('spine05', 'spine04', 'spine03', 'spine02', 'spine01'):
        point_bone(nm, (0, 0.18, 1.0))
    point_bone('neck01', (0, -0.25, 1.0))
    point_bone('head', (0, -0.8, 1.0))
    point_bone('upperarm01.L', (0.25, -0.35, -1.0))
    point_bone('lowerarm01.L', (-0.5, -1.0, 0.55))
    point_bone('upperarm01.R', (-0.25, -0.35, -1.0))
    point_bone('lowerarm01.R', (0.5, -1.0, 0.55))
    for side in ('L', 'R'):  # normal-size hands here so they don't hide the book
        rig.pose.bones[f'wrist.{side}'].scale = (0.95, 0.95, 0.95)
    ground_hips(0.5)


set_time(16.4)
# warm window light falling on the reading nook
rl = bpy.data.lights.new('read_light', 'AREA')
rl.energy, rl.color, rl.size = 45, (1.0, 0.82, 0.62), 0.6
rlo = bpy.data.objects.new('read_light', rl)
s.collection.objects.link(rlo)
rlo.location = (-1.7, -0.45, 1.6)
rlo.rotation_euler = (Vector((-1.25, -1.05, 1.0)) - rlo.location).to_track_quat('-Z', 'Y').to_euler()
pose_read()
bpy.context.view_layer.update()
hl = rig.matrix_world @ rig.pose.bones['wrist.L'].tail
hr = rig.matrix_world @ rig.pose.bones['wrist.R'].tail
e = eyes()
book = make_book()
mid = (hl + hr) / 2 + Vector((0, 0, 0.07))
n = (e - mid).normalized()
across = (hl - hr).normalized()
y = n.cross(across).normalized()
x = y.cross(n).normalized()
book.matrix_world = Matrix.Translation(mid) @ Matrix((x, y, n)).transposed().to_4x4()
print('READ eyes', e, 'book', mid, flush=True)
f3 = Vector((FACE.x, FACE.y, 0))
look_at = e.lerp(mid, 0.45)
aim(look_at + f3 * 0.75 + Vector((0.18 * FACE.y, -0.18 * FACE.x, 0.12)), look_at, 26)
snap('read')
aim(look_at + f3 * 1.5 + Vector((0.4 * FACE.y, -0.4 * FACE.x, 0.35)), look_at + Vector((0, 0, -0.2)), 22)
snap('read_wide')
