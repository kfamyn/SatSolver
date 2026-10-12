"""Load the hero + subway NPCs into one scene and pose them seated / standing.

Each person: dict(name, rig, body, eyes) ; pose with seat(person, x, side, ...).
Side +1 = bench along y=+HALF_W (faces -y), -1 = bench along y=-HALF_W (faces +y).
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'mh'))
from ps1fy import ps1fy  # noqa: E402
from style import apply_style  # noqa: E402

NPC = {'office': 'female1605', 'worker': 'proxy741', 'student': 'female1605', 'business': 'proxy741'}
HAIR_TINT = {'hero': (0.22, 0.13, 0.08), 'office': (0.35, 0.22, 0.12), 'student': (0.08, 0.06, 0.05),
             'worker': (0.15, 0.15, 0.15), 'business': (0.3, 0.25, 0.2)}


def _tint_hair(objs, rgb):
    for o in objs:
        if o.type != 'MESH' or not any(k in o.name.lower() for k in ('hair', 'short0', 'bob', 'ponytail')):
            continue
        for sl in o.material_slots:
            nt = sl.material.node_tree
            tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and 'norm' not in n.name.lower()), None)
            bsdf = nt.nodes.get('Principled BSDF')
            if tex and bsdf:
                mul = nt.nodes.new('ShaderNodeMix')
                mul.data_type, mul.blend_type = 'RGBA', 'MULTIPLY'
                mul.inputs['Factor'].default_value = 1.0
                mul.inputs['B'].default_value = (*rgb, 1)
                nt.links.new(tex.outputs['Color'], mul.inputs['A'])
                nt.links.new(mul.outputs['Result'], bsdf.inputs['Base Color'])


def _person(name, objs, proxy):
    rig = next(o for o in objs if o.type == 'ARMATURE')
    body = next(o for o in objs if o.type == 'MESH' and proxy in o.name)
    eyes = next((o for o in objs if o.type == 'MESH' and 'low-poly' in o.name), None)
    ps1fy([body], decimate=1.0, tex_px=224)
    ps1fy([o for o in objs if o.type == 'MESH' and o is not body], decimate=1.0, tex_px=64)
    for sl in body.material_slots:
        for n in sl.material.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs['Roughness'].default_value = 0.9
    _tint_hair(objs, HAIR_TINT.get(name, (0.2, 0.15, 0.1)))
    return {'name': name, 'rig': rig, 'body': body, 'eyes': eyes, 'objs': objs}


def load_cast(hero_blend='/home/user/mh/scroller_lp.blend', npc_dir='/home/user/mh/npc', which=None):
    """Opens the hero file as the base scene, appends the NPCs. Returns {name: person}."""
    bpy.ops.wm.open_mainfile(filepath=hero_blend)
    hero_objs = list(bpy.data.objects)
    cast = {'hero': _person('hero', hero_objs, 'proxy741')}
    for name, proxy in NPC.items():
        if which and name not in which:
            continue
        path = os.path.join(npc_dir, f'{name}_npc.blend')
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = list(src.objects)
        objs = [o for o in dst.objects if o is not None]
        for o in objs:
            bpy.context.scene.collection.objects.link(o)
        cast[name] = _person(name, objs, proxy)
    return cast


def point(rig, bone, d):
    pb = rig.pose.bones[bone]
    bpy.context.view_layer.update()
    h = pb.head.copy()
    q = (pb.tail - pb.head).normalized().rotation_difference(Vector(d).normalized())
    pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ pb.matrix


def reset(p):
    for pb in p['rig'].pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    apply_style(p['rig'])
    if p['name'] == 'hero':  # tuck the phone hand's fingers so they don't cover the screen in close-ups
        for f in '2345':
            p['rig'].pose.bones[f'finger{f}-1.L'].scale = (0.35, 0.35, 0.35)
        p['rig'].pose.bones['metacarpal1.L'].scale = (0.3, 0.3, 0.3)
    bpy.context.view_layer.update()


def ground_hips(p, z):
    bpy.context.view_layer.update()
    r = p['rig']
    hz = (r.matrix_world @ r.pose.bones['pelvis.L'].head).z
    r.location.z += z - hz
    bpy.context.view_layer.update()


def seat(p, x, side, act='idle', t=0.0, k=0.0, half_w=1.35):
    """Seated on a bench. act: idle | phone | scroll | read | paper | look_up | phone_down.
    k: 0..1 shot progress (for gestures)."""
    reset(p)
    r = p['rig']
    r.location = (x, side * (half_w - 0.42), 0.0)
    r.rotation_euler = (0, 0, 0 if side > 0 else math.pi)
    for s_, sg in (('L', 1), ('R', -1)):
        point(r, f'upperleg01.{s_}', (sg * 0.1, -1.0, 0.05))
        point(r, f'lowerleg01.{s_}', (sg * 0.05, -0.2, -1.0))
    for nm in ('spine05', 'spine04', 'spine03', 'spine02', 'spine01'):
        point(r, nm, (0, 0.12, 1.0))
    head_dn = {'idle': 0.05, 'phone': 0.7, 'scroll': 0.75, 'read': 0.8, 'paper': 0.45, 'look_up': 0.0, 'phone_down': 0.15}[act]
    point(r, 'neck01', (0, -0.2, 1.0))
    sway = math.sin(t * 0.13 + x) * 0.03  # train sway
    point(r, 'head', (sway, -head_dn, 1.0))
    if act in ('phone', 'scroll', 'look_up'):
        point(r, 'upperarm01.L', (0.22, -0.45, -1.0))
        point(r, 'lowerarm01.L', (-0.45, -1.0, 0.75))
        flick = max(0.0, math.sin(t * 1.4)) * (0.45 if act == 'scroll' else 0.0)
        point(r, 'upperarm01.R', (-0.22, -0.45, -1.0))
        point(r, 'lowerarm01.R', (0.4, -1.0, 0.7 + flick))
    elif act in ('read', 'paper'):
        for s_, sg in (('L', 1), ('R', -1)):
            point(r, f'upperarm01.{s_}', (sg * 0.25, -0.35, -1.0))
            point(r, f'lowerarm01.{s_}', (-sg * (0.5 if act == 'read' else 0.15), -1.0, 0.55 if act == 'read' else 0.9))
            r.pose.bones[f'wrist.{s_}'].scale = (0.95, 0.95, 0.95)
    else:  # hands in lap
        for s_, sg in (('L', 1), ('R', -1)):
            point(r, f'upperarm01.{s_}', (sg * 0.2, -0.25, -1.0))
            point(r, f'lowerarm01.{s_}', (-sg * 0.2, -1.0, -0.15))
    ground_hips(p, 0.5)


def stand(p, x, y, facing=0.0, act='hold', t=0.0):
    """Standing in the aisle holding the overhead rail (act=hold) or a phone (act=phone)."""
    reset(p)
    r = p['rig']
    r.location = (x, y, 0.0)
    r.rotation_euler = (0, 0, facing)
    sway = math.sin(t * 0.13 + x) * 0.04
    point(r, 'spine05', (sway, 0, 1.0))
    if act == 'hold':
        point(r, 'upperarm01.R', (-0.15, 0.0, 1.0))
        point(r, 'lowerarm01.R', (-0.05, 0.0, 1.0))
        point(r, 'upperarm01.L', (0.2, 0.03, -1.0))
        point(r, 'lowerarm01.L', (0.12, -0.12, -1.0))
        point(r, 'head', (0, -0.2, 1.0))
    else:  # relaxed: arms down, hands near the hips, slight head tilt
        for s_, sg in (('L', 1), ('R', -1)):
            point(r, f'upperarm01.{s_}', (sg * 0.18, 0.02, -1.0))
            point(r, f'lowerarm01.{s_}', (sg * 0.08, -0.15, -1.0))
        point(r, 'head', (0.05, -0.15, 1.0))
    bpy.context.view_layer.update()
    ev = p['body'].evaluated_get(bpy.context.evaluated_depsgraph_get())
    zmin = min((ev.matrix_world @ v.co).z for v in ev.data.vertices)
    r.location.z -= zmin
    bpy.context.view_layer.update()


def eyes(p):
    bpy.context.view_layer.update()
    e = p['eyes']
    ev = e.evaluated_get(bpy.context.evaluated_depsgraph_get())
    pts = [ev.matrix_world @ v.co for v in ev.data.vertices]
    return sum(pts, Vector()) / len(pts)


def hand(p, side='L'):
    bpy.context.view_layer.update()
    r = p['rig']
    return r.matrix_world @ r.pose.bones[f'wrist.{side}'].tail


def clone(p, name):
    """Background passenger: copy of a person (own rig/pose, shared meshes)."""
    m = {}
    for o in p['objs']:
        if o.type in ('ARMATURE', 'MESH'):
            c = o.copy()
            bpy.context.scene.collection.objects.link(c)
            m[o] = c
    for o, c in m.items():
        if o.parent in m:
            c.parent = m[o.parent]
        for mod in c.modifiers:
            if mod.type == 'ARMATURE' and mod.object in m:
                mod.object = m[mod.object]
    return {'name': name, 'rig': m[p['rig']], 'body': m[p['body']], 'eyes': m.get(p['eyes']), 'objs': list(m.values())}


def turn_head(p, yaw, tilt=0.0):
    """Yaw the head around its own axis (radians, + = character's left), optional extra nod."""
    pb = p['rig'].pose.bones['head']
    bpy.context.view_layer.update()
    pb.matrix = pb.matrix @ Matrix.Rotation(yaw, 4, 'Y') @ Matrix.Rotation(tilt, 4, 'X')
    nk = p['rig'].pose.bones['neck01']
    nk.matrix = nk.matrix @ Matrix.Rotation(yaw * 0.3, 4, 'Y')
    bpy.context.view_layer.update()
