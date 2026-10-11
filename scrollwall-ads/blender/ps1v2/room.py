"""The bedroom set: a lived-in Gen Z room on a sunny afternoon, low-poly with
photo-like textures. Room: x -1.8..1.8, y -1.7..1.7 (back wall at +y), z 0..2.6.
Bed in the back-left, desk on the right wall, window with blinds on the left.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from char import cmat, link, tmat

R = random.Random(9)


def box(name, size, loc, mat, rot=(0, 0, 0), front=None, uv=(1.0, 1.0), par=None):
    """Box with each face UV'd 0..1 (textures stretch per face, PS1 style)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    bm.normal_update()
    for f in bm.faces:
        n = f.normal
        for l in f.loops:
            c = l.vert.co
            if abs(n.z) > 0.5:
                u, v = c.x / size[0] + 0.5, c.y / size[1] + 0.5
            elif abs(n.x) > 0.5:
                u, v = c.y / size[1] + 0.5, c.z / size[2] + 0.5
                if n.x < 0:
                    u = 1 - u
            else:
                u, v = c.x / size[0] + 0.5, c.z / size[2] + 0.5
                if n.y > 0:
                    u = 1 - u
            l[uvl].uv = (u * uv[0], v * uv[1])
        if front is not None and n.y < -0.5:
            f.material_index = 1
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    o.data.materials.append(mat)
    if front is not None:
        o.data.materials.append(front)
    o.location = loc
    o.rotation_euler = rot
    o.parent = par
    return o


def cyl(name, r, h, loc, mat, seg=10, rot=(0, 0, 0), r2=None, par=None, top_mat=None):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    bm.normal_update()
    for f in bm.faces:
        side = abs(f.normal.z) < 0.5
        for l in f.loops:
            c = l.vert.co
            if side:
                u = (math.atan2(c.y, c.x) / (2 * math.pi)) % 1.0
                l[uvl].uv = (u, c.z / h + 0.5)
            else:
                l[uvl].uv = (c.x / (2 * r) + 0.5, c.y / (2 * r) + 0.5)
        if top_mat is not None and not side and f.normal.z > 0:
            f.material_index = 1
    # fix the wrap seam
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    o.data.materials.append(mat)
    if top_mat is not None:
        o.data.materials.append(top_mat)
    for p in o.data.polygons:
        p.use_smooth = True
    o.location = loc
    o.rotation_euler = rot
    o.parent = par
    return o


