"""Bake the AI face photo into the MakeHuman body's own skin texture.

The front photo is planar-projected onto the front of the head (rest pose),
blended into the original skin with a soft mask, and the result baked into the
body's UV layout, so the face deforms with the rig like any other texture.
Skin tone of the rest of the body is matched to the photo.
"""
import math
import os

import bpy
import numpy as np
from mathutils import Vector

FACE_SRC = '/home/user/SatSolver/scrollwall-ads/blender/assets/ps1v2/face_src/t8.png'
OUT_IMG = os.environ.get('IMG', '/home/user/mh/skin_face.png')
EYE_PX = (160, 148)  # midpoint between the eyes in the photo
IPD_PX = 70.0

bpy.ops.wm.open_mainfile(filepath=os.environ.get('IN', '/home/user/mh/scroller.blend'))
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = 1
P = bpy.data.objects['Human.' + os.environ.get('PROXY', 'male1591')]
eyes = bpy.data.objects['Human.low-poly']
bb = [eyes.matrix_world @ Vector(c) for c in eyes.bound_box]
ex = max(v.x for v in bb) - min(v.x for v in bb)
eye_z = sum(v.z for v in bb) / 8
ipd_m = ex * 0.66  # eye centres ~2/3 of the pair's total width
k = IPD_PX / ipd_m
print('ipd', round(ipd_m, 4), 'eye_z', round(eye_z, 3), 'px/m', round(k), flush=True)

photo = bpy.data.images.load(FACE_SRC)
pw, ph = photo.size

# --- projected UVs + soft mask, from the rest-pose mesh
me = P.data
proj = me.uv_layers.new(name='proj')
mask = me.color_attributes.new('facemask', 'FLOAT_COLOR', 'CORNER')
mw = P.matrix_world
face_cz = eye_z - 0.03
for poly in me.polygons:
    n = (mw.to_3x3() @ poly.normal).normalized()
    for li in poly.loop_indices:
        co = mw @ me.vertices[me.loops[li].vertex_index].co
        u = (EYE_PX[0] + co.x * k) / pw
        v = 1 - (EYE_PX[1] - (co.z - eye_z) * k) / ph
        proj.data[li].uv = (u, v)
        front = max(0.0, min(1.0, (-n.y - 0.15) / 0.45))
        e = (co.x / 0.066) ** 2 + ((co.z - face_cz) / 0.105) ** 2
        rad = max(0.0, min(1.0, (1.0 - e) / 0.35))
        w = front * rad if co.y < -0.02 else 0.0
        mask.data[li].color = (w, w, w, 1)

# --- skin-tone match: photo cheek colour vs original skin around the face
pa = np.array(photo.pixels[:]).reshape(ph, pw, 4)[::-1]
cheek = pa[185:205, 105:135, :3].reshape(-1, 3).mean(0)
mat = P.material_slots[0].material
nt = mat.node_tree
skin_nodes = [n for n in nt.nodes if n.type == 'TEX_IMAGE']
skin_img = skin_nodes[0].image
sa = np.array(skin_img.pixels[:]).reshape(skin_img.size[1], skin_img.size[0], 4)
skin_avg = sa[..., :3].reshape(-1, 3)
skin_avg = skin_avg[skin_avg.sum(1) > 0.6].mean(0)
tone = np.clip(cheek / np.maximum(skin_avg, 1e-3) * 0.95, 0.4, 1.6)
print('tone', tone.round(3), flush=True)

