"""Room look-dev stills (with the character in bed)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import char as C
import room

OUT = os.path.join(C.HERE, '..', '..', 'out', 'ps1v2')
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = int(os.environ.get('SPP', 32))
s.cycles.use_denoising = True
s.cycles.max_bounces = 4
s.cycles.filter_width = 0.01
s.render.resolution_x, s.render.resolution_y = 270, 480
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'AgX - Medium High Contrast'
w = bpy.data.worlds.new('w'); s.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.65, 0.9, 1)
w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.15
S = room.build(15.2)
room.lights()
guy = C.Scroller(loc=(-0.85, 1.15, -0.32))
guy.pose_bed(0.2)
guy.set_head('glazed')
guy.set_screen(bpy.data.images.load(os.path.join(C.HERE, '..', 'assets', 'ps1', 'feed', '0004.png')), 2.5)
cd = bpy.data.cameras.new('cam'); cd.sensor_fit = 'VERTICAL'
cam = bpy.data.objects.new('cam', cd); s.collection.objects.link(cam); s.camera = cam

def shot(name, loc, target, lens):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = lens
    s.render.filepath = os.path.join(OUT, f'raw_room_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', name, flush=True)

which = sys.argv[1:] or ['wide', 'reverse', 'night', 'desk', 'floor']
if 'wide' in which: shot('wide', (1.25, -1.55, 1.65), (-0.55, 0.85, 0.85), 16)
if 'reverse' in which: shot('reverse', (-1.3, 1.2, 1.5), (1.3, -0.2, 0.9), 16)
if 'night' in which: shot('night', (-0.2, 0.75, 0.95), (0.25, 1.45, 0.6), 24)
if 'desk' in which: shot('desk', (0.3, -0.3, 1.35), (1.55, 0.4, 0.95), 20)
if 'floor' in which: shot('floor', (-0.2, -1.6, 0.6), (0.4, -0.7, 0.05), 18)
