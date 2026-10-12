"""Profile-picture renders of the Scrollwall guy (PS1 look, square, circle-safe).

Variants: wall (warm key, violet rim), glow (lit from below by the phone),
front (straight on).
Usage: python avatar.py   -> /home/user/avatar/char_<variant>.png + heads.json,
then python3 avatar_compose.py for the final squares.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Matrix, Vector

from ps1fy import ps1fy
from style import apply_style

OUT = os.environ.get('OUT', '/home/user/avatar')
RES = int(os.environ.get('RES', 320))
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath='/home/user/mh/scroller_lp.blend')
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = 48
s.cycles.use_denoising = True
s.cycles.max_bounces = 3
s.cycles.filter_width = 0.01
s.render.resolution_x = s.render.resolution_y = RES
s.render.resolution_percentage = 100
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'AgX - Punchy'
if s.world is None:
    s.world = bpy.data.worlds.new('w')
s.world.use_nodes = True
bg_node = s.world.node_tree.nodes['Background']
bg_node.inputs['Strength'].default_value = 0.05

body = bpy.data.objects['Human.proxy741']
ps1fy([body], decimate=1.0, tex_px=256)
ps1fy([o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Human') and o is not body], decimate=1.0, tex_px=64)
for sl in body.material_slots:
    for n in sl.material.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            n.inputs['Roughness'].default_value = 0.9
rig = bpy.data.objects['Human.rig']


def point_bone(name, direction):
    pb = rig.pose.bones[name]
    bpy.context.view_layer.update()
    head = pb.head.copy()
    cur = (pb.tail - pb.head).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    pb.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ pb.matrix


for side, sg in (('L', 1), ('R', -1)):
    point_bone(f'upperarm01.{side}', (sg * 0.22, 0.03, -1.0))
    point_bone(f'lowerarm01.{side}', (sg * 0.13, -0.12, -1.0))
apply_style(rig)
bpy.context.view_layer.update()
head = rig.matrix_world @ rig.pose.bones['head'].head
eyes = bpy.data.objects['Human.low-poly']
ev = eyes.evaluated_get(bpy.context.evaluated_depsgraph_get())
pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
EYE = sum(pts, Vector()) / len(pts)
pbh = rig.pose.bones['head']
HEAD = rig.matrix_world @ ((pbh.head + pbh.tail) / 2)
print('eyes', EYE, 'head', HEAD, flush=True)

# dark-brown hair to match the face photo (same tint as the look-dev sheet)
_hair = next(o for o in bpy.data.objects if o.type == 'MESH' and ('hair' in o.name or 'short0' in o.name))
for sl in _hair.material_slots:
    hn = sl.material.node_tree
    tex = next((n for n in hn.nodes if n.type == 'TEX_IMAGE' and 'norm' not in n.name.lower()), None)
    bsdf = hn.nodes.get('Principled BSDF')
    if tex and bsdf:
        mul = hn.nodes.new('ShaderNodeMix')
        mul.data_type, mul.blend_type = 'RGBA', 'MULTIPLY'
        mul.inputs['Factor'].default_value = 1.0
        mul.inputs['B'].default_value = (0.22, 0.13, 0.08, 1)
        hn.links.new(tex.outputs['Color'], mul.inputs['A'])
        hn.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])

# ---- background: force-field wall with the ghost
img = bpy.data.images.load(os.path.join(HERE, '..', 'assets', 'ps1', 'screens', 'forcefield.png'))
bgm = bpy.data.meshes.new('bgwall')
w, h = 2.4, 1.44
bgm.from_pydata([(-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2)], [], [(0, 1, 2, 3)])
uv = bgm.uv_layers.new(name='UVMap')
for i, c in enumerate(((0, 0.5), (1, 0.5), (1, 1), (0, 1))):
    uv.data[i].uv = c
bgo = bpy.data.objects.new('bgwall', bgm)
s.collection.objects.link(bgo)
m = bpy.data.materials.new('bgwall')
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
o = nt.nodes.new('ShaderNodeOutputMaterial')
e = nt.nodes.new('ShaderNodeEmission')
t = nt.nodes.new('ShaderNodeTexImage')
t.image, t.interpolation = img, 'Closest'
# composite the translucent texture over a deep violet base
mx = nt.nodes.new('ShaderNodeMixRGB')
mx.inputs['Color1'].default_value = (0.05, 0.025, 0.16, 1)
nt.links.new(t.outputs['Alpha'], mx.inputs['Fac'])
nt.links.new(t.outputs['Color'], mx.inputs['Color2'])
nt.links.new(mx.outputs['Color'], e.inputs['Color'])
e.inputs['Strength'].default_value = 1.4
nt.links.new(e.outputs[0], o.inputs['Surface'])
bgm.materials.append(m)

L = {}


def light(name, kind, loc, energy, color, size=0.5, target=None):
    d = bpy.data.lights.new(name, kind)
    d.energy, d.color = energy, color
    if kind == 'AREA':
        d.size = size
    else:
        d.shadow_soft_size = size
    ob = bpy.data.objects.new(name, d)
    s.collection.objects.link(ob)
    ob.location = loc
    tg = Vector(target) if target else EYE
    ob.rotation_euler = (tg - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    L[name] = ob
    return ob


light('key', 'AREA', EYE + Vector((0.5, -0.8, 0.35)), 22, (1.0, 0.9, 0.78), 0.6)
light('rim', 'AREA', EYE + Vector((-0.45, 0.5, 0.2)), 30, (0.6, 0.45, 1.0), 0.5)
light('rim2', 'AREA', EYE + Vector((0.45, 0.5, 0.15)), 18, (0.6, 0.45, 1.0), 0.5)
light('phone', 'POINT', EYE + Vector((0.0, -0.25, -0.22)), 3.5, (0.7, 0.82, 1.0), 0.05)
light('fill', 'AREA', EYE + Vector((-0.7, -0.6, 0.0)), 6, (0.9, 0.85, 1.0), 1.0)

cd = bpy.data.cameras.new('cam')
cam = bpy.data.objects.new('cam', cd)
s.collection.objects.link(cam)
s.camera = cam


import json  # noqa: E402

from bpy_extras.object_utils import world_to_camera_view  # noqa: E402

s.render.film_transparent = True
bgo.hide_render = True
s.render.resolution_x = s.render.resolution_y = RES
info = {}


def render(name, cam_off, lens, energies):
    """character only (transparent); avatar_compose.py adds the background and crop."""
    for k, v in energies.items():
        L[k].data.energy = v
    tgt = HEAD + Vector((0, 0, -0.02))
    cam.location = tgt + Vector(cam_off)
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = lens
    bpy.context.view_layer.update()
    c = world_to_camera_view(s, cam, HEAD)
    top = world_to_camera_view(s, cam, HEAD + Vector((0, 0, 0.16)))
    info[name] = {'cx': c.x, 'cy': 1 - c.y, 'top': 1 - top.y}
    s.render.filepath = os.path.join(OUT, f'char_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', name, flush=True)


render('wall', (0.3, -0.95, 0.02), 40, {'key': 22, 'rim': 30, 'rim2': 18, 'phone': 0, 'fill': 6})
render('glow', (0.25, -0.9, -0.04), 40, {'key': 0, 'rim': 22, 'rim2': 12, 'phone': 5, 'fill': 0})
render('front', (0.0, -0.95, 0.0), 40, {'key': 22, 'rim': 30, 'rim2': 18, 'phone': 1.5, 'fill': 8})
json.dump(info, open(os.path.join(OUT, 'heads.json'), 'w'))
