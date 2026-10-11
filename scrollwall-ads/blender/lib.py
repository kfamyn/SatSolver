"""Scene-building helpers for the Scrollwall shorts (Blender as a Python module).

Everything is generated from code: no external models. Units are metres.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Euler


# ---------------------------------------------------------------- scene setup

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.device = 'CPU'
    s.cycles.use_denoising = True
    s.cycles.denoiser = 'OPENIMAGEDENOISE'
    s.cycles.samples = 48
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.05
    s.cycles.max_bounces = 6
    s.cycles.caustics_reflective = False
    s.cycles.caustics_refractive = False
    s.render.resolution_x = 1080
    s.render.resolution_y = 1920
    s.render.resolution_percentage = 50
    s.render.image_settings.file_format = 'PNG'
    s.render.fps = 30
    s.view_settings.view_transform = 'AgX'
    s.view_settings.look = 'AgX - Medium High Contrast'
    world = bpy.data.worlds.new('World')
    s.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.004, 0.003, 0.008, 1)
    bg.inputs['Strength'].default_value = 1.0
    return s


def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def set_smooth(obj, subdiv=2):
    for p in obj.data.polygons:
        p.use_smooth = True
    if subdiv:
        m = obj.modifiers.new('subd', 'SUBSURF')
        m.levels = subdiv
        m.render_levels = subdiv
    return obj


# ---------------------------------------------------------------- materials

def mat(name, color, rough=0.5, metal=0.0, sss=0.0, sss_radius=(1.0, 0.4, 0.25), coat=0.0, emit=None, emit_strength=0.0,
        sheen=0.0, alpha=1.0, transmission=0.0, ior=1.45, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Subsurface Weight'].default_value = sss
    b.inputs['Subsurface Radius'].default_value = sss_radius
    b.inputs['Subsurface Scale'].default_value = 0.02
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Alpha'].default_value = alpha
    b.inputs['Transmission Weight'].default_value = transmission
    b.inputs['IOR'].default_value = ior
    b.inputs['Specular IOR Level'].default_value = spec
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = emit_strength
    return m


def hexc(h):
    """sRGB hex -> linear tuple."""
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def emission_image_mat(name, image, strength=3.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.interpolation = 'Linear'
    nt.links.new(tex.outputs['Color'], em.inputs['Color'])
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m, tex, em


# ---------------------------------------------------------------- primitives

def sphere(name, r, loc, scale=(1, 1, 1), material=None, seg=48, rings=24, subdiv=1, rot=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    bm.to_mesh(mesh)
    bm.free()
    o = link(bpy.data.objects.new(name, mesh))
    o.location = loc
    o.scale = scale
    o.rotation_euler = rot
    if material:
        o.data.materials.append(material)
    set_smooth(o, subdiv)
    return o


def capsule(name, r, length, loc, material=None, rot=(0, 0, 0), scale=(1, 1, 1), subdiv=1, seg=48):
    """Capsule along local Z. length = straight part."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = 32
    verts = []
    # build as a sphere then stretch the hemispheres apart
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for v in bm.verts:
        if v.co.z > 1e-6:
            v.co.z += length / 2
        elif v.co.z < -1e-6:
            v.co.z -= length / 2
    bm.to_mesh(mesh)
    bm.free()
    o = link(bpy.data.objects.new(name, mesh))
    o.location = loc
    o.rotation_euler = rot
    o.scale = scale
    if material:
        o.data.materials.append(material)
    set_smooth(o, subdiv)
    return o


def box(name, size, loc, material=None, bevel=0.01, rot=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    bm.to_mesh(mesh)
    bm.free()
    o = link(bpy.data.objects.new(name, mesh))
    o.location = loc
    o.rotation_euler = rot
    if material:
        o.data.materials.append(material)
    if bevel:
        b = o.modifiers.new('bevel', 'BEVEL')
        b.width = bevel
        b.segments = 4
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def cylinder(name, r, depth, loc, material=None, rot=(0, 0, 0), verts=48, subdiv=0):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=depth)
    bm.to_mesh(mesh)
    bm.free()
    o = link(bpy.data.objects.new(name, mesh))
    o.location = loc
    o.rotation_euler = rot
    if material:
        o.data.materials.append(material)
    b = o.modifiers.new('bevel', 'BEVEL')
    b.width = min(r, depth) * 0.15
    b.segments = 3
    for p in o.data.polygons:
        p.use_smooth = True
    if subdiv:
        set_smooth(o, subdiv)
    return o


def limb(name, a, b, r, material, r2=None, subdiv=1):
    """Tapered capsule from point a to point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    o = capsule(name, r, max(0.001, d.length), (a + b) / 2, material, subdiv=subdiv)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    if r2 is not None:
        # taper: scale far end
        for v in o.data.vertices:
            t = (v.co.z + d.length / 2 + r) / (d.length + 2 * r)
            k = 1 + (r2 / r - 1) * max(0, min(1, t))
            v.co.x *= k
            v.co.y *= k
    return o


def parent(child, par):
    """Parent with child's current location interpreted as local to `par`."""
    child.parent = par
    return child


def empty(name, loc=(0, 0, 0)):
    e = link(bpy.data.objects.new(name, None))
    e.location = loc
    return e


# ---------------------------------------------------------------- lights / camera

def area_light(name, loc, energy, color=(1, 1, 1), size=1.0, target=None, shape='DISK'):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy = energy
    d.color = color
    d.size = size
    d.shape = shape
    o = link(bpy.data.objects.new(name, d))
    o.location = loc
    if target is not None:
        aim(o, target)
    return o


def point_light(name, loc, energy, color=(1, 1, 1), radius=0.05):
    d = bpy.data.lights.new(name, 'POINT')
    d.energy = energy
    d.color = color
    d.shadow_soft_size = radius
    o = link(bpy.data.objects.new(name, d))
    o.location = loc
    return o


def aim(obj, target):
    t = Vector(target) - obj.location
    obj.rotation_euler = t.to_track_quat('-Z', 'Y').to_euler()


def camera(name='Cam', lens=35, loc=(0, -3, 1.5), target=(0, 0, 1), dof_obj=None, fstop=2.8, sensor=36):
    c = bpy.data.cameras.new(name)
    c.lens = lens
    c.sensor_width = sensor
    c.sensor_fit = 'VERTICAL'
    c.clip_start = 0.005
    o = link(bpy.data.objects.new(name, c))
    o.location = loc
    aim(o, target)
    if dof_obj is not None or fstop:
        c.dof.use_dof = True
        c.dof.aperture_fstop = fstop
        if dof_obj is not None:
            c.dof.focus_object = dof_obj
    bpy.context.scene.camera = o
    return o
