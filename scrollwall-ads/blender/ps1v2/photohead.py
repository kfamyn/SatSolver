"""Low-poly head textured the PS1 way: a front photo projected onto the
front-facing polygons and a profile photo projected onto the sides/back, then
stretched. Seams are left visible on purpose.

Landmarks are measured in the source crops (pixels):
  front (t8, 300x360): centre x=160, chin y=275, top of hair y=5
  profile (t1, 300x260): nose tip x=65, chin y=190, top of hair y=12
"""
import math
import os

import bmesh
import bpy
from mathutils import Vector

FRONT = dict(w=300, h=360, cx=160, chin=275, top=5)
SIDE = dict(w=300, h=260, nose=65, chin=190, top=12)
HEAD_H = 0.27  # chin -> top of hair, metres
NOSE_Y = -0.125  # nose tip depth (front is -Y)

# (z above chin, width, depth, y offset, squareness)
RINGS = [
    (0.000, 0.060, 0.050, -0.080, 2.0),
    (0.020, 0.110, 0.120, -0.050, 2.2),
    (0.050, 0.135, 0.170, -0.030, 2.4),
    (0.085, 0.150, 0.200, -0.012, 2.5),
    (0.120, 0.158, 0.212, 0.002, 2.5),
    (0.150, 0.172, 0.228, 0.008, 2.4),
    (0.190, 0.188, 0.245, 0.014, 2.3),
    (0.230, 0.178, 0.235, 0.018, 2.2),
    (0.258, 0.128, 0.175, 0.018, 2.0),
    (0.272, 0.050, 0.070, 0.016, 2.0),
]


def _uv_front(co):
    s = HEAD_H / (FRONT['chin'] - FRONT['top'])
    px = FRONT['cx'] + co.x / s
    py = FRONT['chin'] - co.z / s
    return (px / FRONT['w'], 1 - py / FRONT['h'])


def _uv_side(co):
    s = HEAD_H / (SIDE['chin'] - SIDE['top'])
    px = SIDE['nose'] + 14 + (co.y - NOSE_Y) / s * 0.93
    py = SIDE['chin'] - co.z / s
    return (px / SIDE['w'], 1 - py / SIDE['h'])


def photo_mat(name, path):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(path)
    t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.65
    b.inputs['Specular IOR Level'].default_value = 0.25
    m['tex'] = t.name
    return m


def build(name, front_path, side_path, parent=None, n=12):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for (z, w, d, yo, sq) in RINGS:
        ring = []
        for k in range(n):
            th = 2 * math.pi * k / n
            s_, c_ = math.sin(th), math.cos(th)
            p = 2.0 / sq
            x = (w / 2) * math.copysign(abs(s_) ** p, s_)
            y = -(d / 2) * math.copysign(abs(c_) ** p, c_) + yo
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    for r in range(len(rings) - 1):
        for k in range(n):
            k2 = (k + 1) % n
            bm.faces.new((rings[r][k], rings[r][k2], rings[r + 1][k2], rings[r + 1][k]))
    top = bm.verts.new((0, RINGS[-1][3], RINGS[-1][0] + 0.004))
    bot = bm.verts.new((0, RINGS[0][3], -0.002))
    for k in range(n):
        k2 = (k + 1) % n
        bm.faces.new((rings[-1][k], rings[-1][k2], top))
        bm.faces.new((rings[0][k2], rings[0][k], bot))
    bm.normal_update()
    for f in bm.faces:
        n_ = f.normal
        front = n_.y < -0.3 and abs(n_.z) < 0.85
        f.material_index = 0 if front else 1
        for l in f.loops:
            l[uvl].uv = _uv_front(l.vert.co) if front else _uv_side(l.vert.co)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(photo_mat(f'{name}_front', front_path))
    o.data.materials.append(photo_mat(f'{name}_side', side_path))
    for p in o.data.polygons:
        p.use_smooth = True
    o.parent = parent
    return o
