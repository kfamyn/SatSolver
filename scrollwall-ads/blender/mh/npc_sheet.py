"""Lineup render of one subway NPC (front, PS1-ified). Env: BLEND, PROXY, OUTPNG."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Matrix, Vector

from ps1fy import ps1fy
from style import apply_style

bpy.ops.wm.open_mainfile(filepath=os.environ['BLEND'])
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = 16
s.cycles.use_denoising = True
s.cycles.filter_width = 0.01
s.render.resolution_x, s.render.resolution_y = 200, 400
s.view_settings.view_transform = 'AgX'
if s.world is None:
    s.world = bpy.data.worlds.new('w')
s.world.use_nodes = True
s.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.3, 0.3, 0.33, 1)
s.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
body = bpy.data.objects['Human.' + os.environ['PROXY']]
ps1fy([body], decimate=1.0, tex_px=224)
ps1fy([o for o in bpy.data.objects if o.type == 'MESH' and o is not body], decimate=1.0, tex_px=64)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')


def point_bone(name, d):
    pb = rig.pose.bones[name]
    bpy.context.view_layer.update()
    h = pb.head.copy()
    q = (pb.tail - pb.head).normalized().rotation_difference(Vector(d).normalized())
    pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix


for side, sg in (('L', 1), ('R', -1)):
    point_bone(f'upperarm01.{side}', (sg * 0.2, 0.03, -1.0))
    point_bone(f'lowerarm01.{side}', (sg * 0.12, -0.12, -1.0))
apply_style(rig)
for loc, e in (((1.5, -2.5, 2.5), 300), ((-2, 1.5, 2), 150)):
    L = bpy.data.lights.new('l', 'AREA')
    L.energy, L.size = e, 1.5
    o = bpy.data.objects.new('l', L)
    s.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 1)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
cd = bpy.data.cameras.new('c')
cam = bpy.data.objects.new('c', cd)
s.collection.objects.link(cam)
s.camera = cam
cam.location = (0, -4.2, 0.85)
cam.rotation_euler = (Vector((0, 0, 0.8)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cd.lens = 40
s.render.filepath = os.environ['OUTPNG']
bpy.ops.render.render(write_still=True)
