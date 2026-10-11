"""Character look-dev renders (studio)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector, Quaternion
import char as C

OUT = os.path.join(C.HERE, '..', '..', 'out', 'ps1v2')
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = int(os.environ.get('SPP', 24))
s.cycles.use_denoising = True
s.cycles.max_bounces = 3
s.cycles.filter_width = 0.01
s.render.resolution_x, s.render.resolution_y = 270, 480
s.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.05, 0.05, 0.07, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
floor = bpy.data.meshes.new('floor')
import bmesh
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=4); bm.to_mesh(floor); bm.free()
fo = bpy.data.objects.new('floor', floor); s.collection.objects.link(fo)
fo.data.materials.append(C.cmat('floorm', (0.12, 0.11, 0.14), 0.8))

def light(name, kind, loc, energy, color=(1, 1, 1), size=1.0, target=(0, 0, 1.2)):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if kind == 'AREA': d.size = size
    o = bpy.data.objects.new(name, d); s.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o
light('key', 'AREA', (1.5, -2.2, 2.5), 140, (1, 0.93, 0.85), 1.5)
light('rim', 'AREA', (-1.6, 1.5, 2.2), 160, (0.6, 0.7, 1.0), 1.0)
light('fill', 'AREA', (-2, -1.5, 1.2), 30, (0.9, 0.85, 1.0), 2.0)

guy = C.Scroller()
cam_d = bpy.data.cameras.new('cam'); cam_d.sensor_fit = 'VERTICAL'
cam = bpy.data.objects.new('cam', cam_d); s.collection.objects.link(cam); s.camera = cam

def shot(name, loc, target, lens):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_d.lens = lens
    s.render.filepath = os.path.join(OUT, f'raw_char_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', name, flush=True)

guy.set_head('neutral')
shot('front', (0, -4.2, 1.0), (0, 0, 0.92), 40)
guy.root.rotation_euler = (0, 0, math.radians(35))
shot('34', (0, -4.2, 1.0), (0, 0, 0.92), 40)
guy.root.rotation_euler = (0, 0, math.radians(90))
shot('side', (0, -4.2, 1.0), (0, 0, 0.92), 40)
guy.root.rotation_euler = (0, 0, math.radians(20))
shot('face', (0.0, -1.0, 1.65), (0.0, 0, 1.6), 50)
guy.root.rotation_euler = (0, 0, math.radians(25))
guy.pose_phone(0.3)
guy.set_head('glazed')
guy.set_screen(bpy.data.images.load(os.path.join(C.HERE, '..', 'assets', 'ps1', 'feed', '0004.png')), 2.5)
shot('phone', (0.3, -2.2, 1.5), (0, 0, 1.3), 40)
