"""PS1-style clothing: bake the hoodie / pants / shoes colours onto the
low-poly body's own texture, then drop the cloth meshes. Hair is decimated to
a few dozen polygons. The face (already baked into the skin) is kept wherever
no cloth is hit.

Env: IN (blend with face), OUT (blend), IMG (output texture), PROXY.
"""
import os

import bpy
import numpy as np

IN = os.environ.get('IN', '/home/user/mh/scroller741_face.blend')
OUT = os.environ.get('OUT', '/home/user/mh/scroller_lp.blend')
IMG = os.environ.get('IMG', '/home/user/mh/skin_lp.png')
PROXY = os.environ.get('PROXY', 'proxy741')
RES = int(os.environ.get('RES', 512))

bpy.ops.wm.open_mainfile(filepath=IN)
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = 8
body = bpy.data.objects['Human.' + PROXY]
cloth = [o for o in bpy.data.objects if o.type == 'MESH' and any(k in o.name for k in ('jacket', 'pants', 'shoes'))]
print('cloth', [o.name for o in cloth], flush=True)

# recolour the hoodie to heather grey (reads better at PS1 resolution)
for o in cloth:
    if 'jacket' not in o.name:
        continue
    for sl in o.material_slots:
        nt = sl.material.node_tree
        bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is None or not bsdf.inputs['Base Color'].links:
            continue
        src_sock = bsdf.inputs['Base Color'].links[0].from_socket
        hsv = nt.nodes.new('ShaderNodeHueSaturation')
        hsv.inputs['Saturation'].default_value = float(os.environ.get('HOOD_SAT', 0.12))
        hsv.inputs['Value'].default_value = float(os.environ.get('HOOD_VAL', 3.2))
        nt.links.new(src_sock, hsv.inputs['Color'])
        nt.links.new(hsv.outputs['Color'], bsdf.inputs['Base Color'])

# target starts as the face-baked skin, resized to RES
mat = body.material_slots[0].material
skin_nodes = [n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE']
src = skin_nodes[0].image
tmp = src.copy()
tmp.scale(RES, RES)
target = bpy.data.images.new('skin_lp', RES, RES)
target.pixels[:] = tmp.pixels[:]

tn = mat.node_tree.nodes.new('ShaderNodeTexImage')
tn.image = target
mat.node_tree.nodes.active = tn

bk = s.render.bake
bk.use_pass_direct = False
bk.use_pass_indirect = False
bk.use_pass_color = True
bk.use_selected_to_active = True
bk.use_cage = False
bk.cage_extrusion = float(os.environ.get('EXTRUDE', 0.05))
bk.max_ray_distance = float(os.environ.get('RAYDIST', 0.12))
bk.margin = 4
bk.use_clear = False

for o in bpy.context.view_layer.objects:
    o.select_set(False)
for o in cloth:
    o.hide_render = False
    o.select_set(True)
body.hide_render = False
body.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.bake(type='DIFFUSE', use_clear=False)
target.filepath_raw = IMG
target.file_format = 'PNG'
target.save()
print('baked', IMG, flush=True)

mat.node_tree.nodes.remove(tn)
baked = bpy.data.images.load(IMG)
for n in skin_nodes:
    n.image = baked
for o in cloth:
    bpy.data.objects.remove(o, do_unlink=True)

# hair: crush it to a low-poly helmet of cards
hair = next((o for o in bpy.data.objects if o.type == 'MESH' and ('hair' in o.name or 'short0' in o.name)), None)
if hair:
    m = hair.modifiers.new('ps1_decimate', 'DECIMATE')
    m.ratio = float(os.environ.get('HAIR', 0.08))
for o in bpy.data.objects:
    if o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('saved', OUT, flush=True)
