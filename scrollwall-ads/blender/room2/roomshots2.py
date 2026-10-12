"""Look-dev stills of room v2 with the low-poly character in bed."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Matrix, Vector

OUT = '/home/user/SatSolver/scrollwall-ads/out/room2'
os.makedirs(OUT, exist_ok=True)
# start from the character file so the rigged guy comes along
bpy.ops.wm.open_mainfile(filepath='/home/user/mh/scroller_lp.blend')
import room2  # noqa: E402  (after the file load: helpers create data in this scene)
from ps1fy import ps1fy  # noqa: E402

s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = int(os.environ.get('SPP', 48))
s.cycles.use_denoising = True
s.cycles.max_bounces = 4
s.cycles.volume_bounces = 0
s.cycles.volume_step_rate = 4.0
s.cycles.filter_width = 0.01
s.render.resolution_x, s.render.resolution_y = 270, 480
s.render.resolution_percentage = 100
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'AgX - Punchy'
s.view_settings.exposure = float(os.environ.get('EXPO', 0.0))
if s.world is None:
    s.world = bpy.data.worlds.new('w')
s.world.use_nodes = True
s.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.65, 0.9, 1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.05

# character: PS1 textures, matte, sitting up in bed scrolling
body = bpy.data.objects['Human.proxy741']
ps1fy([body], decimate=1.0, tex_px=224)
ps1fy([o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Human') and o is not body], decimate=1.0, tex_px=64)
for sl in body.material_slots:
    for n in sl.material.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            n.inputs['Roughness'].default_value = 0.9
rig = bpy.data.objects['Human.rig']
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mh'))
from style import apply_style  # noqa: E402
apply_style(rig)

S = room2.build()
room2.lights(float(os.environ.get('SUN', 14)), float(os.environ.get('HAZE', 0.02)))

# place him sitting up against the headboard, legs out under the duvet edge, phone up
rig.location = (-0.85, 1.12, 0.0)
rig.rotation_euler = (0, 0, 0)


def point_bone(name, direction):
    pb = rig.pose.bones[name]
    bpy.context.view_layer.update()
    head = pb.head.copy()
    cur = (pb.tail - pb.head).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    pb.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ pb.matrix
    bpy.context.view_layer.update()


for side, sg in (('L', 1), ('R', -1)):
    point_bone(f'upperleg01.{side}', (sg * 0.06, -1.0, 0.0))
    point_bone(f'lowerleg01.{side}', (sg * 0.04, -1.0, -0.08))
for nm in ('spine05', 'spine04', 'spine03', 'spine02', 'spine01'):
    point_bone(nm, (0, 0.28, 1.0))
point_bone('neck01', (0, -0.1, 1.0))
point_bone('head', (0, -0.55, 1.0))
point_bone('upperarm01.L', (0.22, -0.45, -1.0))
point_bone('lowerarm01.L', (-0.45, -1.0, 0.75))
point_bone('upperarm01.R', (-0.22, -0.45, -1.0))
point_bone('lowerarm01.R', (0.4, -1.0, 0.7))
# sit him ON the mattress: lowest body point -> mattress top
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg)
zmin = min((ev.matrix_world @ v.co).z for v in ev.data.vertices)
rig.location.z += 0.57 - zmin
bpy.context.view_layer.update()
# the phone, held in the left hand
import bmesh  # noqa: E402
pm = bpy.data.meshes.new('phone')
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co.x *= 0.075; v.co.y *= 0.009; v.co.z *= 0.155
for f in bm.faces:
    if f.normal.y < -0.5:  # the face pointing at his eyes is the screen
        f.material_index = 1
bm.to_mesh(pm); bm.free()
phone = bpy.data.objects.new('phone', pm)
s.collection.objects.link(phone)
pmat = bpy.data.materials.new('phone_m'); pmat.use_nodes = True
pb_ = pmat.node_tree.nodes['Principled BSDF']; pb_.inputs['Base Color'].default_value = (0.02, 0.02, 0.025, 1); pb_.inputs['Roughness'].default_value = 0.3
phone.data.materials.append(pmat)
scr = bpy.data.materials.new('phone_screen'); scr.use_nodes = True
sn = scr.node_tree.nodes; sn.clear()
so = sn.new('ShaderNodeOutputMaterial'); se = sn.new('ShaderNodeEmission'); st = sn.new('ShaderNodeTexImage')
st.image = bpy.data.images.load('/home/user/SatSolver/scrollwall-ads/blender/assets/ps1/feed/0004.png'); st.interpolation = 'Closest'
se.inputs['Strength'].default_value = 3.0
scr.node_tree.links.new(st.outputs['Color'], se.inputs['Color']); scr.node_tree.links.new(se.outputs['Emission'], so.inputs['Surface'])
phone.data.materials.append(scr)
phone.parent = rig
phone.parent_type = 'BONE'
phone.parent_bone = 'wrist.L'
phone.location = (0.0, 0.05, 0.0)
phone.rotation_euler = (math.radians(70), 0, 0)
sl = bpy.data.lights.new('phone_light', 'POINT')
sl.energy, sl.color, sl.shadow_soft_size = 2.0, (0.7, 0.82, 1.0), 0.04
plo = bpy.data.objects.new('phone_light', sl)
s.collection.objects.link(plo)
plo.parent = phone
plo.location = (0, -0.12, 0.05)

cd = bpy.data.cameras.new('cam')
cd.sensor_fit = 'VERTICAL'
cam = bpy.data.objects.new('cam', cd)
s.collection.objects.link(cam)
s.camera = cam


def shot(name, loc, target, lens):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = lens
    s.render.filepath = os.path.join(OUT, f'raw_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', name, flush=True)


which = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['wide', 'desk', 'corner', 'night', 'bed']
if 'wide' in which: shot('wide', (1.3, -1.5, 1.7), (-0.5, 0.85, 0.8), 16)
if 'desk' in which: shot('desk', (-0.2, -0.6, 1.45), (1.55, 0.5, 0.95), 18)
if 'corner' in which: shot('corner', (0.3, 0.9, 1.5), (-1.3, -1.1, 0.6), 18)
if 'night' in which: shot('night', (-0.25, 0.7, 0.95), (0.2, 1.42, 0.6), 22)
if 'bed' in which: shot('bed', (-0.2, -0.4, 1.25), (-0.85, 1.05, 0.95), 24)
