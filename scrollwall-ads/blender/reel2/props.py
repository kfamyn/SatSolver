"""Hand props for Reel 2: phones (emissive screen texture), book, newspaper."""
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, '..', 'assets', 'ps1')
_imgs = {}


def img(rel):
    if rel not in _imgs:
        _imgs[rel] = bpy.data.images.load(os.path.join(ASSETS, rel + '.png'), check_existing=True)
    return _imgs[rel]


def _mat(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*rgb, 1)
    b.inputs['Roughness'].default_value = rough
    return m


def phone(name, screen='feed/0001', strength=3.0):
    """Big PS1 phone; returns (object, image texture node). Screen = local -Y face."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.075
        v.co.y *= 0.009
        v.co.z *= 0.155
    bm.normal_update()
    for f in bm.faces:
        if f.normal.y < -0.5:
            f.material_index = 1
        for l in f.loops:
            c = l.vert.co
            l[uvl].uv = (c.x / 0.075 + 0.5, c.z / 0.155 + 0.5)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    scr = bpy.data.materials.new(name + '_screen')
    scr.use_nodes = True
    nt = scr.node_tree
    nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    t = nt.nodes.new('ShaderNodeTexImage')
    t.interpolation = 'Closest'
    t.image = img(screen)
    e.inputs['Strength'].default_value = strength
    nt.links.new(t.outputs['Color'], e.inputs['Color'])
    nt.links.new(e.outputs['Emission'], o.inputs['Surface'])
    ob.data.materials.append(_mat(name + '_body', (0.02, 0.02, 0.025), 0.3))
    ob.data.materials.append(scr)
    return ob, t


def hold_phone(ob, person):
    """Parent to the left wrist like the hero in Reel 1."""
    ob.parent = person['rig']
    ob.parent_type = 'BONE'
    ob.parent_bone = 'wrist.L'
    ob.location = (0.0, 0.13, 0.0)
    ob.rotation_euler = (math.radians(-70), 0, 0)


def _two_page(name, w, h, open_deg, outer, inner, thick=0.006):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    for side in (-1, 1):
        r = bmesh.ops.create_cube(bm, size=1.0)
        vs = r['verts']
        for v in vs:
            v.co.x = v.co.x * w + side * w / 2
            v.co.y *= h
            v.co.z *= thick
        bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-open_deg * side), 3, 'Y'))
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = 0 if f.normal.z < -0.3 else 1  # outside (away from reader) vs inside
            for l in f.loops:
                c = l.vert.co
                l[uvl].uv = (((c.x + w) / (2 * w)), c.y / h + 0.5)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(outer)
    me.materials.append(inner)
    return ob


def book(name='book'):
    return _two_page(name, 0.16, 0.24, 14, _mat('book_cover', (0.35, 0.05, 0.04), 0.9), _mat('book_pages', (0.85, 0.8, 0.68), 0.9), 0.012)


def newspaper(name='paper'):
    m = bpy.data.materials.new('newsprint')
    m.use_nodes = True
    nt = m.node_tree
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = img('subway/newspaper')
    t.interpolation = 'Closest'
    # front page on the right half of the outside, plain newsprint elsewhere
    nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    nt.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.95
    ob = _two_page(name, 0.3, 0.42, 8, m, _mat('newsprint_in', (0.8, 0.78, 0.72), 0.95), 0.003)
    # UVs: map each outside page to the full front page so the headline reads on both
    uvl = ob.data.uv_layers['UVMap']
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            u, v = uvl.data[li].uv
            u2 = (u * 2) % 1.0 if u < 0.999 else 1.0
            uvl.data[li].uv = (1.0 - u2, 1.0 - v)  # as seen from across the aisle
    return ob


def between_hands(ob, person, eyes_pt, lift=0.07, push=0.0):
    """Place a two-page prop between the hands, pages facing the reader's eyes."""
    bpy.context.view_layer.update()
    r = person['rig']
    hl = r.matrix_world @ r.pose.bones['wrist.L'].tail
    hr = r.matrix_world @ r.pose.bones['wrist.R'].tail
    mid = (hl + hr) / 2 + Vector((0, 0, lift))
    n = (eyes_pt - mid).normalized()
    mid = mid - n * push
    across = (hl - hr).normalized()
    y = n.cross(across).normalized()
    x = y.cross(n).normalized()
    ob.matrix_world = Matrix.Translation(mid) @ Matrix((x, y, n)).transposed().to_4x4()