# --- bake material
bake = bpy.data.materials.new('bake_face')
bake.use_nodes = True
b = bake.node_tree
b.nodes.clear()
out = b.nodes.new('ShaderNodeOutputMaterial')
em = b.nodes.new('ShaderNodeEmission')
uv0 = b.nodes.new('ShaderNodeUVMap'); uv0.uv_map = 'UVMap'
uv1 = b.nodes.new('ShaderNodeUVMap'); uv1.uv_map = 'proj'
t0 = b.nodes.new('ShaderNodeTexImage'); t0.image = skin_img
t1 = b.nodes.new('ShaderNodeTexImage'); t1.image = photo; t1.extension = 'EXTEND'
tint = b.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'
tint.inputs['Factor'].default_value = 1.0
tint.inputs['B'].default_value = (*tone, 1)
# smooth per-pixel mask: ellipse in photo space x front-facing normal
sep = b.nodes.new('ShaderNodeSeparateXYZ')
b.links.new(uv1.outputs['UV'], sep.inputs[0])
def m(op, a, bb=None, v1=None, v2=None):
    n_ = b.nodes.new('ShaderNodeMath'); n_.operation = op
    if a is not None: b.links.new(a, n_.inputs[0])
    else: n_.inputs[0].default_value = v1
    if bb is not None: b.links.new(bb, n_.inputs[1])
    elif v2 is not None: n_.inputs[1].default_value = v2
    return n_.outputs[0]
uc, vc, ru, rv = EYE_PX[0] / pw, 1 - 185 / ph, 78 / pw, 105 / ph
du = m('DIVIDE', m('SUBTRACT', sep.outputs['X'], None, v2=uc), None, v2=ru)
dv = m('DIVIDE', m('SUBTRACT', sep.outputs['Y'], None, v2=vc), None, v2=rv)
e = m('ADD', m('MULTIPLY', du, du), m('MULTIPLY', dv, dv))
rad = m('DIVIDE', m('SUBTRACT', None, e, v1=1.0), None, v2=0.45)
rad = m('MINIMUM', m('MAXIMUM', rad, None, v2=0.0), None, v2=1.0)
geo = b.nodes.new('ShaderNodeNewGeometry')
sn = b.nodes.new('ShaderNodeSeparateXYZ')
b.links.new(geo.outputs['Normal'], sn.inputs[0])
fr = m('DIVIDE', m('SUBTRACT', m('MULTIPLY', sn.outputs['Y'], None, v2=-1.0), None, v2=0.2), None, v2=0.5)
fr = m('MINIMUM', m('MAXIMUM', fr, None, v2=0.0), None, v2=1.0)
maskv = m('MULTIPLY', rad, fr)
mix = b.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
b.links.new(uv0.outputs['UV'], t0.inputs['Vector'])
b.links.new(uv1.outputs['UV'], t1.inputs['Vector'])
b.links.new(t0.outputs['Color'], tint.inputs['A'])
b.links.new(maskv, mix.inputs['Factor'])
b.links.new(tint.outputs['Result'], mix.inputs['A'])
b.links.new(t1.outputs['Color'], mix.inputs['B'])
b.links.new(mix.outputs['Result'], em.inputs['Color'])
b.links.new(em.outputs['Emission'], out.inputs['Surface'])
target = bpy.data.images.new('skin_face', 1024, 1024)
tn = b.nodes.new('ShaderNodeTexImage'); tn.image = target
b.nodes.active = tn
orig_mats = [sl.material for sl in P.material_slots]
for sl in P.material_slots:
    sl.material = bake
me.uv_layers.active = me.uv_layers['UVMap']
for o in bpy.context.view_layer.objects:
    o.select_set(False)
P.hide_render = False
P.hide_set(False)
P.select_set(True)
bpy.context.view_layer.objects.active = P
bpy.ops.object.bake(type='EMIT', margin=6, use_clear=True)
target.filepath_raw = OUT_IMG
target.file_format = 'PNG'
target.save()
print('baked', OUT_IMG, flush=True)
# put the original material back, now pointing at the baked skin
for sl, m in zip(P.material_slots, orig_mats):
    sl.material = m
baked = bpy.data.images.load(OUT_IMG)
for n in skin_nodes:
    n.image = baked
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get('OUT', '/home/user/mh/scroller_face.blend'))
print('saved', flush=True)
