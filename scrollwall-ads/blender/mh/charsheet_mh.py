"""Look-dev renders of the MakeHuman-based character, PS1-ified."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector

from ps1fy import ps1fy

OUT = '/home/user/SatSolver/scrollwall-ads/out/mh'
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.environ.get('BLEND', '/home/user/mh/scroller_face.blend'))
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = 24
s.cycles.use_denoising = True
s.cycles.max_bounces = 3
s.cycles.filter_width = 0.01
s.render.resolution_x, s.render.resolution_y = 270, 480
s.render.resolution_percentage = 100
s.view_settings.view_transform = 'AgX'
if s.world is None:
    s.world = bpy.data.worlds.new('w')
s.world.use_nodes = True
s.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.04, 0.04, 0.06, 1)
# skin atlas keeps more pixels so the face survives; everything else stays tiny
body = bpy.data.objects['Human.' + os.environ.get('PROXY', 'male1591')]
ps1fy([body], decimate=1.0, tex_px=int(os.environ.get('SKIN', 512)))
ps1fy([o for o in bpy.data.objects if o.type == 'MESH' and o is not body], decimate=float(os.environ.get('DEC', 0.35)), tex_px=int(os.environ.get('TEX', 128)))
# dark-brown hair to match the face photo
_hair = next(o for o in bpy.data.objects if o.type == 'MESH' and ('hair' in o.name or 'short0' in o.name))
for sl in _hair.material_slots:
    nt = sl.material.node_tree
    tex = nt.nodes.get('diffuseTexture') or next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and 'norm' not in n.name.lower()), None)
    bsdf = nt.nodes.get('Principled BSDF')
    if tex and bsdf:
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
        mul.inputs['Factor'].default_value = 1.0
        mul.inputs['B'].default_value = (0.22, 0.13, 0.08, 1)
        nt.links.new(tex.outputs['Color'], mul.inputs['A'])
        nt.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])

rig = bpy.data.objects['Human.rig']
for sl in body.material_slots:  # matte, like old games
    for n in sl.material.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            n.inputs['Roughness'].default_value = 0.9
            n.inputs['Specular IOR Level'].default_value = 0.15
print('bones', [b.name for b in rig.pose.bones][:40], flush=True)
# arms down from the A-pose
from mathutils import Matrix


def point_bone(rig, name, direction):
    """Rotate a pose bone (armature space) so it points along `direction`."""
    pb = rig.pose.bones[name]
    bpy.context.view_layer.update()
    head = pb.head.copy()
    cur = (pb.tail - pb.head).normalized()
    q = cur.rotation_difference(Vector(direction).normalized())
    pb.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ pb.matrix
    bpy.context.view_layer.update()


OUTW = float(os.environ.get('ARM_OUT', 0.22))
for side, sg in (('L', 1), ('R', -1)):
    point_bone(rig, f'upperarm01.{side}', (sg * OUTW, 0.03, -1.0))
    point_bone(rig, f'lowerarm01.{side}', (sg * OUTW * 0.6, -0.12, -1.0))


def light(name, loc, energy, color, size=1.5, target=(0, 0, 1.2)):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy, d.color, d.size = energy, color, size
    o = bpy.data.objects.new(name, d)
    s.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


light('key', (1.5, -2.2, 2.5), 160, (1, 0.93, 0.85))
light('rim', (-1.6, 1.5, 2.2), 180, (0.6, 0.7, 1.0), 1.0)
light('fill', (-2, -1.5, 1.2), 40, (0.9, 0.85, 1.0), 2.0)
cd = bpy.data.cameras.new('cam')
cd.sensor_fit = 'VERTICAL'
cam = bpy.data.objects.new('cam', cd)
s.collection.objects.link(cam)
s.camera = cam
top = max((o.matrix_world @ Vector(c)).z for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render for c in o.bound_box)
print('height', round(top, 3), flush=True)


def shot(name, loc, target, lens, rotz=0.0):
    rig.rotation_euler = (0, 0, math.radians(rotz))
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = lens
    s.render.filepath = os.path.join(OUT, f'raw_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', name, flush=True)


h = top
shot('front', (0, -4.4, h * 0.55), (0, 0, h * 0.52), 40)
shot('34', (0, -4.4, h * 0.55), (0, 0, h * 0.52), 40, 35)
shot('side', (0, -4.4, h * 0.55), (0, 0, h * 0.52), 40, 90)
shot('face', (0.0, -1.0, h * 0.93), (0, 0, h * 0.92), 50, 20)