def plane(name, w, h, loc, mat, rot=(math.pi / 2, 0, 0), par=None):
    """Vertical card facing -Y by default."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new((x * w / 2, y * h / 2, 0)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f = bm.faces.new(vs)
    for l, uv in zip(f.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        l[uvl].uv = uv
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    o.data.materials.append(mat)
    o.location = loc
    o.rotation_euler = rot
    o.parent = par
    return o


def lump(name, r, loc, mat, scale=(1, 1, 0.5), seed=0):
    """Irregular low-poly blob (clothes, bags)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=r, calc_uvs=False)
    rr = random.Random(seed)
    for v in bm.verts:
        v.co *= 1 + rr.uniform(-0.25, 0.25)
    for f in bm.faces:
        for l in f.loops:
            c = l.vert.co
            l[uvl].uv = (c.x / r * 0.5 + 0.5, c.y / r * 0.5 + 0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    o.data.materials.append(mat)
    o.location = loc
    o.scale = scale
    o.rotation_euler = (0, 0, rr.uniform(0, 3))
    return o


def draped(name, size, loc, mat, segs=(10, 12), droop=0.28, bumps=0.05, seed=0, top=(1.4, 1.5)):
    """A blanket/duvet: grid that sits on top and droops past the edges, with folds."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    nx, ny = segs
    rr = random.Random(seed)
    phase = [rr.uniform(0, 6) for _ in range(6)]
    verts = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = (i / nx - 0.5) * size[0]
            y = (j / ny - 0.5) * size[1]
            z = (math.sin(x * 7 + phase[0]) * math.cos(y * 5 + phase[1]) + math.sin(x * 13 + y * 4 + phase[2]) * 0.5) * bumps
            ox = max(0, abs(x) - top[0] / 2)
            oy = max(0, abs(y) - top[1] / 2)
            z -= (ox + oy) / max(1e-3, (size[0] - top[0]) / 2) * droop
            row.append(bm.verts.new((x, y, z)))
        verts.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
            for l, (a, b) in zip(f.loops, [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]):
                l[uvl].uv = (a / nx * 2, b / ny * 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = link(bpy.data.objects.new(name, me))
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    o.location = loc
    sol = o.modifiers.new('thick', 'SOLIDIFY')
    sol.thickness = 0.03
    return o


def emissive(name, rgb, strength):
    return cmat(name, rgb, 0.5, emission=strength)


# ===================================================================== build

def build(clock_hour=15.0):
    S = {}
    wall = tmat('surf_wall_plaster')
    # --- shell
    box('floor', (3.6, 3.4, 0.04), (0, 0, -0.02), tmat('surf_floor_wood'), uv=(3, 3))
    box('ceiling', (3.6, 3.4, 0.04), (0, 0, 2.62), tmat('surf_ceiling'), uv=(3, 3))
    box('wall_back', (3.6, 0.08, 2.6), (0, 1.74, 1.3), wall, uv=(3, 2))
    box('wall_right', (0.08, 3.4, 2.6), (1.84, 0, 1.3), wall, uv=(3, 2))
    # left wall with a window hole (window: y -0.55..0.65, z 0.95..2.05)
    wl = dict(x=-1.84, t=0.08)
    box('wall_l_a', (0.08, 1.15, 2.6), (wl['x'], -1.125, 1.3), wall, uv=(1, 2))
    box('wall_l_b', (0.08, 1.05, 2.6), (wl['x'], 1.175, 1.3), wall, uv=(1, 2))
    box('wall_l_c', (0.08, 1.2, 0.95), (wl['x'], 0.05, 0.475), wall)
    box('wall_l_d', (0.08, 1.2, 0.55), (wl['x'], 0.05, 2.325), wall)
    white = tmat('surf_plastic_white')
    for nm, sz, lc in [('sill', (0.22, 1.3, 0.04), (-1.74, 0.05, 0.95)), ('wf_t', (0.1, 1.24, 0.05), (-1.8, 0.05, 2.05)),
                       ('wf_l', (0.1, 0.05, 1.1), (-1.8, -0.55, 1.5)), ('wf_r', (0.1, 0.05, 1.1), (-1.8, 0.65, 1.5)),
                       ('wf_m', (0.06, 0.04, 1.1), (-1.82, 0.05, 1.5))]:
        box(nm, sz, lc, white)
    view = plane('window_view', 1.6, 1.6, (-2.6, 0.05, 1.5), tmat('window_view', emission=1.3), rot=(math.pi / 2, 0, -math.pi / 2))
    # blinds: slats tilted open so the sun comes through in stripes
    S['slats'] = []
    for i in range(18):
        sl = box(f'slat{i}', (0.06, 1.16, 0.006), (-1.74, 0.05, 2.0 - i * 0.058), white, rot=(0, math.radians(35), 0))
        S['slats'].append(sl)
    # plants on the sill
    for k, y in enumerate((-0.35, 0.45)):
        cyl(f'pot{k}', 0.06, 0.1, (-1.72, y, 1.02), cmat(f'potm{k}', (0.75, 0.42, 0.28), 0.7))
        lump(f'plant{k}', 0.09, (-1.72, y, 1.15), cmat(f'leaf{k}', (0.18, 0.4, 0.15), 0.7), scale=(1, 1, 1.2), seed=k + 30)

    # --- bed (back-left)
    bx, by = -0.85, 0.62
    dk = tmat('surf_wood_dark')
    box('bed_frame', (1.55, 2.12, 0.32), (bx, by, 0.2), dk)
    for dx in (-0.72, 0.72):
        for dy in (-1.0, 1.0):
            box('bed_leg', (0.07, 0.07, 0.06), (bx + dx, by + dy, 0.03), dk)
    box('mattress', (1.48, 2.04, 0.2), (bx, by, 0.45), tmat('surf_sheet'))
    box('headboard', (1.6, 0.08, 0.95), (bx, 1.68, 0.62), dk)
    pil = tmat('surf_pillow')
    lump('pillow_a', 0.3, (bx - 0.35, 1.38, 0.63), pil, scale=(1.15, 0.6, 0.35), seed=1)
    lump('pillow_b', 0.3, (bx + 0.33, 1.42, 0.63), pil, scale=(1.1, 0.55, 0.33), seed=2)
    S['duvet'] = draped('duvet', (1.9, 1.75), (bx, by - 0.28, 0.6), tmat('surf_duvet'), droop=0.33, bumps=0.045, seed=3,
                        top=(1.46, 1.55))
    lump('thrown_hoodie', 0.22, (bx + 0.45, by - 0.65, 0.66), tmat('surf_laundry_black'), scale=(1.3, 0.9, 0.3), seed=4)
    # fairy lights over the headboard (bloom later)
    S['fairy'] = []
    for i in range(16):
        t = i / 15
        x = bx - 0.85 + t * 1.7
        z = 1.55 - math.sin(t * math.pi) * 0.12 + math.sin(t * 9) * 0.02
        b = link(bpy.data.objects.new(f'fairy{i}', bpy.data.meshes.new(f'fairy{i}')))
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.016)
        bm.to_mesh(b.data)
        bm.free()
        b.data.materials.append(emissive('fairy_m', (1.0, 0.78, 0.45), 12))
        b.location = (x, 1.69, z)
        S['fairy'].append(b)
    # wall clock above the bed
    clock = link(bpy.data.objects.new('clock', None))
    clock.location = (bx, 1.69, 2.1)
    cyl('clock_rim', 0.17, 0.04, (0, 0, 0), cmat('clock_rimm', (0.12, 0.11, 0.14), 0.4), seg=16, rot=(math.pi / 2, 0, 0), par=clock)
    plane('clock_face', 0.31, 0.31, (0, -0.022, 0), tmat('clock_face', alpha=True), par=clock)
    hh = link(bpy.data.objects.new('clock_hour', None))
    hh.parent = clock
    hh.location = (0, -0.03, 0)
    box('hh_m', (0.014, 0.006, 0.08), (0, 0, 0.035), cmat('ink', (0.03, 0.03, 0.04), 0.5), par=hh)
    mh = link(bpy.data.objects.new('clock_min', None))
    mh.parent = clock
    mh.location = (0, -0.034, 0)
    box('mh_m', (0.01, 0.006, 0.12), (0, 0, 0.055), cmat('ink2', (0.03, 0.03, 0.04), 0.5), par=mh)
    hh.rotation_euler = (0, math.radians((clock_hour % 12) * 30), 0)
    mh.rotation_euler = (0, math.radians((clock_hour % 1) * 360), 0)
    S['clock'], S['clock_hour'], S['clock_min'] = clock, hh, mh

    # --- nightstand (right of bed)
    nx_, ny_ = 0.2, 1.45
    box('nightstand', (0.45, 0.4, 0.55), (nx_, ny_, 0.275), tmat('surf_wood_desk'))
    box('ns_drawer', (0.4, 0.01, 0.18), (nx_, ny_ - 0.205, 0.38), tmat('surf_wood_dark'))
    cyl('lamp_base', 0.07, 0.03, (nx_ + 0.1, ny_ + 0.06, 0.57), tmat('surf_metal'))
    cyl('lamp_pole', 0.012, 0.32, (nx_ + 0.1, ny_ + 0.06, 0.74), tmat('surf_metal'), seg=6)
    cyl('lamp_shade', 0.13, 0.17, (nx_ + 0.1, ny_ + 0.06, 0.95), emissive('shade', (1.0, 0.82, 0.6), 0.6), r2=0.08)
    can_m = tmat('can_volt')
    for i, (dx, dy, tip) in enumerate([(-0.12, -0.05, 0), (-0.04, -0.1, 0), (0.05, -0.12, 0)]):
        cyl(f'ns_can{i}', 0.033, 0.12, (nx_ + dx, ny_ + dy, 0.61), can_m, seg=10)
    cyl('glass', 0.035, 0.11, (nx_ - 0.15, ny_ + 0.1, 0.605), cmat('glass', (0.7, 0.8, 0.85), 0.05), seg=10)
    box('airpods_case', (0.05, 0.022, 0.06), (nx_ + 0.12, ny_ - 0.12, 0.58), tmat('surf_plastic_white'))
    # charger cable from the wall to the bed
    pts = [Vector((0.05, 1.7, 0.3)), Vector((0.0, 1.5, 0.05)), Vector((-0.2, 1.1, 0.02)), Vector((-0.12, 0.8, 0.3)),
           Vector((-0.25, 0.6, 0.57))]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        d = b - a
        c = cyl(f'cable{i}', 0.006, d.length, (a + b) / 2, cmat('cable', (0.92, 0.92, 0.92), 0.5), seg=5)
        c.rotation_mode = 'QUATERNION'
        c.rotation_quaternion = d.to_track_quat('Z', 'Y')

    # --- desk area (right wall)
    dx_, dy_ = 1.45, 0.45
    dw = tmat('surf_wood_desk')
    box('desk_top', (0.7, 1.45, 0.04), (dx_, dy_, 0.75), dw)
    for oy in (-0.68, 0.68):
        box('desk_side', (0.66, 0.04, 0.73), (dx_, dy_ + oy, 0.365), dw)
    # LED strip under the desk + behind the monitor (purple glow)
    box('led_desk', (0.02, 1.4, 0.01), (dx_ - 0.33, dy_, 0.725), emissive('led', (0.65, 0.3, 1.0), 25))
    box('led_back', (0.01, 0.9, 0.01), (1.8, dy_, 1.05), emissive('led2', (0.65, 0.3, 1.0), 25))
    # monitor on a stand
    box('mon_body', (0.05, 0.62, 0.36), (1.62, dy_ + 0.1, 1.15), tmat('surf_plastic_black'))
    plane('mon_screen', 0.58, 0.32, (1.594, dy_ + 0.1, 1.15), tmat('screen_monitor', emission=2.0), rot=(math.pi / 2, 0, -math.pi / 2))
    box('mon_stand', (0.04, 0.04, 0.2), (1.66, dy_ + 0.1, 0.87), tmat('surf_plastic_black'))
    box('mon_foot', (0.18, 0.22, 0.015), (1.64, dy_ + 0.1, 0.775), tmat('surf_plastic_black'))
    # open laptop
    box('lap_base', (0.24, 0.34, 0.015), (1.3, dy_ - 0.32, 0.778), tmat('surf_metal'))
    lid = box('lap_lid', (0.012, 0.34, 0.22), (1.42, dy_ - 0.32, 0.89), tmat('surf_metal'), rot=(0, math.radians(-12), 0))
    plane('lap_screen', 0.31, 0.19, (1.41, dy_ - 0.32, 0.89), tmat('screen_laptop', emission=1.6), rot=(math.pi / 2, math.radians(12), -math.pi / 2))
    box('keyboard', (0.15, 0.42, 0.015), (1.3, dy_ + 0.12, 0.778), tmat('surf_plastic_black'))
    box('mouse', (0.06, 0.035, 0.02), (1.28, dy_ + 0.45, 0.78), tmat('surf_plastic_black'))
    cyl('mug', 0.04, 0.1, (1.25, dy_ - 0.6, 0.82), cmat('mug', (0.85, 0.85, 0.82), 0.4), seg=10)
    for i in range(4):
        box(f'deskbook{i}', (0.22, 0.28, 0.035), (1.6, dy_ - 0.55, 0.79 + i * 0.037), tmat('surf_wood_dark' if i % 2 else 'surf_cardboard'),
            rot=(0, 0, R.uniform(-0.2, 0.2)))
    lump('headphones', 0.08, (1.55, dy_ + 0.6, 0.8), tmat('surf_plastic_black'), scale=(1, 1, 0.5), seed=7)
    # desk lamp
    cyl('dl_base', 0.06, 0.02, (1.65, dy_ - 0.2, 0.78), tmat('surf_plastic_black'))
    box('dl_arm', (0.02, 0.02, 0.35), (1.6, dy_ - 0.2, 0.95), tmat('surf_plastic_black'), rot=(0, math.radians(-20), 0))
    cyl('dl_head', 0.06, 0.08, (1.5, dy_ - 0.2, 1.1), tmat('surf_plastic_black'), rot=(0, math.radians(60), 0), r2=0.03)
    # gaming chair
    ch = tmat('surf_plastic_black')
    box('chair_seat', (0.5, 0.5, 0.08), (0.95, dy_, 0.48), ch)
    box('chair_back', (0.08, 0.5, 0.7), (0.66, dy_, 0.9), ch, rot=(0, math.radians(-8), 0))
    box('chair_stripe', (0.085, 0.12, 0.6), (0.66, dy_, 0.92), cmat('chair_red', (0.7, 0.12, 0.15), 0.5), rot=(0, math.radians(-8), 0))
    cyl('chair_pole', 0.03, 0.38, (0.95, dy_, 0.25), tmat('surf_metal'), seg=6)
    for k in range(5):
        a = k / 5 * math.tau
        box(f'chair_leg{k}', (0.3, 0.04, 0.03), (0.95 + math.cos(a) * 0.15, dy_ + math.sin(a) * 0.15, 0.05), ch, rot=(0, 0, a))
    # shelf + books + figurines above the desk
    box('shelf', (0.25, 1.1, 0.03), (1.7, dy_, 1.65), dw)
    box('shelf_books', (0.2, 0.7, 0.24), (1.7, dy_ - 0.18, 1.79), tmat('surf_wood_dark'), front=None)
    sp = plane('spines', 0.7, 0.24, (1.595, dy_ - 0.18, 1.79), tmat('spines'), rot=(math.pi / 2, 0, -math.pi / 2))
    for k in range(3):
        lump(f'figure{k}', 0.04, (1.7, dy_ + 0.25 + k * 0.1, 1.71), cmat(f'fig{k}', [(0.9, 0.3, 0.3), (0.3, 0.6, 0.9), (0.95, 0.8, 0.3)][k], 0.4),
             scale=(0.8, 0.8, 1.5), seed=10 + k)
    # cork board with photos + sticky notes
    box('cork', (0.03, 0.7, 0.5), (1.8, dy_ + 0.05, 2.1), tmat('surf_cork'))
    for k in range(4):
        plane(f'photo{k}', 0.1, 0.13, (1.78, dy_ - 0.2 + k * 0.15, 2.15 + (k % 2) * 0.1), tmat(f'photo_{k}'),
              rot=(math.pi / 2, R.uniform(-0.15, 0.15), -math.pi / 2))
    for k in range(5):
        plane(f'sticky{k}', 0.07, 0.07, (1.78, dy_ - 0.25 + k * 0.13, 1.95), tmat(f'sticky_{k % 4}'), rot=(math.pi / 2, R.uniform(-0.2, 0.2), -math.pi / 2))
    # posters on the back wall
    plane('poster_movie', 0.5, 0.75, (0.75, 1.695, 1.6), tmat('poster_movie'))
    plane('poster_game', 0.42, 0.56, (1.3, 1.695, 1.75), tmat('poster_game'))
    plane('poster_band', 0.42, 0.56, (-1.55, -0.6, 1.6), tmat('poster_band'), rot=(math.pi / 2, 0, -math.pi / 2))

    # purple LED strip along the ceiling edge (back + right walls)
    box('led_ceiling_b', (3.5, 0.02, 0.02), (0, 1.68, 2.56), emissive('ledc', (0.6, 0.3, 1.0), 12))
    box('led_ceiling_r', (0.02, 3.3, 0.02), (1.78, 0, 2.56), emissive('ledc2', (0.6, 0.3, 1.0), 12))

    # --- floor clutter
    box('rug', (1.6, 1.1, 0.01), (0.25, -0.55, 0.005), tmat('surf_rug'))
    box('pizza_box', (0.4, 0.4, 0.04), (0.55, -0.75, 0.025), tmat('surf_cardboard'), rot=(0, 0, 0.5))
    plane('pizza_in', 0.38, 0.38, (0.55, -0.75, 0.047), tmat('pizza_inside'), rot=(0, 0, 0.5))
    lidp = box('pizza_lid', (0.4, 0.4, 0.01), (0.65, -0.55, 0.2), tmat('surf_cardboard'), rot=(math.radians(70), 0, 0.5))
    plane('pizza_lid_top', 0.38, 0.38, (0.0, 0.0, 0.006), tmat('pizza_lid'), rot=(0, 0, 0), par=lidp)
    for k in range(5):
        lump(f'clothes{k}', 0.22, (-0.15 + R.uniform(-0.3, 0.3), -1.25 + R.uniform(-0.2, 0.2), 0.06),
             tmat(R.choice(['surf_laundry_blue', 'surf_laundry_white', 'surf_laundry_black'])), scale=(1.4, 1, 0.35), seed=20 + k)
    for s in (-1, 1):
        box(f'sneaker{s}', (0.11, 0.3, 0.1), (1.0 + s * 0.08, -1.2, 0.05), tmat('sneaker'), rot=(0, 0, 0.3 + s * 0.2))
    box('backpack', (0.32, 0.18, 0.42), (1.55, -0.6, 0.21), cmat('pack', (0.18, 0.22, 0.32), 0.7), rot=(0, 0, -0.4))
    cyl('basket', 0.22, 0.45, (-1.4, -1.2, 0.225), cmat('basket', (0.85, 0.85, 0.82), 0.7), seg=10, r2=0.25)
    lump('basket_overflow', 0.25, (-1.4, -1.2, 0.47), tmat('surf_laundry_white'), scale=(1, 1, 0.5), seed=30)
    for k in range(3):
        cyl(f'floor_can{k}', 0.033, 0.12, (0.0 + k * 0.3, -0.25 - k * 0.1, 0.033), can_m, seg=10,
            rot=(math.pi / 2, 0, R.uniform(0, 3)))
    box('controller', (0.15, 0.1, 0.04), (0.3, -0.1, 0.02), tmat('surf_plastic_black'), rot=(0, 0, 0.7))
    # door on the right wall, hoodie hanging on it
    box('door', (0.05, 0.85, 2.05), (1.8, -1.15, 1.025), tmat('surf_wood_desk'))
    cyl('door_knob', 0.03, 0.06, (1.76, -0.82, 1.0), tmat('surf_metal'), rot=(0, math.pi / 2, 0), seg=8)
    lump('hanging_hoodie', 0.25, (1.73, -1.3, 1.55), tmat('surf_laundry_blue'), scale=(0.4, 1, 1.6), seed=40)
    return S


def lights(hour=15.0):
    """Afternoon sun through the blinds + practical lights."""
    sd = bpy.data.lights.new('sun', 'SUN')
    sd.energy = 11.0
    sd.color = (1.0, 0.86, 0.66)
    sd.angle = math.radians(1.5)
    sun = link(bpy.data.objects.new('sun', sd))
    d = Vector((1.0, 0.25, -0.75)).normalized()
    sun.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    # sky light bleeding in from the window
    a = bpy.data.lights.new('window_fill', 'AREA')
    a.energy = 25
    a.size = 1.2
    a.color = (0.75, 0.85, 1.0)
    wf = link(bpy.data.objects.new('window_fill', a))
    wf.location = (-1.6, 0.05, 1.5)
    wf.rotation_euler = Vector((1, 0, -0.2)).to_track_quat('-Z', 'Y').to_euler()
    # LED glow
    for nm, loc, rot in [('led_glow_b', (0, 1.5, 2.45), (1, 0, 0)), ('led_glow_r', (1.6, 0, 2.45), (0, 0, 0))]:
        l = bpy.data.lights.new(nm, 'AREA')
        l.energy = 6
        l.size = 2.5
        l.color = (0.6, 0.35, 1.0)
        lo = link(bpy.data.objects.new(nm, l))
        lo.location = loc
        lo.rotation_euler = (0.6, 0, 0) if 'b' in nm else (0, -0.6, 0)
    # monitor glow
    m = bpy.data.lights.new('mon_glow', 'AREA')
    m.energy = 12
    m.size = 0.6
    m.color = (0.6, 0.8, 1.0)
    mo = link(bpy.data.objects.new('mon_glow', m))
    mo.location = (1.5, 0.55, 1.15)
    mo.rotation_euler = (0, math.pi / 2, 0)
    return sun
