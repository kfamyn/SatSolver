"""PS1-style scene: Doug's sunny, messy bedroom, low-poly Doug, giant phone.

Low-poly primitives + tiny pixel textures with 'Closest' filtering. Front of
characters faces -Y, Z up, metres.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, '..', 'assets', 'ps1')

_imgs = {}
_mats = {}


def img(name):
    if name not in _imgs:
        _imgs[name] = bpy.data.images.load(os.path.join(TEX, f'{name}.png'))
    return _imgs[name]


def tmat(name, emission=0.0, alpha=False, rough=0.85, tint=None):
    """Material from a pixel texture, nearest-neighbour sampled."""
    key = (name, emission, alpha, tint)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(f'm_{name}')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = img(name)
    t.interpolation = 'Closest'
    col = t.outputs['Color']
    if tint:
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1
        nt.links.new(col, mix.inputs['A'])
        mix.inputs['B'].default_value = (*tint, 1)
        col = mix.outputs['Result']
    nt.links.new(col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.15
    if emission:
        nt.links.new(col, b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = emission
    if alpha:
        nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    m['tex_node'] = t.name
    _mats[key] = m
    return m


def cmat(name, rgb, emission=0.0, rough=0.8, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Alpha'].default_value = alpha
    if emission:
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = emission
    return m


def link(o):
    bpy.context.scene.collection.objects.link(o)
    return o


def empty(name, loc=(0, 0, 0), par=None):
    e = link(bpy.data.objects.new(name, None))
    e.location = loc
    e.parent = par
    return e


def _obj(name, bm, mats, loc, rot, par, smooth):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    for m in mats:
        o.data.materials.append(m)
    for p in o.data.polygons:
        p.use_smooth = smooth
    o.location = loc
    o.rotation_euler = rot
    o.parent = par
    return o


def box(name, size, loc=(0, 0, 0), mat=None, rot=(0, 0, 0), par=None, front=None, smooth=False, uv_scale=1.0):
    """Box with per-face UVs. `front` = material for the -Y face (e.g. a poster)."""
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    uv = bm.loops.layers.uv.active
    # re-UV each face to 0..1 (stretched texture per face, very PS1)
    for f in bm.faces:
        n = f.normal
        for l in f.loops:
            co = l.vert.co
            if abs(n.z) > 0.5:
                u, v = co.x / size[0] + 0.5, co.y / size[1] + 0.5
            elif abs(n.x) > 0.5:
                u, v = co.y / size[1] + 0.5, co.z / size[2] + 0.5
            else:
                u, v = co.x / size[0] + 0.5, co.z / size[2] + 0.5
            if n.y > 0.5 or n.x < -0.5:
                u = 1 - u
            l[uv].uv = (u * uv_scale, v * uv_scale)
        if front is not None and n.y < -0.5:
            f.material_index = 1
    mats = [mat] + ([front] if front is not None else [])
    return _obj(name, bm, mats, loc, rot, par, smooth)


def ball(name, r, loc=(0, 0, 0), mat=None, seg=8, rings=6, scale=(1, 1, 1), par=None, smooth=True, rot=(0, 0, 0)):
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r, calc_uvs=True)
    o = _obj(name, bm, [mat] if mat else [], loc, rot, par, smooth)
    o.scale = scale
    return o


def cyl(name, r, depth, loc=(0, 0, 0), mat=None, seg=8, rot=(0, 0, 0), par=None, r2=None, smooth=True):
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth, calc_uvs=True)
    return _obj(name, bm, [mat] if mat else [], loc, rot, par, smooth)


def plane(name, w, h, loc=(0, 0, 0), mat=None, rot=(math.pi / 2, 0, 0), par=None):
    """Vertical plane facing -Y by default (rot x=90°)."""
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True)
    for v in bm.verts:
        v.co.x *= w
        v.co.y *= h
    return _obj(name, bm, [mat] if mat else [], loc, rot, par, False)


# =================================================================== room

def room():
    R = random.Random(5)
    wall = tmat('wallpaper')
    # floor + rug
    box('floor', (5, 5, 0.02), (0, 0, -0.01), tmat('floor'), uv_scale=1)
    box('rug', (1.6, 1.1, 0.01), (0.2, -0.75, 0.005), tmat('rug'))
    # walls (back, left, right)
    box('wall_back', (5, 0.05, 3), (0, 1.6, 1.5), wall)
    box('wall_left', (0.05, 5, 3), (-1.9, 0, 1.5), wall)
    box('wall_right', (0.05, 5, 3), (2.0, 0, 1.5), wall)
    box('skirting', (5, 0.06, 0.1), (0, 1.56, 0.05), tmat('white_plastic'))

    # bed against the back wall
    dark = tmat('wood_dark')
    box('bed_frame', (1.3, 2.0, 0.32), (-0.55, 0.55, 0.16), dark)
    box('mattress', (1.24, 1.94, 0.18), (-0.55, 0.55, 0.41), tmat('sheet'), smooth=False)
    box('headboard', (1.36, 0.08, 0.85), (-0.55, 1.53, 0.55), dark)
    box('pillow', (0.7, 0.32, 0.12), (-0.55, 1.28, 0.56), tmat('pillow'), rot=(0.25, 0, 0))
    box('blanket', (1.3, 1.2, 0.12), (-0.55, 0.1, 0.55), tmat('blanket'), rot=(0, 0.03, 0))
    box('blanket_fold', (1.3, 0.25, 0.09), (-0.55, 0.62, 0.58), tmat('blanket'), rot=(0.2, 0, 0))

    # nightstand with lamp, cans
    box('nightstand', (0.45, 0.4, 0.5), (-1.55, 1.25, 0.25), dark)
    cyl('lamp_base', 0.07, 0.04, (-1.6, 1.3, 0.52), tmat('metal'))
    cyl('lamp_pole', 0.015, 0.3, (-1.6, 1.3, 0.69), tmat('metal'))
    cyl('lamp_shade', 0.14, 0.18, (-1.6, 1.3, 0.88), cmat('shade', (1.0, 0.75, 0.45), emission=0.0), r2=0.08)
    for i in range(3):
        cyl(f'can{i}', 0.035, 0.12, (-1.45 + i * 0.08, 1.15 - i * 0.03, 0.56), tmat('can'), seg=8)

    # big wall clock above the bed
    clock = empty('clock', (-0.55, 1.57, 1.75))
    cyl('clock_rim', 0.26, 0.05, (0, 0, 0), cmat('clock_rim', (0.15, 0.13, 0.2)), seg=16, rot=(math.pi / 2, 0, 0), par=clock)
    plane('clock_face', 0.48, 0.48, (0, -0.03, 0), tmat('clock_face', alpha=True), par=clock)
    hp = empty('clock_hour', (0, -0.04, 0), clock)
    box('clock_hour_hand', (0.025, 0.01, 0.13), (0, 0, 0.055), cmat('hand_ink', (0.05, 0.04, 0.07)), par=hp)
    mp = empty('clock_min', (0, -0.045, 0), clock)
    box('clock_min_hand', (0.018, 0.01, 0.19), (0, 0, 0.085), cmat('hand_ink2', (0.05, 0.04, 0.07)), par=mp)

    # posters + shelf with books
    for i, (k, x) in enumerate([('band', 0.5), ('game', 0.95), ('cat', -1.35)]):
        plane(f'poster_{k}', 0.32, 0.48, (x, 1.57, 1.55 + (i % 2) * 0.08), tmat(f'poster_{k}'), rot=(math.pi / 2, 0, R.uniform(-0.08, 0.08)))
    box('shelf', (0.8, 0.22, 0.03), (1.3, 1.45, 1.35), dark)
    box('shelf_books', (0.7, 0.18, 0.22), (1.28, 1.45, 1.48), tmat('wood_light'), front=tmat('books'))

    # window on the left wall
    win = empty('window', (-1.87, 0.0, 1.45))
    plane('window_sky', 1.0, 1.2, (0, 0, 0), tmat('sky_noon', emission=2.0), rot=(math.pi / 2, 0, -math.pi / 2), par=win)
    frame = tmat('white_plastic')
    for nm, sz, lc in [('wtop', (0.06, 1.12, 0.06), (0.02, 0, 0.62)), ('wbot', (0.12, 1.12, 0.06), (0.04, 0, -0.62)),
                       ('wl', (0.06, 0.06, 1.3), (0.02, -0.53, 0)), ('wr', (0.06, 0.06, 1.3), (0.02, 0.53, 0)),
                       ('wm', (0.04, 0.04, 1.2), (0.02, 0, 0)), ('wh', (0.04, 1.06, 0.04), (0.02, 0, 0))]:
        box(nm, sz, lc, frame, par=win)
    curtain = cmat('curtain', (0.55, 0.42, 0.85))
    for s in (-1, 1):
        box(f'curtain{s}', (0.05, 0.28, 1.5), (0.08, s * 0.72, 0.05), curtain, par=win)

    # desk + chair on the right
    light = tmat('wood_light')
    box('desk_top', (1.2, 0.6, 0.05), (1.4, 0.6, 0.75), light)
    for dx, dy in [(-0.55, -0.25), (0.55, -0.25), (-0.55, 0.25), (0.55, 0.25)]:
        box('desk_leg', (0.05, 0.05, 0.73), (1.4 + dx, 0.6 + dy, 0.365), light)
    box('desk_books', (0.32, 0.24, 0.16), (1.75, 0.75, 0.86), tmat('wood_light'), front=tmat('books'))
    cyl('desk_mug', 0.045, 0.1, (1.05, 0.55, 0.83), cmat('mug', (0.9, 0.35, 0.3)), seg=8)
    box('chair_seat', (0.45, 0.45, 0.06), (1.35, 0.05, 0.47), tmat('black_plastic'))
    box('chair_back', (0.45, 0.06, 0.5), (1.35, -0.18, 0.75), tmat('black_plastic'))
    cyl('chair_pole', 0.03, 0.42, (1.35, 0.05, 0.22), tmat('metal'))

    # floor clutter: pizza box, laundry, cans, backpack, trash
    box('pizza_box', (0.42, 0.42, 0.05), (0.55, -0.35, 0.03), tmat('wood_light'), rot=(0, 0, 0.4))
    plane('pizza_lid', 0.42, 0.42, (0.55, -0.35, 0.056), tmat('pizza'), rot=(0, 0, 0.4))
    for i in range(5):
        ball(f'laundry{i}', R.uniform(0.12, 0.2), (-1.25 + R.uniform(-0.25, 0.25), -0.75 + R.uniform(-0.3, 0.3), 0.05),
             tmat(R.choice(['cloth_a', 'cloth_b', 'cloth_c'])), seg=6, rings=4, scale=(1.3, 1, 0.45), smooth=False, rot=(0, 0, R.uniform(0, 3)))
    for i in range(3):
        cyl(f'floorcan{i}', 0.035, 0.12, (0.2 + i * 0.25, -1.1 + i * 0.12, 0.035), tmat('can'), seg=8, rot=(math.pi / 2, 0, R.uniform(0, 3)))
    box('backpack', (0.32, 0.18, 0.42), (1.7, -0.25, 0.21), cmat('backpack', (0.2, 0.45, 0.85)), rot=(0, 0, -0.5))
    cyl('trash', 0.15, 0.32, (1.75, 1.2, 0.16), tmat('metal'), seg=8, r2=0.17)
    for i in range(3):
        ball(f'paper{i}', 0.05, (1.55 + i * 0.1, 1.0 - i * 0.05, 0.05), tmat('white_plastic'), seg=5, rings=4, smooth=False)
    # plant in the corner
    cyl('pot', 0.13, 0.22, (-1.65, -1.4, 0.11), cmat('pot', (0.8, 0.45, 0.3)), seg=8)
    for k in range(3):
        plane(f'leaves{k}', 0.6, 0.7, (-1.65, -1.4, 0.55), tmat('leaves', alpha=True), rot=(math.pi / 2, 0, k * math.pi / 3))

    # fake god-ray shaft through the window (additive transparent quad, very PS1)
    shaft = plane('sunshaft', 1.0, 2.6, (-1.0, -0.1, 0.9), cmat('shaft', (1.0, 0.9, 0.6), emission=0.6, alpha=0.12),
                  rot=(math.radians(55), 0, math.radians(-70)))
    shaft.visible_shadow = False
    return clock


# =================================================================== Doug

class Doug:
    """Chunky box-headed Doug. Parts are parented through pivots so shots can
    pose him with a handful of numbers."""

    FACES = ['trance', 'trance_blink', 'surprised', 'normal', 'blink', 'focus', 'happy']

    def __init__(self, loc=(0, 0, 0)):
        hood = tmat('hoodie')
        hood_f = tmat('hoodie_front')
        skin = tmat('skin')
        self.root = empty('doug', loc)
        r = self.root
        self.torso = box('d_torso', (0.38, 0.26, 0.38), (0, 0, 0.32), hood, front=hood_f, par=r)
        box('d_hood', (0.32, 0.12, 0.12), (0, 0.13, 0.52), hood, par=r, rot=(0.3, 0, 0))
        # legs (visible when he sits at the desk)
        self.legs = []
        for s in (-1, 1):
            lg = box(f'd_thigh{s}', (0.13, 0.36, 0.13), (s * 0.1, -0.2, 0.1), tmat('pants'), par=r)
            sh = box(f'd_shin{s}', (0.12, 0.12, 0.34), (s * 0.1, -0.38, -0.1), tmat('pants'), par=r)
            ft = box(f'd_foot{s}', (0.13, 0.2, 0.08), (s * 0.1, -0.44, -0.27), tmat('white_plastic'), par=r)
            self.legs += [lg, sh, ft]
        # head on a neck pivot
        self.neck = empty('d_neck', (0, 0, 0.52), r)
        self.head = box('d_head', (0.34, 0.3, 0.32), (0, 0, 0.17), skin, par=self.neck, smooth=False)
        self.face_planes = {}
        for f in self.FACES:
            fp = plane(f'd_face_{f}', 0.33, 0.31, (0, -0.152, 0.16), tmat(f'face_{f}', alpha=True), par=self.neck)
            fp.hide_render = True
            self.face_planes[f] = fp
        # hair: a slab plus chunky tufts
        hair = tmat('hair')
        box('d_hair_top', (0.37, 0.33, 0.1), (0, 0.01, 0.35), hair, par=self.neck)
        box('d_hair_back', (0.37, 0.08, 0.26), (0, 0.15, 0.24), hair, par=self.neck)
        for i, (x, rz) in enumerate([(-0.12, 0.3), (0.0, -0.2), (0.12, 0.4), (-0.05, 0.9)]):
            box(f'd_tuft{i}', (0.1, 0.1, 0.08), (x, -0.13, 0.31), hair, par=self.neck, rot=(0.5, 0, rz))
        for s in (-1, 1):
            box(f'd_ear{s}', (0.04, 0.06, 0.08), (s * 0.18, 0, 0.15), skin, par=self.neck)
        # arms: shoulder pivot -> upper arm -> elbow pivot -> forearm -> hand
        self.sh, self.el, self.hand = {}, {}, {}
        for s in (-1, 1):
            sp = empty(f'd_sh{s}', (s * 0.24, 0, 0.46), r)
            box(f'd_upper{s}', (0.11, 0.11, 0.26), (0, 0, -0.12), hood, par=sp)
            ep = empty(f'd_el{s}', (0, 0, -0.25), sp)
            box(f'd_fore{s}', (0.1, 0.1, 0.24), (0, 0, -0.11), hood, par=ep)
            hd = box(f'd_hand{s}', (0.09, 0.07, 0.09), (0, 0, -0.26), skin, par=ep)
            self.sh[s], self.el[s], self.hand[s] = sp, ep, hd
        # the giant phone, held by the left hand
        self.phone = empty('d_phone', (0.0, -0.5, 0.56), r)
        box('d_phone_body', (0.24, 0.025, 0.46), (0, 0, 0), tmat('black_plastic'), par=self.phone)
        self.screen_mat = bpy.data.materials.new('m_screen')
        self.screen_mat.use_nodes = True
        nt = self.screen_mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        em = nt.nodes.new('ShaderNodeEmission')
        self.screen_tex = nt.nodes.new('ShaderNodeTexImage')
        self.screen_tex.interpolation = 'Closest'
        nt.links.new(self.screen_tex.outputs['Color'], em.inputs['Color'])
        em.inputs['Strength'].default_value = 1.6
        self.screen_em = em
        nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
        # screen faces +Y (toward Doug) by default; a second copy faces -Y for camera close-ups
        self.screen_back = plane('d_screen', 0.215, 0.43, (0, 0.0135, 0), self.screen_mat, par=self.phone, rot=(math.pi / 2, 0, math.pi))
        self.screen_front = plane('d_screen_f', 0.215, 0.43, (0, -0.0135, 0), self.screen_mat, par=self.phone)
        self.screen_front.hide_render = True
        self.screen_light = bpy.data.lights.new('d_screen_light', 'AREA')
        self.screen_light.energy = 6
        self.screen_light.size = 0.3
        self.screen_light.color = (0.75, 0.85, 1.0)
        sl = link(bpy.data.objects.new('d_screen_light', self.screen_light))
        sl.parent = self.phone
        sl.location = (0, 0.05, 0)
        sl.rotation_euler = (-math.pi / 2, 0, 0)
        self.set_face('normal')

    def set_face(self, name):
        for k, p in self.face_planes.items():
            p.hide_render = k != name

    def set_screen(self, image, strength=1.6):
        self.screen_tex.image = image
        self.screen_em.inputs['Strength'].default_value = strength
        self.screen_light.energy = 6 * strength / 1.6

    def aim_arm(self, side, target, elbow_down=1.0):
        """Two-bone arm: shoulder + elbow angles so the hand lands on `target`
        (Doug-local coords). Upper arm 0.25, forearm-to-hand 0.26."""
        from mathutils import Quaternion
        A, B = 0.25, 0.26
        sp = self.sh[side]
        d = Vector(target) - sp.location
        dist = max(0.05, min(d.length, A + B - 0.002))
        alpha = math.acos(max(-1, min(1, (A * A + dist * dist - B * B) / (2 * A * dist))))
        beta = math.pi - math.acos(max(-1, min(1, (A * A + B * B - dist * dist) / (2 * A * B))))
        base = d.to_track_quat('-Z', 'Y')
        sp.rotation_mode = 'QUATERNION'
        sp.rotation_quaternion = base @ Quaternion((1, 0, 0), -alpha * elbow_down)
        self.el[side].rotation_mode = 'XYZ'
        self.el[side].rotation_euler = (beta * elbow_down, 0, 0)

    def set_phone(self, loc=(0.0, -0.5, 0.56), tilt=0.35, roll=0.0):
        self.phone.location = loc
        self.phone.rotation_euler = (tilt, 0, roll)

    def pose_scroll(self, phase, head_pitch=0.45, sitting_bed=True, phone=(0.0, -0.5, 0.56)):
        """phase 0..1 of one whole-arm swipe: fast flick up, slow return."""
        swipe = (phase / 0.3) if phase < 0.3 else 1 - (phase - 0.3) / 0.7
        swipe = max(0, min(1, swipe))
        P = Vector(phone)
        self.set_phone(phone, tilt=0.35 + swipe * 0.04)
        self.aim_arm(-1, P + Vector((-0.13, 0.03, -0.1)))
        # the ENTIRE right arm sweeps up across the screen
        self.aim_arm(1, P + Vector((0.06 - swipe * 0.08, 0.1, -0.2 + swipe * 0.4)))
        self.neck.rotation_euler = (head_pitch, 0, 0)
        for o in self.legs:
            o.hide_render = sitting_bed
