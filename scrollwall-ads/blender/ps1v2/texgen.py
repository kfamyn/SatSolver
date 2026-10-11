"""Renders photo-like surface textures from Blender procedural materials into
small images (then used, nearest-filtered, on low-poly geometry).
Usage: python texgen.py   -> assets/ps1v2/surf_*.png"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets', 'ps1v2')


def reset(size):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = 4
    s.cycles.use_denoising = False
    s.render.resolution_x = s.render.resolution_y = size
    s.view_settings.view_transform = 'Standard'
    cam = bpy.data.cameras.new('c')
    cam.type = 'ORTHO'
    cam.ortho_scale = 1.0
    co = bpy.data.objects.new('c', cam)
    s.collection.objects.link(co)
    co.location = (0, 0, 1)
    s.camera = co
    bpy.ops.mesh.primitive_plane_add(size=1)
    return s, bpy.context.active_object


def node(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        if k.startswith('_'):
            setattr(n, k[1:], v)
        else:
            n.inputs[k].default_value = v
    return n


def ramp(nt, stops):
    r = nt.nodes.new('ShaderNodeValToRGB')
    els = r.color_ramp.elements
    els[0].position, els[0].color = stops[0][0], (*stops[0][1], 1)
    els[1].position, els[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, col in stops[1:-1]:
        e = els.new(pos)
        e.color = (*col, 1)
    return r


def hexc(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def make(name, size, build):
    s, plane = reset(size)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    col = build(nt, tc)
    nt.links.new(col, em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    plane.data.materials.append(m)
    s.render.filepath = os.path.join(OUT, f'surf_{name}.png')
    bpy.ops.render.render(write_still=True)
    print('surf', name, flush=True)


L = lambda nt, a, b, ia=0, ib=0: nt.links.new(a.outputs[ia] if isinstance(ia, int) else a.outputs[ia], b.inputs[ib] if isinstance(ib, int) else b.inputs[ib])


def wood(dark, light, scale=4.0, plank=None):
    def build(nt, tc):
        mp = node(nt, 'ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1, 14, 1)
        L(nt, tc, mp, 'UV', 'Vector')
        n = node(nt, 'ShaderNodeTexNoise', Scale=scale, Detail=8.0, Roughness=0.6)
        L(nt, mp, n, 'Vector', 'Vector')
        w = node(nt, 'ShaderNodeTexWave', Scale=3.0, Distortion=2.5, Detail=2.0)
        w.wave_type = 'BANDS'
        w.bands_direction = 'X'
        L(nt, mp, w, 'Vector', 'Vector')
        mix = node(nt, 'ShaderNodeMath', _operation='MULTIPLY')
        L(nt, w, mix, 'Fac', 0)
        L(nt, n, mix, 'Fac', 1)
        r = ramp(nt, [(0.1, hexc(dark)), (0.55, hexc(light))])
        L(nt, mix, r, 0, 'Fac')
        if plank:  # plank seams
            br = node(nt, 'ShaderNodeTexBrick', Scale=plank, **{'Mortar Size': 0.008, 'Bias': 0.0})
            br.inputs['Color1'].default_value = (1, 1, 1, 1)
            br.inputs['Color2'].default_value = (0.8, 0.8, 0.8, 1)
            br.inputs['Mortar'].default_value = (0.25, 0.2, 0.17, 1)
            br.offset = 0.5
            br.squash = 1.0
            mp2 = node(nt, 'ShaderNodeMapping')
            mp2.inputs['Scale'].default_value = (0.25, 1, 1)
            L(nt, tc, mp2, 'UV', 'Vector')
            L(nt, mp2, br, 'Vector', 'Vector')
            m2 = node(nt, 'ShaderNodeMix', _data_type='RGBA', _blend_type='MULTIPLY', Factor=1.0)
            L(nt, r, m2, 'Color', 6)
            L(nt, br, m2, 'Color', 7)
            return m2.outputs[2]
        return r.outputs['Color']
    return build


def fabric(base, var, scale=60.0, weave=True):
    def build(nt, tc):
        n = node(nt, 'ShaderNodeTexNoise', Scale=6.0, Detail=6.0, Roughness=0.55)
        L(nt, tc, n, 'UV', 'Vector')
        r = ramp(nt, [(0.35, hexc(var)), (0.65, hexc(base))])
        L(nt, n, r, 'Fac', 'Fac')
        if not weave:
            return r.outputs['Color']
        c = node(nt, 'ShaderNodeTexChecker', Scale=scale)
        c.inputs['Color1'].default_value = (1, 1, 1, 1)
        c.inputs['Color2'].default_value = (0.86, 0.86, 0.86, 1)
        L(nt, tc, c, 'UV', 'Vector')
        m2 = node(nt, 'ShaderNodeMix', _data_type='RGBA', _blend_type='MULTIPLY', Factor=1.0)
        L(nt, r, m2, 'Color', 6)
        L(nt, c, m2, 'Color', 7)
        return m2.outputs[2]
    return build


def speckle(base, dark, scale=30.0, detail=10.0):
    def build(nt, tc):
        n = node(nt, 'ShaderNodeTexNoise', Scale=scale, Detail=detail, Roughness=0.7)
        L(nt, tc, n, 'UV', 'Vector')
        v = node(nt, 'ShaderNodeTexVoronoi', Scale=scale * 2)
        L(nt, tc, v, 'UV', 'Vector')
        mx = node(nt, 'ShaderNodeMath', _operation='ADD')
        L(nt, n, mx, 'Fac', 0)
        L(nt, v, mx, 'Distance', 1)
        r = ramp(nt, [(0.45, hexc(dark)), (1.0, hexc(base))])
        L(nt, mx, r, 0, 'Fac')
        return r.outputs['Color']
    return build


def wrinkled(base, shade, scale=3.0):
    def build(nt, tc):
        n = node(nt, 'ShaderNodeTexNoise', Scale=scale, Detail=3.0, Roughness=0.5, Distortion=1.5)
        L(nt, tc, n, 'UV', 'Vector')
        r = ramp(nt, [(0.3, hexc(shade)), (0.5, hexc(base)), (0.7, hexc(base))])
        L(nt, n, r, 'Fac', 'Fac')
        return r.outputs['Color']
    return build


make('floor_wood', 256, wood('#5A3A22', '#A7744B', 3.0, plank=4.0))
make('wood_desk', 128, wood('#6E4C33', '#B78A5E', 2.5))
make('wood_dark', 128, wood('#2E2018', '#5E4230', 3.0))
make('wall_plaster', 128, speckle('#E8DDCF', '#CFC2B2', 18.0))
make('ceiling', 64, speckle('#EFEBE4', '#DAD4CA', 12.0))
make('carpet', 128, speckle('#5C6378', '#3D4255', 60.0))
make('duvet', 128, wrinkled('#2F3A5C', '#1C2440', 2.5))
make('sheet', 128, wrinkled('#E9E7E2', '#BDB8AF', 3.0))
make('pillow', 64, wrinkled('#F0EEE9', '#C9C4BA', 2.0))
make('curtain', 128, fabric('#7A6A9E', '#5A4C7E', 80.0))
make('cardboard', 64, speckle('#B58A5A', '#8E6A42', 40.0))
make('metal', 64, speckle('#A8ACB4', '#7E828A', 80.0))
make('plastic_black', 64, speckle('#26252B', '#1A191E', 50.0))
make('plastic_white', 64, speckle('#EDECEA', '#D6D4D0', 50.0))
make('laundry_blue', 64, wrinkled('#3E5C8E', '#263D66', 4.0))
make('laundry_white', 64, wrinkled('#E6E4E0', '#A9A49C', 4.0))
make('laundry_black', 64, wrinkled('#2A2A30', '#141418', 4.0))
make('cork', 64, speckle('#B98B5E', '#8A6440', 70.0))
make('rug', 128, fabric('#5B7378', '#3C5054', 120.0))
print('texgen done')
