"""Profile pictures of the guy in everyday moments (no Scrollwall branding):
reuses the reel's room/character setup (reel1/_head.py) with portrait cameras.

Shots: bed (fairy lights), desk (monitor glow), selfie (high angle).
Usage: python avatar_room.py  -> /home/user/avatar_room/raw_<name>.png
"""
import math
import os

os.environ.setdefault('REEL', '/home/user/reel2')
os.environ.setdefault('FRAMES', 'avatar_tmp')
AR = int(os.environ.get('ARES', 400))
OUT = os.environ.get('OUT', '/home/user/avatar_room')
HEAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reel1', '_head.py')
__file__ = os.path.abspath(HEAD)  # _head.py resolves its paths from its own location
exec(compile(open(HEAD).read(), HEAD, 'exec'))

os.makedirs(OUT, exist_ok=True)
s.render.resolution_x = s.render.resolution_y = AR
s.cycles.samples = int(os.environ.get('ASPP', 32))
cd = bpy.data.cameras.new('acam')
cd.sensor_fit = 'VERTICAL'
cd.clip_start = 0.01
acam = bpy.data.objects.new('acam', cd)
s.collection.objects.link(acam)
s.camera = acam


def aim(loc, target, lens):
    acam.location = Vector(loc)
    acam.rotation_mode = 'QUATERNION'
    acam.rotation_quaternion = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y')
    cd.lens = lens


def snap(name):
    s.render.filepath = os.path.join(OUT, f'raw_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', name, flush=True)


show_phone(False)
desk_phone.hide_render = True
hide_coins()

# 1) chilling on the bed in the late-afternoon sun, fairy lights behind
set_time(17.6)
pose_bed(0, scroll=0.0, look=0.05, free_arm_down=True)
point_bone('upperarm01.L', (0.3, 0.05, -1.0))
point_bone('lowerarm01.L', (0.1, -0.6, -1.0))
e = eyes()
aim(e + Vector((0.28, -0.62, -0.02)), e + Vector((0, 0, -0.05)), 38)
snap('bed')

# 2) gaming / working at the desk, lit by the monitor and the lamp
set_time(19.3)
pose_desk(0)
point_bone('head', (0.0, -0.25, 1.0))
e = eyes()
aim(e + Vector((0.32, -0.42, 0.02)), e + Vector((0, 0, -0.05)), 30)
snap('desk')

# 3) the classic high-angle selfie on the bed, golden hour
set_time(18.4)
pose_bed(0, scroll=0.0, look=-0.15, free_arm_down=True)
point_bone('upperarm01.L', (0.3, 0.05, -1.0))
point_bone('lowerarm01.L', (0.1, -0.6, -1.0))
e = eyes()
aim(e + Vector((0.12, -0.42, 0.32)), e + Vector((0, 0, -0.06)), 30)
snap('selfie')
