"""Look-dev stills: Doug wide, eye macro, Doug + Wally. Draft quality."""
import os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
from lib import reset, camera, area_light, hexc, aim
from characters import Doug, Wally, bedroom

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'out', 'drafts')
os.makedirs(OUT, exist_ok=True)
pct = int(os.environ.get('PCT', 33))
spp = int(os.environ.get('SPP', 16))

s = reset()
s.render.resolution_percentage = pct
s.cycles.samples = spp
bedroom('11:58')
doug = Doug(origin=(0, 0.45, 0.5), feed_dir=os.path.join(HERE, 'assets', 'feed'))
wally = Wally(origin=(0.95, -0.55, 0))
s.frame_set(37)
s.view_settings.exposure = 0.8
bpy.context.view_layer.update()

def shot(name, cam):
    s.camera = cam
    s.render.filepath = os.path.join(OUT, f'lookdev_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', s.render.filepath, flush=True)

eye = doug.eyes[1].matrix_world.translation.copy()
head = doug.head_pivot.matrix_world.translation.copy()
which = sys.argv[1:] or ['wide', 'eye', 'duo']
if 'wide' in which:
    shot('wide', camera('cam_wide', lens=26, loc=(0.85, -1.5, 1.45), target=(0.05, 0.3, 1.05), fstop=4))
if 'eye' in which:
    fwd = doug.eyes[1].matrix_world.to_quaternion() @ Vector((0, -1, 0))
    c = camera('cam_eye', lens=100, loc=tuple(eye + fwd * 0.11 + Vector((0.015, 0, 0.005))), target=tuple(eye), fstop=2.8)
    c.data.dof.focus_distance = 0.11
    shot('eye', c)
if 'duo' in which:
    shot('duo', camera('cam_duo', lens=30, loc=(0.35, -3.1, 1.15), target=(0.45, 0.1, 0.8), fstop=5.6))
