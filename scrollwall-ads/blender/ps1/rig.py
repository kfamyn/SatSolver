"""Render setup, lights and camera helpers for the PS1 shorts."""
import math
import os

import bpy
from mathutils import Quaternion, Vector

import scene as S


def setup(res=(270, 480), spp=16):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = spp
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 3
    s.cycles.filter_width = 0.01  # no anti-aliasing: hard jaggies
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.render.use_persistent_data = True
    s.view_settings.view_transform = 'Standard'
    s.view_settings.look = 'None'
    w = bpy.data.worlds.new('w')
    s.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.7, 0.95, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.55
    return s


def sun():
    d = bpy.data.lights.new('sun', 'SUN')
    d.energy = 4.5
    d.color = (1.0, 0.92, 0.78)
    d.angle = math.radians(3)
    return S.link(bpy.data.objects.new('sun', d))


def set_sun(o, hour):
    """Sun comes in through the left-wall window; arcs and warms through the day."""
    k = (hour - 9) / 9  # 9:00 .. 18:00
    k = max(0, min(1, k))
    elev = math.radians(65 - 45 * k)
    az = math.radians(-120 + 40 * k)
    o.rotation_euler = (elev, 0, az)
    warm = Vector((1.0, 0.92, 0.78)).lerp(Vector((1.0, 0.62, 0.38)), k)
    o.data.color = tuple(warm)
    o.data.energy = 4.5 - 1.5 * k


def bounce():
    d = bpy.data.lights.new('bounce', 'AREA')
    d.energy = 120
    d.size = 3
    d.color = (1, 0.85, 0.75)
    o = S.link(bpy.data.objects.new('bounce', d))
    o.location = (0.8, -1.2, 2.6)
    o.rotation_euler = (0.5, 0, 0.3)
    return o


class Cam:
    def __init__(self):
        c = bpy.data.cameras.new('cam')
        c.sensor_fit = 'VERTICAL'
        c.sensor_width = 36
        c.clip_start = 0.01
        self.o = S.link(bpy.data.objects.new('cam', c))
        bpy.context.scene.camera = self.o

    def set(self, loc, target, lens=24, roll=0.0, snap=0.01):
        """PS1-ish: camera position snapped to a coarse grid -> slightly jerky moves."""
        loc = Vector([round(v / snap) * snap for v in loc])
        d = (Vector(target) - loc).normalized()
        self.o.location = loc
        self.o.rotation_mode = 'QUATERNION'
        self.o.rotation_quaternion = d.to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), roll)
        self.o.data.lens = lens


def world(obj):
    bpy.context.view_layer.update()
    return obj.matrix_world.translation.copy()


def forward(obj, axis=(0, -1, 0)):
    bpy.context.view_layer.update()
    return obj.matrix_world.to_quaternion() @ Vector(axis)
