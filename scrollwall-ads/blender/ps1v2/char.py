"""Low-poly, realistically proportioned PS1-style character ("the scroller").

Body parts are lofted from cross-section rings (8-12 sides) with cylindrical
UVs, so painted textures wrap around them like in late-90s games. Parts are
rigid and parented to joint empties; posing = rotating joints.
Front faces -Y, Z up, metres. Stands ~1.76 m.
"""
import math
import os

import bmesh
import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, '..', 'assets', 'ps1v2')
_img, _mat = {}, {}


def img(name):
    if name not in _img:
        _img[name] = bpy.data.images.load(os.path.join(TEX, f'{name}.png'))
    return _img[name]


def tmat(name, rough=0.8, emission=0.0, alpha=False, interp='Closest', sheen=0.0):
    key = (name, emission, alpha)
    if key in _mat:
        return _mat[key]
    m = bpy.data.materials.new(f'm_{name}')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = img(name)
    t.interpolation = interp
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.2
    b.inputs['Sheen Weight'].default_value = sheen
    if emission:
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = emission
    if alpha:
        nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    m['tex'] = t.name
    _mat[key] = m
    return m


def cmat(name, rgb, rough=0.6, emission=0.0, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emission:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emission
    return m


def link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def joint(name, loc, par=None):
    e = link(bpy.data.objects.new(name, None))
    e.location = loc
    e.parent = par
    e.rotation_mode = 'XYZ'
    return e


def loft(name, rings, mat, n=8, par=None, smooth=True, cap_top=True, cap_bottom=True, u_scale=1.0):
    """rings: list of (z, width, depth, y_offset, squareness, v). Front = -Y = u 0.5."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    vrings = []
    for (z, w, dpt, yo, sq, v) in rings:
        ring = []
        for k in range(n):
            th = 2 * math.pi * k / n
            s, c = math.sin(th), math.cos(th)
            p = 2.0 / sq
            x = (w / 2) * math.copysign(abs(s) ** p, s)
            y = -(dpt / 2) * math.copysign(abs(c) ** p, c) + yo
            ring.append(bm.verts.new((x, y, z)))
        vrings.append(ring)
    us = [((0.5 + k / n) % 1.0) for k in range(n)]
    for r in range(len(rings) - 1):
        for k in range(n):
            k2 = (k + 1) % n
            f = bm.faces.new((vrings[r][k], vrings[r][k2], vrings[r + 1][k2], vrings[r + 1][k]))
            u1, u2 = us[k], us[k2]
            if u2 < u1:
                u2 += 1.0
            v1, v2 = rings[r][5], rings[r + 1][5]
            for l, (u, v) in zip(f.loops, [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]):
                l[uvl].uv = (u * u_scale, v)
    for idx, cap in ((0, cap_bottom), (len(rings) - 1, cap_top)):
        if not cap:
            continue
        z, w, dpt, yo, sq, v = rings[idx]
        cen = bm.verts.new((0, yo, z))
        for k in range(n):
            k2 = (k + 1) % n
            vs = (vrings[idx][k], vrings[idx][k2], cen) if idx else (vrings[idx][k2], vrings[idx][k], cen)
            f = bm.faces.new(vs)
            for l in f.loops:
                l[uvl].uv = (0.5, v)
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    o.data.materials.append(mat)
    for poly in o.data.polygons:
        poly.use_smooth = smooth
    o.parent = par
    return o


def blockmesh(name, size, loc, mat, par=None, rot=(0, 0, 0)):
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    o.data.materials.append(mat)
    o.location = loc
    o.rotation_euler = rot
    o.parent = par
    return o


class Scroller:
    HEADS = ['glazed', 'neutral', 'shock', 'focus', 'smile', 'blink', 'glazed_blink']

    def __init__(self, loc=(0, 0, 0), rotz=0.0, photo=True):
        hood, sleeve, pants = tmat('hoodie', sheen=0.4), tmat('sleeve', sheen=0.4), tmat('pants', sheen=0.2)
        skin, sock = tmat('hand', rough=0.6), tmat('socks')
        self.root = joint('scroller', loc)
        self.root.rotation_euler = (0, 0, rotz)
        self.pelvis = joint('pelvis', (0, 0, 0.95), self.root)
        # torso: oversized hoodie (loose, boxy)
        loft('torso', [
            (-0.05, 0.33, 0.23, 0.0, 2.4, 0.0),
            (0.05, 0.34, 0.235, 0.0, 2.4, 0.12),
            (0.2, 0.355, 0.245, -0.005, 2.4, 0.35),
            (0.34, 0.38, 0.245, -0.01, 2.5, 0.6),
            (0.44, 0.39, 0.225, 0.0, 2.5, 0.82),
            (0.5, 0.3, 0.19, 0.01, 2.3, 0.95),
            (0.54, 0.15, 0.14, 0.01, 2.0, 1.0),
        ], hood, n=10, par=self.pelvis)
        # bunched hood behind the neck
        loft('hood', [
            (0.5, 0.3, 0.12, 0.1, 2.2, 0.9), (0.58, 0.32, 0.16, 0.1, 2.2, 0.95), (0.64, 0.26, 0.14, 0.09, 2.0, 1.0),
        ], sleeve, n=8, par=self.pelvis)
        # neck + head
        self.neck = joint('neck', (0, 0.01, 0.52), self.pelvis)
        loft('neck_m', [(0.0, 0.105, 0.105, 0.0, 2.0, 0.85), (0.07, 0.095, 0.095, 0.0, 2.0, 0.85)], cmat('neck_skin', (0.62, 0.42, 0.32), 0.6), n=8, par=self.neck)
        self.head_j = joint('head', (0, 0.0, 0.06), self.neck)
        self.heads = {}
        if photo:
            import photohead
            src = os.path.join(TEX, 'face_src')
            for hname in ('neutral', 'glazed'):
                h = photohead.build(f'phead_{hname}', os.path.join(src, f'front_{hname}.png'), os.path.join(src, 'side.png'),
                                    parent=self.head_j)
                h.hide_render = True
                self.heads[hname] = h
            for s in (-1, 1):
                blockmesh(f'airpod{s}', (0.008, 0.01, 0.018), (s * 0.084, 0.03, 0.105), cmat(f'pod{s}', (0.95, 0.95, 0.95), 0.2),
                          par=self.head_j)
        else:
            for hname in self.HEADS:
                h = loft(f'head_{hname}', [
                    (0.0, 0.1, 0.1, 0.0, 2.0, 0.02),
                    (0.03, 0.12, 0.13, -0.015, 2.2, 0.12),
                    (0.06, 0.135, 0.165, -0.02, 2.4, 0.2),
                    (0.11, 0.152, 0.19, -0.012, 2.6, 0.36),
                    (0.16, 0.16, 0.2, -0.004, 2.6, 0.53),
                    (0.21, 0.162, 0.2, 0.0, 2.5, 0.68),
                    (0.25, 0.15, 0.185, 0.004, 2.3, 0.8),
                    (0.28, 0.115, 0.15, 0.006, 2.0, 0.9),
                    (0.295, 0.06, 0.08, 0.006, 2.0, 0.97),
                ], tmat(f'head_{hname}', rough=0.6), n=12, par=self.head_j)
                h.hide_render = True
                self.heads[hname] = h
            # nose wedge + ears + hair volume + AirPods
            nose = loft('nose', [(0.11, 0.035, 0.02, -0.098, 2.0, 0.45), (0.15, 0.022, 0.012, -0.1, 2.0, 0.45)], skin, n=6, par=self.head_j)
            for s in (-1, 1):
                ear = blockmesh(f'ear{s}', (0.02, 0.04, 0.06), (s * 0.08, 0.005, 0.15), skin, par=self.head_j)
                pod = blockmesh(f'airpod{s}', (0.012, 0.012, 0.03), (s * 0.088, -0.005, 0.135), cmat(f'pod{s}', (0.95, 0.95, 0.95), 0.2),
                                par=self.head_j)
            hair = tmat('hair')
            loft('hair_vol', [
                (0.2, 0.17, 0.21, 0.01, 2.4, 0.0), (0.25, 0.175, 0.215, 0.012, 2.3, 0.4),
                (0.29, 0.15, 0.19, 0.012, 2.1, 0.7), (0.32, 0.09, 0.12, 0.015, 2.0, 1.0),
            ], hair, n=12, par=self.head_j, cap_bottom=False)
            for i, (x, rx, rz) in enumerate([(-0.05, 0.9, 0.2), (0.0, 1.1, -0.1), (0.05, 0.8, 0.3), (0.03, 0.6, -0.5), (-0.07, 0.5, 0.6)]):
                t = blockmesh(f'tuft{i}', (0.045, 0.02, 0.07), (x, -0.08, 0.27), hair, par=self.head_j, rot=(rx, 0, rz))
        # arms
        self.sh, self.el, self.wr = {}, {}, {}
        for s in (-1, 1):
            sh = joint(f'sh{s}', (s * 0.2, 0.0, 0.45), self.pelvis)
            loft(f'uarm{s}', [(0.03, 0.13, 0.13, 0, 2.2, 1.0), (-0.15, 0.115, 0.115, 0, 2.2, 0.55), (-0.29, 0.1, 0.1, 0, 2.2, 0.1)],
                 sleeve, n=8, par=sh)
            el = joint(f'el{s}', (0, 0, -0.29), sh)
            loft(f'farm{s}', [(0.02, 0.1, 0.1, 0, 2.2, 1.0), (-0.2, 0.085, 0.085, 0, 2.2, 0.2), (-0.25, 0.09, 0.09, 0, 2.2, 0.05)],
                 sleeve, n=8, par=el)
            wr = joint(f'wr{s}', (0, 0, -0.25), el)
            loft(f'hand{s}', [(0.0, 0.065, 0.04, 0, 2.4, 1.0), (-0.07, 0.085, 0.035, 0, 2.6, 0.55), (-0.15, 0.075, 0.03, 0, 2.4, 0.05)],
                 skin, n=8, par=wr)
            th = joint(f'thumb{s}', (s * -0.035, -0.015, -0.03), wr)
            loft(f'thumb_m{s}', [(0.0, 0.028, 0.028, 0, 2.0, 0.5), (-0.07, 0.02, 0.02, 0, 2.0, 0.5)], skin, n=6, par=th)
            th.rotation_euler = (0.3, 0, s * -0.6)
            self.sh[s], self.el[s], self.wr[s] = sh, el, wr
        # legs
        self.hip, self.knee, self.ankle = {}, {}, {}
        for s in (-1, 1):
            hp = joint(f'hip{s}', (s * 0.1, 0.0, -0.02), self.pelvis)
            loft(f'thigh{s}', [(0.03, 0.18, 0.19, 0, 2.2, 1.0), (-0.22, 0.15, 0.155, 0, 2.2, 0.55), (-0.44, 0.12, 0.12, 0, 2.2, 0.05)],
                 pants, n=8, par=hp)
            kn = joint(f'knee{s}', (0, 0, -0.44), hp)
            loft(f'shin{s}', [(0.02, 0.12, 0.12, 0, 2.2, 1.0), (-0.2, 0.1, 0.105, 0, 2.2, 0.5), (-0.42, 0.09, 0.09, 0, 2.2, 0.05)],
                 pants, n=8, par=kn)
            an = joint(f'ankle{s}', (0, 0, -0.43), kn)
            loft(f'foot{s}', [(0.0, 0.08, 0.1, 0.0, 2.2, 1.0), (-0.05, 0.09, 0.2, -0.05, 2.6, 0.6), (-0.07, 0.09, 0.24, -0.06, 2.8, 0.1)],
                 sock, n=8, par=an)
            self.hip[s], self.knee[s], self.ankle[s] = hp, kn, an
        # phone (slightly oversized), held in the left hand
        self.phone = joint('phone', (0.0, -0.03, -0.11), self.wr[-1])
        blockmesh('phone_body', (0.095, 0.011, 0.19), (0, 0, 0), tmat('phone_back', rough=0.3), par=self.phone)
        self.screen_mat = bpy.data.materials.new('m_screen')
        self.screen_mat.use_nodes = True
        nt = self.screen_mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        self.screen_em = nt.nodes.new('ShaderNodeEmission')
        self.screen_tex = nt.nodes.new('ShaderNodeTexImage')
        self.screen_tex.interpolation = 'Closest'
        nt.links.new(self.screen_tex.outputs['Color'], self.screen_em.inputs['Color'])
        self.screen_em.inputs['Strength'].default_value = 2.0
        nt.links.new(self.screen_em.outputs['Emission'], out.inputs['Surface'])
        bpy.ops.mesh.primitive_plane_add(size=1)
        scr = bpy.context.active_object
        scr.name = 'screen'
        scr.scale = (0.088, 0.18, 1)
        scr.rotation_euler = (math.pi / 2, 0, math.pi)  # faces +Y (toward his face)
        scr.location = (0, 0.0058, 0)
        scr.parent = self.phone
        scr.data.materials.append(self.screen_mat)
        self.screen = scr
        sl = bpy.data.lights.new('screen_light', 'AREA')
        sl.energy = 3.0
        sl.size = 0.15
        sl.color = (0.7, 0.82, 1.0)
        self.screen_light = link(bpy.data.objects.new('screen_light', sl))
        self.screen_light.parent = self.phone
        self.screen_light.location = (0, 0.03, 0)
        self.screen_light.rotation_euler = (math.pi / 2, 0, 0)
        self.set_head('neutral')
        self.pose_stand()

    def set_head(self, name):
        if name not in self.heads:
            name = 'glazed' if 'glazed' in name else 'neutral'
        for k, h in self.heads.items():
            h.hide_render = k != name

    def set_screen(self, image, strength=2.0):
        if image is not None:
            self.screen_tex.image = image
        self.screen_em.inputs['Strength'].default_value = strength
        self.screen_light.data.energy = 3.0 * strength / 2.0

    def pose_stand(self):
        for s in (-1, 1):
            self.sh[s].rotation_euler = (0.05, s * 0.0, s * 0.12)
            self.el[s].rotation_euler = (-0.25, 0, 0)
            self.wr[s].rotation_euler = (0, 0, 0)
            self.hip[s].rotation_euler = (0, 0, s * 0.03)
            self.knee[s].rotation_euler = (0, 0, 0)
            self.ankle[s].rotation_euler = (0, 0, 0)
        self.neck.rotation_euler = (0, 0, 0)
        self.head_j.rotation_euler = (0, 0, 0)
        self.pelvis.location = (0, 0, 0.95)
        self.pelvis.rotation_euler = (0, 0, 0)

    def pose_phone(self, scroll=0.0, head_down=0.35):
        """Standing, phone held up in the left hand; right thumb/arm scrolls."""
        self.pose_stand()
        self.sh[-1].rotation_euler = (-0.55, 0, -0.25)
        self.el[-1].rotation_euler = (-1.55, 0, 0.35)
        self.wr[-1].rotation_euler = (0.2, 0, 0.0)
        self.sh[1].rotation_euler = (-0.5 - scroll * 0.25, 0, 0.35)
        self.el[1].rotation_euler = (-1.5 - scroll * 0.2, 0, -0.5)
        self.wr[1].rotation_euler = (0.3, 0, 0)
        self.neck.rotation_euler = (head_down * 0.5, 0, 0)
        self.head_j.rotation_euler = (head_down * 0.6, 0, 0)

    def pose_bed(self, scroll=0.0, head_down=0.3, lean=-0.35):
        """Sitting up in bed against the headboard, legs out, phone up."""
        self.pose_phone(scroll, head_down)
        self.pelvis.rotation_euler = (lean, 0, 0)
        for s in (-1, 1):
            self.hip[s].rotation_euler = (math.pi / 2 + lean * -1 - 0.05, 0, s * 0.06)
            self.knee[s].rotation_euler = (-0.25, 0, 0)
            self.ankle[s].rotation_euler = (0.3, 0, 0)
