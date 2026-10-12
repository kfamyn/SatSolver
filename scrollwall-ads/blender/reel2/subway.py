"""Subway car for Reel 2 ('what if scrolling cost money'), PS1 style:
CC0 Poly Haven photo textures on simple boxes, pixel ad posters, steel poles,
fluorescent strips, and a dark tunnel with lamps streaming past the windows.

Car footprint: x -5..5 (length), y -1.35..1.35, floor z 0, ceiling ~2.25.
Longitudinal benches along both walls, so passengers face each other.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
for p in ('../room2', '../ps1v2', '../mh'):
    sys.path.insert(0, os.path.join(HERE, p))
import char as C  # noqa: E402
from room import box, cyl, plane  # noqa: E402
from ps1fy import shrink_image  # noqa: E402
from room2 import photo  # noqa: E402

TEX = os.path.join(HERE, '..', 'assets', 'ps1', 'subway')
HALF_W, LEN, CEIL = 1.35, 5.0, 2.25
DOORS = (-2.6, 2.6)  # door centres (both sides)
DOOR_W = 1.3
WIN_Z = (0.95, 1.7)


def pix(name, emission=0.0, rough=0.7):
    """Material from one of our pixel textures (nearest filtering)."""
    m = bpy.data.materials.new(f'px_{name}')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(TEX, name + '.png'), check_existing=True)
    t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    if emission:
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = emission
    return m


def steel():
    return C.cmat('steel', (0.75, 0.76, 0.78), 0.28, metal=1.0)


def seat_spans():
    """x ranges of bench sections between the doors."""
    gaps = [(d - DOOR_W / 2 - 0.1, d + DOOR_W / 2 + 0.1) for d in DOORS]
    spans, x = [], -LEN + 0.15
    for a, b in gaps:
        spans.append((x, a))
        x = b
    spans.append((x, LEN - 0.15))
    return spans


def build():
    S = {}
    st = steel()
    floor = photo('rubber_tiles', (10, 3), 128, tint=(0.55, 0.58, 0.62))
    lower = photo('blue_metal_plate', (8, 1), 96, tint=(0.92, 0.93, 0.95))
    panel = C.cmat('panel_white', (0.86, 0.87, 0.86), 0.45)
    box('floor', (2 * LEN, 2 * HALF_W, 0.04), (0, 0, -0.02), floor)
    # ceiling: flat centre + angled coves (where the ads live)
    box('ceil_mid', (2 * LEN, 1.4, 0.04), (0, 0, CEIL + 0.02), panel)
    for sg in (-1, 1):
        box(f'cove{sg}', (2 * LEN, 0.62, 0.03), (0, sg * 0.98, CEIL - 0.14), panel, rot=(sg * math.radians(28), 0, 0))
    # fluorescent strips (two rows)
    lamp = C.cmat('fluoro', (0.92, 0.96, 1.0), 0.5, emission=6.0)
    for sg in (-1, 1):
        for i in range(8):
            box(f'fluoro{sg}_{i}', (1.0, 0.09, 0.03), (-4.4 + i * 1.25, sg * 0.45, CEIL - 0.005), lamp)
    # walls: lower panels, window band (pillars between windows), upper strip
    tunnel_glass = C.cmat('glass_dark', (0.02, 0.025, 0.03), 0.05)
    tunnel_glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.35
    for sg in (-1, 1):
        y = sg * HALF_W
        box(f'wall_low{sg}', (2 * LEN, 0.05, WIN_Z[0]), (0, y, WIN_Z[0] / 2), lower)
        box(f'wall_top{sg}', (2 * LEN, 0.05, CEIL - 0.25 - WIN_Z[1]), (0, y, (WIN_Z[1] + CEIL - 0.25) / 2), panel)
        # window glass sits slightly outside; we see the tunnel through it
        g = box(f'glass{sg}', (2 * LEN, 0.01, WIN_Z[1] - WIN_Z[0]), (0, y + sg * 0.06, sum(WIN_Z) / 2), tunnel_glass)
        g.visible_shadow = False
        x = -LEN
        while x <= LEN + 0.01:
            in_door = any(abs(x - d) < DOOR_W / 2 for d in DOORS)
            if not in_door:
                box(f'pillar{sg}_{x:.1f}', (0.16, 0.08, WIN_Z[1] - WIN_Z[0]), (x, y, sum(WIN_Z) / 2), panel)
            x += 1.1
        # doors: steel leaves with a window, yellow edge strips, sticker
        sticker = pix('door_sticker')
        for d in DOORS:
            for k in (-1, 1):
                cx = d + k * DOOR_W / 4
                box(f'door{sg}_{d}_{k}_lo', (DOOR_W / 2 - 0.01, 0.04, 0.95), (cx, y, 0.475), st)
                box(f'door{sg}_{d}_{k}_hi', (DOOR_W / 2 - 0.01, 0.04, CEIL - 0.25 - 1.75), (cx, y, (1.75 + CEIL - 0.25) / 2), st)
                for edge in (-1, 1):
                    box(f'door{sg}_{d}_{k}_e{edge}', (0.04, 0.045, 1.75), (cx + edge * (DOOR_W / 4 - 0.03), y, 0.875), st)
            box(f'doorstrip{sg}_{d}', (0.03, 0.05, 2.0), (d, y - sg * 0.005, 1.0), C.cmat('door_yellow', (1.0, 0.78, 0.05), 0.5))
            plane(f'sticker{sg}_{d}', 0.24, 0.12, (d - 0.3, y - sg * 0.03, 1.3), sticker,
                  rot=(math.pi / 2, 0, 0 if sg > 0 else math.pi))
    # end walls with the window to the next car
    for sx in (-1, 1):
        box(f'end{sx}', (0.05, 2 * HALF_W, CEIL), (sx * LEN, 0, CEIL / 2), lower)
        box(f'endwin{sx}', (0.06, 0.5, 0.7), (sx * (LEN - 0.01), 0, 1.4), tunnel_glass)
    # benches between the doors, both sides (blue fabric, steel base)
    fabric = photo('denim_fabric', (8, 1), 64, tint=(0.7, 0.8, 1.0))
    for sg in (-1, 1):
        for i, (a, b) in enumerate(seat_spans()):
            w, cx = b - a, (a + b) / 2
            box(f'seat{sg}_{i}', (w, 0.46, 0.09), (cx, sg * (HALF_W - 0.26), 0.42), fabric)
            box(f'back{sg}_{i}', (w, 0.08, 0.5), (cx, sg * (HALF_W - 0.06), 0.72), fabric, rot=(sg * math.radians(-8), 0, 0))
            box(f'base{sg}_{i}', (w, 0.36, 0.36), (cx, sg * (HALF_W - 0.22), 0.19), st)
            # armrest/stanchion at each end
            for ex in (a, b):
                cyl(f'arm{sg}_{i}_{ex:.1f}', 0.018, 0.55, (ex, sg * (HALF_W - 0.4), 0.72), st, seg=8)
    # vertical poles + overhead rails with straps
    for x in (-3.9, -1.3, 0.0, 1.3, 3.9):
        cyl(f'pole{x}', 0.02, CEIL, (x, 0, CEIL / 2), st, seg=8)
    strap = C.cmat('strap', (0.12, 0.12, 0.13), 0.6)
    for sg in (-1, 1):
        cyl(f'rail{sg}', 0.017, 2 * LEN - 0.4, (0, sg * 0.72, 1.98), st, seg=8, rot=(0, math.pi / 2, 0))
        for i in range(14):
            x = -4.5 + i * 0.7
            box(f'strap{sg}_{i}', (0.025, 0.012, 0.2), (x, sg * 0.72, 1.86), strap)
            bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.008, major_segments=8, minor_segments=4,
                                             location=(x, sg * 0.72, 1.71), rotation=(math.pi / 2, 0, 0))
            bpy.context.active_object.data.materials.append(strap)
    # ads + line map on the coves (facing the aisle)
    ads = ['ad_law', 'ad_topup', 'ad_thumb', 'ad_books', 'ad_law', 'ad_topup', 'ad_books', 'ad_thumb']
    k = 0
    for sg in (-1, 1):
        for i, x in enumerate((-4.1, -1.6, 1.6, 4.1)):
            name = ads[k % len(ads)]
            k += 1
            plane(f'ad{sg}_{i}', 0.9, 0.3, (x, sg * 1.02, CEIL - 0.16), pix(name, emission=0.4),
                  rot=(math.pi / 2 - sg * math.radians(62), 0, 0 if sg > 0 else math.pi))
        plane(f'linemap{sg}', 1.0, 0.125, (0, sg * (HALF_W - 0.04), 1.82), pix('linemap', emission=0.3),
              rot=(math.pi / 2, 0, 0 if sg > 0 else math.pi))
    # tunnel: dark walls outside + lamps that stream past (animated by set_tunnel)
    tunnel = C.cmat('tunnel', (0.05, 0.045, 0.04), 0.9)
    S['tunnel_lamps'] = []
    tl = C.cmat('tunnel_lamp', (1.0, 0.75, 0.45), 0.5, emission=12.0)
    for sg in (-1, 1):
        box(f'tunnel{sg}', (40, 0.1, 4), (0, sg * 2.2, 1.5), tunnel)
        for i in range(10):
            o = box(f'tlamp{sg}_{i}', (0.35, 0.05, 0.06), (0, sg * 2.14, 1.3), tl)
            o.visible_shadow = False
            S['tunnel_lamps'].append((o, sg, i))
    set_tunnel(S, 0.0)
    return S


def set_tunnel(S, t, speed=9.0):
    """t in seconds: lamps race past the windows (wrap every 4 m)."""
    for o, sg, i in S['tunnel_lamps']:
        x = ((i * 4.0 - t * speed) % 40.0) - 20.0
        o.location.x = x


def lights(strength=1.0):
    """Cool fluorescent area lights along the ceiling, very dark world."""
    w = bpy.context.scene.world or bpy.data.worlds.new('w')
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.02, 0.025, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.2
    out = []
    for sg in (-1, 1):
        for i in range(4):
            d = bpy.data.lights.new(f'fl{sg}{i}', 'AREA')
            d.shape, d.size, d.size_y = 'RECTANGLE', 2.0, 0.15
            d.energy, d.color = 90 * strength, (0.9, 0.95, 1.0)
            o = C.link(bpy.data.objects.new(f'fl{sg}{i}', d))
            o.location = (-3.75 + i * 2.5, sg * 0.45, CEIL - 0.04)
            out.append(o)
    return out
