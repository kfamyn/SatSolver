"""Look-dev stills of the subway set with the cast. -> /home/user/reel3look/*.png"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector

import cast as K
cast = K.load_cast()
import subway  # noqa: E402  (after the cast: load_cast opens a new file)

OUT = os.environ.get('OUT', '/home/user/reel3look')
os.makedirs(OUT, exist_ok=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = int(os.environ.get('SPP', 16))
s.cycles.use_denoising = True
s.cycles.max_bounces = 4
s.cycles.filter_width = 0.01
s.render.resolution_x, s.render.resolution_y = 270, 480
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'None'
s.view_settings.exposure = float(os.environ.get('EXPO', -0.3))
S = subway.build()
subway.lights()
subway.set_tunnel(S, 0.3)

K.seat(cast['hero'], 0.55, 1, 'scroll', t=3)
K.seat(cast['business'], -0.75, 1, 'paper')
K.seat(cast['office'], 0.15, -1, 'read')
K.seat(cast['worker'], 1.05, -1, 'idle')
K.stand(cast['student'], -1.25, 0.35, facing=math.pi / 2)
import props as P  # noqa: E402
bg = [K.clone(cast['worker'], 'bg1'), K.clone(cast['office'], 'bg2'), K.clone(cast['business'], 'bg3')]
K.seat(bg[0], -3.7, -1, 'phone_down')
K.seat(bg[1], -4.2, 1, 'idle')
K.stand(bg[2], -3.0, -0.3, facing=-math.pi / 2)
K.turn_head(cast['worker'], 0.5)
hp, hp_tex = P.phone('hero_phone')
P.hold_phone(hp, cast['hero'])
sp, _ = P.phone('student_phone', 'screens/balance_00')
sp.hide_render = True
bk = P.book()
P.between_hands(bk, cast['office'], K.eyes(cast['office']))
np_ = P.newspaper()
P.between_hands(np_, cast['business'], K.eyes(cast['business']), lift=0.12, push=-0.05)

cd = bpy.data.cameras.new('c')
cd.sensor_fit = 'VERTICAL'
cd.clip_start = 0.02
cam = bpy.data.objects.new('c', cd)
s.collection.objects.link(cam)
s.camera = cam


def shot(name, loc, tgt, lens):
    cam.location = loc
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = lens
    s.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', name, flush=True)


shot('aisle', (4.4, 0.0, 1.55), (-1.0, 0.0, 1.05), 16)
shot('across', (0.45, 0.75, 1.15), (0.5, -1.2, 0.95), 18)
e = K.eyes(cast['hero'])
shot('hero', e + Vector((0.45, -0.75, 0.05)), e + Vector((0, 0, -0.18)), 26)
b = K.eyes(cast['business'])
pc = np_.matrix_world.translation
shot('paper', pc + Vector((0.05, -1.25, 0.0)), pc, 30)
shot('low', (2.2, -0.4, 0.35), (-0.5, 0.4, 1.0), 14)
