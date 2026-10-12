"""Bedroom v2: real CC0 photo textures + real props from Poly Haven, PS1-ified,
with afternoon god rays through the blinds. Same footprint as the v1 room:
x -1.8..1.8, y -1.7..1.7 (back wall at +y), z 0..2.6.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ps1v2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mh'))
import char as C  # noqa: E402  (tmat/cmat/link helpers + asset dir)
from room import box, cyl, draped, lump, plane, emissive  # noqa: E402
from ps1fy import shrink_image  # noqa: E402

PH = '/home/user/ph'
R = random.Random(12)
_pmat = {}


def photo(name, tiles=(1, 1), px=128, rough=0.85, tint=None):
    """Material from a Poly Haven photo texture, shrunk + nearest-filtered."""
    key = (name, tiles, tint)
    if key in _pmat:
        return _pmat[key]
    m = bpy.data.materials.new(f'ph_{name}')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.load(os.path.join(PH, 'textures', f'{name}.jpg'), check_existing=True)
    shrink_image(img, px)
    t.image = img
    t.interpolation = 'Closest'
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (tiles[0], tiles[1], 1)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
    col = t.outputs['Color']
    if tint:
        mx = nt.nodes.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        mx.blend_type = 'MULTIPLY'
        mx.inputs['Factor'].default_value = 1.0
        mx.inputs['B'].default_value = (*tint, 1)
        nt.links.new(col, mx.inputs['A'])
        col = mx.outputs['Result']
    nt.links.new(col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.2
    _pmat[key] = m
    return m


def prop(name, loc, height=None, width=None, rotz=0.0, decimate=0.35, px=96):
    """Import a Poly Haven glTF model, PS1-fy it, scale and place it."""
    d = os.path.join(PH, 'models', name)
    gltf = next(f for f in os.listdir(d) if f.endswith('.gltf'))
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(d, gltf))
    new = [o for o in bpy.data.objects if o not in before]
    root = C.link(bpy.data.objects.new(f'prop_{name}', None))
    for o in new:
        if o.parent is None:
            o.parent = root
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    size = hi - lo
    k = 1.0
    if height:
        k = height / max(size.z, 1e-4)
    elif width:
        k = width / max(size.x, size.y, 1e-4)
    # move so the model's base centre sits at the origin, then place
    for o in new:
        if o.parent is root:
            o.location = o.location - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    root.scale = (k, k, k)
    root.rotation_euler = (0, 0, rotz)
    root.location = loc
    for o in meshes:
        if decimate < 1:
            mod = o.modifiers.new('ps1', 'DECIMATE')
            mod.ratio = decimate
        for sl in o.material_slots:
            mat = sl.material
            if not mat or not mat.use_nodes:
                continue
            for n in mat.node_tree.nodes:
                if n.type == 'TEX_IMAGE':
                    n.interpolation = 'Closest'
                    shrink_image(n.image, px)
                if n.type == 'NORMAL_MAP':
                    for l in list(n.outputs[0].links):
                        mat.node_tree.links.remove(l)
    return root


def build():
    S = {}
    floor = photo('laminate_floor_02', (3, 3), 128)
    wall = photo('beige_wall_001', (2, 1.5), 128)
    box('floor', (3.6, 3.4, 0.04), (0, 0, -0.02), floor)
    box('ceiling', (3.6, 3.4, 0.04), (0, 0, 2.62), photo('beige_wall_002', (2, 2), 64, tint=(1.05, 1.05, 1.05)))
    box('wall_back', (3.6, 0.08, 2.6), (0, 1.74, 1.3), wall)
    box('wall_right', (0.08, 3.4, 2.6), (1.84, 0, 1.3), wall)
    box('wall_front', (3.6, 0.08, 2.6), (0, -1.74, 1.3), wall)  # behind camera: closes the light box
    # left wall with window hole (window y -0.55..0.65, z 0.95..2.05)
    box('wall_l_a', (0.08, 1.15, 2.6), (-1.84, -1.125, 1.3), wall)
    box('wall_l_b', (0.08, 1.05, 2.6), (-1.84, 1.175, 1.3), wall)
    box('wall_l_c', (0.08, 1.2, 0.95), (-1.84, 0.05, 0.475), wall)
    box('wall_l_d', (0.08, 1.2, 0.55), (-1.84, 0.05, 2.325), wall)
    white = C.cmat('window_white', (0.85, 0.84, 0.82), 0.5)
    for nm, sz, lc in [('sill', (0.22, 1.3, 0.04), (-1.74, 0.05, 0.95)), ('wf_t', (0.1, 1.24, 0.05), (-1.8, 0.05, 2.05)),
                       ('wf_l', (0.1, 0.05, 1.1), (-1.8, -0.55, 1.5)), ('wf_r', (0.1, 0.05, 1.1), (-1.8, 0.65, 1.5)),
                       ('wf_m', (0.06, 0.04, 1.1), (-1.82, 0.05, 1.5))]:
        box(nm, sz, lc, white)
    wv = plane('window_view', 2.4, 2.4, (-3.2, 0.05, 1.5), C.tmat('window_view', emission=2.5), rot=(math.pi / 2, 0, -math.pi / 2))
    wv.visible_shadow = False  # let the sun through
    S['slats'] = [box(f'slat{i}', (0.06, 1.16, 0.006), (-1.74, 0.05, 2.0 - i * 0.058), white, rot=(0, math.radians(38), 0)) for i in range(18)]
    curtain = photo('crepe_satin', (1, 2), 64, tint=(0.55, 0.45, 0.75))
    for k, y in enumerate((-0.82, 0.92)):
        box(f'curtain{k}', (0.06, 0.32, 1.8), (-1.72, y, 1.45), curtain)
    prop('potted_plant_04', (-1.72, -0.35, 0.97), height=0.32)

    # --- bed
    bx, by = -0.85, 0.62
    dark = photo('black_walnut_veneer_01', (1, 1), 64)
    box('bed_frame', (1.55, 2.12, 0.32), (bx, by, 0.2), dark)
    box('mattress', (1.48, 2.04, 0.2), (bx, by, 0.45), photo('cotton_jersey', (2, 2), 64, tint=(0.95, 0.95, 0.98)))
    box('headboard', (1.6, 0.08, 0.95), (bx, 1.68, 0.62), dark)
    pil = photo('cotton_jersey', (1, 1), 64, tint=(1.0, 1.0, 1.0))
    lump('pillow_a', 0.3, (bx - 0.35, 1.38, 0.63), pil, scale=(1.15, 0.6, 0.35), seed=1)
    lump('pillow_b', 0.3, (bx + 0.33, 1.42, 0.63), pil, scale=(1.1, 0.55, 0.33), seed=2)
    prop('throw_pillows_01', (bx + 0.05, 1.25, 0.6), width=0.7)
    S['duvet'] = draped('duvet', (1.9, 1.75), (bx, by - 0.28, 0.6), photo('curly_teddy_checkered', (2, 2), 96), droop=0.33, bumps=0.045,
                        seed=3, top=(1.46, 1.55))
    lump('thrown_hoodie', 0.22, (bx + 0.45, by - 0.65, 0.66), photo('denim_fabric', (1, 1), 64, tint=(0.4, 0.4, 0.45)), scale=(1.3, 0.9, 0.3), seed=4)
    for i in range(16):  # fairy lights
        t = i / 15
        b = C.link(bpy.data.objects.new(f'fairy{i}', bpy.data.meshes.new(f'fairy{i}')))
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.016)
        bm.to_mesh(b.data)
        bm.free()
        b.data.materials.append(emissive('fairy_m', (1.0, 0.75, 0.42), 14))
        b.location = (bx - 0.85 + t * 1.7, 1.69, 1.55 - math.sin(t * math.pi) * 0.12)
    S['clock'] = prop('wall_clock', (bx, 1.7, 1.95), width=0.34, rotz=0.0)

    # --- nightstand
    prop('painted_wooden_nightstand', (0.22, 1.42, 0.0), height=0.58)
    prop('alarm_clock_01', (0.12, 1.36, 0.58), height=0.09)
    can_m = C.tmat('can_volt')
    for i, (dx, dy) in enumerate([(0.1, -0.08), (0.18, -0.12), (0.26, -0.06)]):
        cyl(f'ns_can{i}', 0.033, 0.12, (0.0 + dx, 1.42 + dy, 0.64), can_m, seg=10)

    # --- desk zone (right wall): table, monitor, laptop, lamp, chair
    oak = photo('oak_veneer_01', (1, 2), 96)
    box('desk_top', (0.7, 1.45, 0.04), (1.45, 0.45, 0.75), oak)
    for oy in (-0.68, 0.68):
        box('desk_side', (0.66, 0.04, 0.73), (1.45, 0.45 + oy, 0.365), oak)
    box('desk_drawer', (0.6, 0.4, 0.5), (1.45, 0.75, 0.48), oak)
    box('led_desk', (0.02, 1.3, 0.01), (1.12, 0.45, 0.72), emissive('led', (0.65, 0.3, 1.0), 20))
    blk = C.cmat('blackplastic', (0.04, 0.04, 0.045), 0.6)
    box('mon_body', (0.05, 0.62, 0.36), (1.65, 0.55, 1.12), blk)
    plane('mon_screen', 0.58, 0.32, (1.624, 0.55, 1.12), C.tmat('screen_monitor', emission=2.2), rot=(math.pi / 2, 0, -math.pi / 2))
    box('mon_stand', (0.04, 0.04, 0.2), (1.69, 0.55, 0.85), blk)
    prop('classic_laptop', (1.35, 0.05, 0.75), width=0.34, rotz=-math.pi / 2)
    prop('desk_lamp_arm_01', (1.6, 0.98, 0.75), height=0.45, rotz=math.pi)
    prop('office_notepads', (1.3, 0.75, 0.75), width=0.22, rotz=0.3)
    prop('binder_notebook', (1.6, 0.15, 0.75), width=0.25, rotz=1.2)
    box('chair_seat', (0.5, 0.5, 0.08), (0.95, 0.45, 0.48), blk)
    box('chair_back', (0.08, 0.5, 0.7), (0.66, 0.45, 0.9), blk, rot=(0, math.radians(-8), 0))
    box('chair_stripe', (0.085, 0.12, 0.6), (0.66, 0.45, 0.92), C.cmat('chair_red', (0.6, 0.08, 0.1), 0.5), rot=(0, math.radians(-8), 0))
    cyl('chair_pole', 0.03, 0.38, (0.95, 0.45, 0.25), C.cmat('chrome', (0.6, 0.6, 0.62), 0.3, metal=1.0), seg=6)
    # wall shelf + frame + boombox above the desk
    prop('Shelf_01', (1.72, 0.45, 1.55), width=0.9, rotz=math.pi / 2)
    prop('boombox', (1.7, 0.75, 1.62), width=0.35, rotz=-math.pi / 2)
    prop('standing_picture_frame_01', (1.72, 0.2, 1.62), height=0.18, rotz=-math.pi / 2)
    prop('hanging_picture_frame_01', (1.79, 0.45, 2.05), width=0.45, rotz=-math.pi / 2)

    # --- back wall: bookshelf + books + plant, posters
    prop('wooden_bookshelf_worn', (0.95, 1.5, 0.0), height=1.75)
    prop('book_encyclopedia_set_01', (0.95, 1.45, 0.92), width=0.5)
    prop('potted_plant_01', (0.95, 1.5, 1.76), height=0.38)
    plane('poster_movie', 0.5, 0.75, (0.25, 1.695, 1.65), C.tmat('poster_movie'))
    plane('poster_band', 0.42, 0.56, (-1.55, -0.6, 1.6), C.tmat('poster_band'), rot=(math.pi / 2, 0, -math.pi / 2))
    box('led_ceiling_b', (3.5, 0.02, 0.02), (0, 1.68, 2.56), emissive('ledc', (0.6, 0.3, 1.0), 10))
    box('led_ceiling_r', (0.02, 3.3, 0.02), (1.78, 0, 2.56), emissive('ledc2', (0.6, 0.3, 1.0), 10))
    S['ceiling_lamp'] = prop('modern_ceiling_lamp_01', (0.2, 0.0, 2.6 - 0.35), height=0.35)

    # --- front-left corner: armchair drowning in clothes, TV dresser
    prop('modern_arm_chair_01', (-1.35, -1.2, 0.0), height=0.85, rotz=math.radians(40))
    for k in range(4):
        lump(f'chair_clothes{k}', 0.2, (-1.35 + R.uniform(-0.15, 0.15), -1.2 + R.uniform(-0.15, 0.15), 0.55 + k * 0.08),
             photo(R.choice(['denim_fabric', 'cotton_jersey', 'crepe_satin']), (1, 1), 48), scale=(1.4, 1, 0.35), seed=50 + k)
    prop('drawer_cabinet', (1.55, -1.05, 0.0), height=0.8, rotz=-math.pi / 2)
    prop('television_02', (1.6, -1.05, 0.8), height=0.42, rotz=-math.pi / 2)
    prop('gaming_console', (1.55, -0.7, 0.8), width=0.28, rotz=-math.pi / 2)

    # --- floor clutter
    box('rug', (1.6, 1.1, 0.01), (0.2, -0.45, 0.005), photo('dirty_carpet', (1, 1), 96))
    prop('cardboard_box_01', (0.55, -1.3, 0.0), height=0.32, rotz=0.4)
    prop('wicker_basket_01', (-0.5, -1.35, 0.0), height=0.45)
    lump('basket_overflow', 0.22, (-0.5, -1.35, 0.42), photo('cotton_jersey', (1, 1), 48), scale=(1, 1, 0.5), seed=30)
    prop('trashbag', (1.55, -0.3, 0.0), height=0.5)
    prop('gamepad', (0.35, -0.2, 0.0), width=0.16, rotz=0.7)
    box('pizza_box', (0.4, 0.4, 0.04), (0.55, -0.7, 0.025), photo('plywood', (1, 1), 48, tint=(1.0, 0.85, 0.65)), rot=(0, 0, 0.5))
    plane('pizza_in', 0.38, 0.38, (0.55, -0.7, 0.047), C.tmat('pizza_inside'), rot=(0, 0, 0.5))
    for k in range(3):
        cyl(f'floor_can{k}', 0.033, 0.12, (0.0 + k * 0.3, -0.15 - k * 0.1, 0.033), can_m, seg=10, rot=(math.pi / 2, 0, R.uniform(0, 3)))
    for k in range(4):
        lump(f'clothes{k}', 0.22, (-0.1 + R.uniform(-0.35, 0.35), -1.0 + R.uniform(-0.2, 0.2), 0.06),
             photo(R.choice(['denim_fabric', 'cotton_jersey']), (1, 1), 48, tint=R.choice([(1, 1, 1), (0.4, 0.4, 0.45), (0.6, 0.3, 0.3)])),
             scale=(1.4, 1, 0.35), seed=20 + k)
    return S


def lights(sun_power=14.0, haze=0.02):
    sd = bpy.data.lights.new('sun', 'SUN')
    sd.energy = sun_power
    sd.color = (1.0, 0.8, 0.58)
    sd.angle = math.radians(0.8)
    sun = C.link(bpy.data.objects.new('sun', sd))
    sun.rotation_euler = Vector((1.0, 0.18, -0.62)).normalized().to_track_quat('-Z', 'Y').to_euler()
    # cool skylight through the window
    a = bpy.data.lights.new('window_fill', 'AREA')
    a.energy, a.size, a.color = 18, 1.1, (0.7, 0.82, 1.0)
    wf = C.link(bpy.data.objects.new('window_fill', a))
    wf.location = (-1.65, 0.05, 1.5)
    wf.rotation_euler = Vector((1, 0, -0.25)).to_track_quat('-Z', 'Y').to_euler()
    # practicals
    pl = bpy.data.lights.new('lamp_desk', 'POINT')
    pl.energy, pl.color, pl.shadow_soft_size = 25, (1.0, 0.7, 0.4), 0.05
    lo = C.link(bpy.data.objects.new('lamp_desk', pl))
    lo.location = (1.45, 0.95, 1.1)
    m = bpy.data.lights.new('mon_glow', 'AREA')
    m.energy, m.size, m.color = 10, 0.6, (0.6, 0.8, 1.0)
    mo = C.link(bpy.data.objects.new('mon_glow', m))
    mo.location = (1.55, 0.55, 1.12)
    mo.rotation_euler = (0, math.pi / 2, 0)
    for nm, loc in [('led_glow_b', (0, 1.5, 2.45)), ('led_glow_r', (1.6, 0, 2.45))]:
        l = bpy.data.lights.new(nm, 'AREA')
        l.energy, l.size, l.color = 4, 2.5, (0.6, 0.35, 1.0)
        o = C.link(bpy.data.objects.new(nm, l))
        o.location = loc
        o.rotation_euler = (0.6, 0, 0) if loc[0] == 0 else (0, -0.6, 0)
    # thin haze so the sun through the blinds draws visible shafts
    if haze > 0:
        vol = box('haze', (3.55, 3.35, 2.55), (0, 0, 1.3), bpy.data.materials.new('haze'))
        vm = vol.data.materials[0]
        vm.use_nodes = True
        nt = vm.node_tree
        nt.nodes.remove(nt.nodes['Principled BSDF'])
        pv = nt.nodes.new('ShaderNodeVolumePrincipled')
        pv.inputs['Density'].default_value = haze
        pv.inputs['Anisotropy'].default_value = 0.6
        pv.inputs['Color'].default_value = (1.0, 0.95, 0.9, 1)
        nt.links.new(pv.outputs['Volume'], nt.nodes['Material Output'].inputs['Volume'])
        vol.visible_shadow = False
    return sun
