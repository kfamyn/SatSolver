"""PS1 look-dev stills: room wide, Doug close (trance), phone close (scrollwall)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector, Quaternion
import scene as S

OUT = os.path.join(S.HERE, '..', '..', 'out', 'ps1')
os.makedirs(OUT, exist_ok=True)


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = int(os.environ.get('SPP', 24))
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 3
    s.cycles.filter_width = 0.01  # no anti-aliasing: hard jaggies
    s.render.resolution_x = 270
    s.render.resolution_y = 480
    s.render.resolution_percentage = 100
    s.view_settings.view_transform = 'Standard'
    s.view_settings.look = 'None'
    w = bpy.data.worlds.new('w')
    s.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.7, 0.95, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
    return s


def sun(rot=(math.radians(60), 0, math.radians(-100)), energy=4.5):
    d = bpy.data.lights.new('sun', 'SUN')
    d.energy = energy
    d.color = (1.0, 0.92, 0.78)
    d.angle = math.radians(3)
    o = S.link(bpy.data.objects.new('sun', d))
    o.rotation_euler = rot
    return o


def cam(loc, target, lens=24, roll=0.0):
    c = bpy.data.cameras.new('cam')
    c.lens = lens
    c.sensor_fit = 'VERTICAL'
    c.sensor_width = 36
    o = S.link(bpy.data.objects.new('cam', c))
    o.location = loc
    d = (Vector(target) - Vector(loc)).normalized()
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), roll)
    bpy.context.scene.camera = o
    return o


s = setup()
clock = S.room()
sun()
bounce = bpy.data.lights.new('bounce', 'AREA'); bounce.energy = 120; bounce.size = 3; bounce.color = (1, 0.85, 0.75)
bo = S.link(bpy.data.objects.new('bounce', bounce)); bo.location = (0.8, -1.2, 2.6); bo.rotation_euler = (0.5, 0, 0.3)
doug = S.Doug((-0.55, 0.95, 0.42))
doug.pose_scroll(0.2)
doug.set_face('trance')
feed = S.img('feed/0004')
doug.set_screen(feed, 2.4)
clock.children[2].rotation_euler = (0, -math.radians(30 * 2), 0) if False else clock.children[2].rotation_euler
bpy.context.view_layer.update()


def shot(name, camobj):
    s.camera = camobj
    s.render.filepath = os.path.join(OUT, f'raw_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('wrote', name, flush=True)

head = doug.head.matrix_world.translation.copy()
shot('wide', cam((1.75, -2.4, 1.7), (-0.25, 0.6, 0.75), lens=18))
shot('face', cam(tuple(head + Vector((0.35, -1.0, 0.25))), tuple(head + Vector((0.02, -0.2, -0.15))), lens=32, roll=0.1))
# phone close-up: show the camera-facing screen with the scrollwall
doug.screen_front.hide_render = False
doug.set_screen(S.img('screens/shield_12'), 2.4)
ph = doug.phone.matrix_world.translation.copy()
fwd = doug.phone.matrix_world.to_quaternion() @ Vector((0, -1, 0))
shot('phone', cam(tuple(ph + fwd * 0.75), tuple(ph), lens=40))
