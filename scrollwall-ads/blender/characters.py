"""Doug (the doomscroller), Wally (the wall) and Doug's bedroom.

Front of every character faces -Y. Z is up. Metres.
"""
import math
import random
import bpy
import bmesh
from mathutils import Vector
from lib import (mat, hexc, sphere, capsule, box, cylinder, limb, parent, empty, link, set_smooth,
                 emission_image_mat, area_light, point_light)


# ================================================================= eye shader

def eye_material(name, iris_hex='#4A3426', pupil=0.45):
    """Eyeball facing local -Y. Iris/pupil drawn procedurally; `pupil` (0..1 of the
    iris radius) is exposed on a Value node named 'pupil' so shots can dilate it."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    n = nt.nodes
    L = nt.links
    bsdf = n['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = 0.05
    bsdf.inputs['Coat Weight'].default_value = 1.0
    bsdf.inputs['Coat Roughness'].default_value = 0.0
    bsdf.inputs['Subsurface Weight'].default_value = 0.15
    tc = n.new('ShaderNodeTexCoord')
    sep = n.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Object'], sep.inputs[0])
    # radial distance from the eye's forward axis (normalised by radius 1 sphere)
    mx = n.new('ShaderNodeMath'); mx.operation = 'MULTIPLY'
    mz = n.new('ShaderNodeMath'); mz.operation = 'MULTIPLY'
    L.new(sep.outputs['X'], mx.inputs[0]); L.new(sep.outputs['X'], mx.inputs[1])
    L.new(sep.outputs['Z'], mz.inputs[0]); L.new(sep.outputs['Z'], mz.inputs[1])
    add = n.new('ShaderNodeMath'); add.operation = 'ADD'
    L.new(mx.outputs[0], add.inputs[0]); L.new(mz.outputs[0], add.inputs[1])
    rad = n.new('ShaderNodeMath'); rad.operation = 'SQRT'
    L.new(add.outputs[0], rad.inputs[0])
    front = n.new('ShaderNodeMath'); front.operation = 'LESS_THAN'
    L.new(sep.outputs['Y'], front.inputs[0]); front.inputs[1].default_value = 0.0
    IRIS = 0.52  # in units of the eyeball radius (object scale 1 == radius)
    iris_r = n.new('ShaderNodeValue'); iris_r.outputs[0].default_value = IRIS
    pv = n.new('ShaderNodeValue'); pv.name = 'pupil'; pv.label = 'pupil'
    pv.outputs[0].default_value = pupil
    pr = n.new('ShaderNodeMath'); pr.operation = 'MULTIPLY'
    L.new(iris_r.outputs[0], pr.inputs[0]); L.new(pv.outputs[0], pr.inputs[1])
    in_iris = n.new('ShaderNodeMath'); in_iris.operation = 'LESS_THAN'
    L.new(rad.outputs[0], in_iris.inputs[0]); L.new(iris_r.outputs[0], in_iris.inputs[1])
    in_pupil = n.new('ShaderNodeMath'); in_pupil.operation = 'LESS_THAN'
    L.new(rad.outputs[0], in_pupil.inputs[0]); L.new(pr.outputs[0], in_pupil.inputs[1])
    ii = n.new('ShaderNodeMath'); ii.operation = 'MULTIPLY'
    L.new(in_iris.outputs[0], ii.inputs[0]); L.new(front.outputs[0], ii.inputs[1])
    ip = n.new('ShaderNodeMath'); ip.operation = 'MULTIPLY'
    L.new(in_pupil.outputs[0], ip.inputs[0]); L.new(front.outputs[0], ip.inputs[1])
    # iris colour with radial streaks
    noise = n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 40
    L.new(tc.outputs['Object'], noise.inputs['Vector'])
    iris_col = n.new('ShaderNodeMix'); iris_col.data_type = 'RGBA'
    iris_col.inputs['A'].default_value = (*hexc(iris_hex), 1)
    iris_col.inputs['B'].default_value = (*[c * 2.2 for c in hexc(iris_hex)], 1)
    L.new(noise.outputs['Fac'], iris_col.inputs['Factor'])
    # sclera slightly veiny/pink toward the edge (tired eyes)
    sclera = n.new('ShaderNodeMix'); sclera.data_type = 'RGBA'
    sclera.inputs['A'].default_value = (0.95, 0.93, 0.9, 1)
    sclera.inputs['B'].default_value = (0.9, 0.55, 0.55, 1)
    L.new(rad.outputs[0], sclera.inputs['Factor'])
    c1 = n.new('ShaderNodeMix'); c1.data_type = 'RGBA'
    L.new(ii.outputs[0], c1.inputs['Factor'])
    L.new(sclera.outputs['Result'], c1.inputs['A'])
    L.new(iris_col.outputs['Result'], c1.inputs['B'])
    c2 = n.new('ShaderNodeMix'); c2.data_type = 'RGBA'
    L.new(ip.outputs[0], c2.inputs['Factor'])
    L.new(c1.outputs['Result'], c2.inputs['A'])
    c2.inputs['B'].default_value = (0.005, 0.005, 0.008, 1)
    L.new(c2.outputs['Result'], bsdf.inputs['Base Color'])
    return m


# ================================================================= Doug

class Doug:
    """Builds Doug sitting in bed holding his phone. Keeps handles to the parts
    shots animate: head pivot, neck, lids, pupils, thumb, phone."""

    def __init__(self, origin=(0, 0, 0.5), feed_dir=None):
        self.skin = mat('doug_skin', hexc('#E7BFA3'), rough=0.5, sss=0.35, sss_radius=(1.0, 0.35, 0.2))
        self.skin_dark = mat('doug_skin_dark', hexc('#9C6F7E'), rough=0.6, sss=0.2)
        self.hoodie = mat('doug_hoodie', hexc('#3B3550'), rough=0.85, sheen=0.6)
        self.hoodie2 = mat('doug_hoodie2', hexc('#4A4364'), rough=0.85, sheen=0.6)
        self.hair = mat('doug_hair', hexc('#2A1D18'), rough=0.55, sheen=0.3)
        self.lip = mat('doug_lip', hexc('#3A1C22'), rough=0.4)
        self.eye_mats = []
        root = self.root = empty('doug_root', origin)
        ox, oy, oz = origin

        # torso: hunched hoodie blob
        self.torso = sphere('doug_torso', 1.0, (0, 0.05, 0.34), scale=(0.25, 0.19, 0.3), material=self.hoodie, subdiv=2,
                            rot=(0.28, 0, 0))
        parent(self.torso, root)
        self.hood = sphere('doug_hood', 1.0, (0, 0.14, 0.6), scale=(0.2, 0.13, 0.1), material=self.hoodie2, subdiv=2, rot=(0.6, 0, 0))
        parent(self.hood, root)
        pocket = sphere('doug_pocket', 1.0, (0, -0.14, 0.2), scale=(0.15, 0.04, 0.07), material=self.hoodie2, rot=(0.3, 0, 0))
        parent(pocket, root)
        for s in (-1, 1):
            st = limb(f'doug_string{s}', (s * 0.05, -0.06, 0.6), (s * 0.055, -0.13, 0.42), 0.006, mat('string', hexc('#E8E4F2'), rough=0.7))
            parent(st, root)

        # neck pivot at the base of the neck; head hangs off the end
        self.neck_base = empty('doug_neck_base', (0, -0.02, 0.6))
        parent(self.neck_base, root)
        self.neck = capsule('doug_neck', 0.045, 0.1, (0, 0, 0.06), material=self.skin)
        parent(self.neck, self.neck_base)
        self.head_pivot = empty('doug_head_pivot', (0, 0, 0.13))
        parent(self.head_pivot, self.neck_base)
        hp = self.head_pivot
        head = sphere('doug_head', 1.0, (0, 0, 0.1), scale=(0.115, 0.118, 0.135), material=self.skin, subdiv=2)
        parent(head, hp)
        jaw = sphere('doug_jaw', 1.0, (0, -0.03, 0.03), scale=(0.085, 0.08, 0.06), material=self.skin, subdiv=2)
        parent(jaw, hp)
        nose = sphere('doug_nose', 1.0, (0, -0.122, 0.085), scale=(0.018, 0.02, 0.024), material=self.skin)
        parent(nose, hp)
        for s in (-1, 1):
            ear = sphere(f'doug_ear{s}', 1.0, (s * 0.112, 0.0, 0.1), scale=(0.015, 0.03, 0.04), material=self.skin)
            parent(ear, hp)
        mouth = sphere('doug_mouth', 1.0, (0, -0.103, 0.035), scale=(0.022, 0.006, 0.008), material=self.lip)
        parent(mouth, hp)
        self.mouth = mouth

        # eyes, lids, dark circles
        self.lids = []
        self.eyes = []
        for s in (-1, 1):
            em = eye_material(f'doug_eye{s}')
            self.eye_mats.append(em)
            ex, ey, ez = s * 0.043, -0.098, 0.115
            eye = sphere(f'doug_eye{s}', 1.0, (ex, ey, ez), scale=(0.021, 0.021, 0.021), material=em, subdiv=1)
            parent(eye, hp)
            self.eyes.append(eye)
            # lid = hemisphere of skin pivoting around the eye centre
            lid_piv = empty(f'doug_lidpiv{s}', (ex, ey, ez))
            parent(lid_piv, hp)
            lid = self._hemisphere(f'doug_lid{s}', 0.0235, self.skin)
            lid.location = (0, 0, 0)
            parent(lid, lid_piv)
            self.lids.append(lid_piv)
            bag = sphere(f'doug_bag{s}', 1.0, (ex, ey + 0.004, ez - 0.022), scale=(0.022, 0.008, 0.009), material=self.skin_dark, subdiv=1)
            parent(bag, hp)
            brow = capsule(f'doug_brow{s}', 0.006, 0.022, (ex, ey - 0.006, ez + 0.033), material=self.hair, rot=(0, math.pi / 2 + s * 0.15, 0))
            parent(brow, hp)

        # messy hair
        rnd = random.Random(3)
        for i in range(26):
            a = rnd.uniform(-1.2, 1.2)
            b = rnd.uniform(0.15, 1.25)
            x = math.sin(a) * math.sin(b) * 0.115
            y = -math.cos(a) * math.sin(b) * 0.1 + 0.02
            z = 0.1 + math.cos(b) * 0.13
            if y < -0.07 and z < 0.19:  # keep the forehead clear
                z += 0.02
            h = sphere(f'doug_hair{i}', 1.0, (x, y, z + 0.03), scale=(0.035, 0.03, 0.05), material=self.hair, subdiv=1,
                       rot=(rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), rnd.uniform(0, 3)))
            parent(h, hp)

        # arms -> hands holding the phone in front of the chest
        self.phone_pivot = empty('doug_phone_pivot', (0, -0.22, 0.5))
        parent(self.phone_pivot, root)
        for s in (-1, 1):
            sh = (s * 0.2, 0.0, 0.5)
            el = (s * 0.24, -0.12, 0.26)
            wr = (s * 0.07, -0.22, 0.42)
            ua = limb(f'doug_upper{s}', sh, el, 0.065, self.hoodie, r2=0.06)
            fa = limb(f'doug_fore{s}', el, wr, 0.06, self.hoodie, r2=0.055)
            parent(ua, root)
            parent(fa, root)
            hand = sphere(f'doug_hand{s}', 1.0, (s * 0.05, -0.23, 0.45), scale=(0.035, 0.03, 0.045), material=self.skin, subdiv=2)
            parent(hand, root)
        # phone: body + screen with the feed sequence
        self.phone = box('doug_phone', (0.075, 0.008, 0.155), (0, 0, 0), material=mat('phone', hexc('#121116'), rough=0.25, coat=1), bevel=0.006)
        parent(self.phone, self.phone_pivot)
        self.screen_img = None
        if feed_dir:
            img = bpy.data.images.load(f'{feed_dir}/feed_0001.png')
            img.source = 'SEQUENCE'
            m, tex, em = emission_image_mat('phone_screen', img, strength=2.2)
            tex.image_user.frame_duration = 240
            tex.image_user.use_cyclic = True
            tex.image_user.use_auto_refresh = True
            self.screen_tex = tex
            self.screen_em = em
            bpy.ops.mesh.primitive_plane_add(size=1)
            scr = bpy.context.active_object
            scr.name = 'doug_screen'
            scr.scale = (0.068, 0.148, 1)
            scr.rotation_euler = (math.pi / 2, 0, math.pi)  # faces +Y (toward Doug)
            scr.location = (0, 0.0045, 0)
            scr.data.materials.append(m)
            parent(scr, self.phone_pivot)
        # phone light on his face
        # spot from the screen aimed up at his face (aimed in set_pose)
        sd = bpy.data.lights.new('doug_phonelight', 'SPOT')
        sd.energy = 4.0
        sd.color = hexc('#BFD6FF')
        sd.spot_size = 1.2
        sd.spot_blend = 1.0
        sd.shadow_soft_size = 0.06
        self.phone_light = link(bpy.data.objects.new('doug_phonelight', sd))
        self.phone_light.location = (0, 0.03, 0.0)
        parent(self.phone_light, self.phone_pivot)
        self.head_ref = None
        # thumb (animated flick), lives near the screen
        self.thumb_pivot = empty('doug_thumb_pivot', (0.04, -0.01, -0.045))
        parent(self.thumb_pivot, self.phone_pivot)
        thumb = capsule('doug_thumb', 0.012, 0.045, (-0.015, 0.0, 0.03), material=self.skin, rot=(0, -0.5, 0))
        parent(thumb, self.thumb_pivot)
        nail = sphere('doug_nail', 1.0, (-0.026, 0.008, 0.05), scale=(0.009, 0.003, 0.011), material=mat('nail', hexc('#F2CDBF'), rough=0.2, coat=1),
                      rot=(0, -0.5, 0))
        parent(nail, self.thumb_pivot)
        self.nail = nail

        tc = self.phone_light.constraints.new('TRACK_TO')
        tc.target = head
        tc.track_axis = 'TRACK_NEGATIVE_Z'
        tc.up_axis = 'UP_Y'
        self.head = head
        # default pose: head tilted down at the phone
        self.phone_pivot.rotation_euler = (0.65, 0, 0)
        self.set_pose()

    @staticmethod
    def _hemisphere(name, r, material):
        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-5], context='VERTS')
        bm.to_mesh(mesh)
        bm.free()
        o = link(bpy.data.objects.new(name, mesh))
        o.data.materials.append(material)
        set_smooth(o, 1)
        return o

    def set_pose(self, head_pitch=0.95, neck_len=1.0, lid=0.45, pupil=0.45, thumb=0.0, head_roll=0.0, mouth_open=0.0):
        """lid: 0 open .. 1 closed. neck_len: 1 normal, >1 stretched toward the phone."""
        self.neck_base.rotation_euler = (head_pitch * 0.6, 0, head_roll)
        self.neck.scale = (1, 1, neck_len)
        self.neck.location = (0, 0, 0.06 * neck_len)
        self.head_pivot.location = (0, 0, 0.13 * neck_len)
        self.head_pivot.rotation_euler = (head_pitch * 0.4, 0, 0)
        for lp in self.lids:
            # -1.4 rad = fully open (lid tucked up/back), +0.25 = closed over the front
            lp.rotation_euler = (-1.4 + lid * 1.65, 0, 0)
        for em in self.eye_mats:
            em.node_tree.nodes['pupil'].outputs[0].default_value = pupil
        self.thumb_pivot.rotation_euler = (thumb * 0.5, 0, 0)
        self.mouth.scale = (0.022, 0.006, 0.008 + mouth_open * 0.014)


# ================================================================= Wally

class Wally:
    """The pill from the Scrollwall icon, alive: glazed porcelain with a soft
    violet glow inside, and nothing but two capsule eyes."""

    def __init__(self, origin=(0, 0, 0), height=1.0):
        self.porcelain = mat('wally_porcelain', hexc('#F5F2FB'), rough=0.18, coat=1.0, sss=0.45, sss_radius=(0.7, 0.55, 1.0),
                             emit=hexc('#B9A0F0'), emit_strength=0.25)
        self.ink = mat('wally_ink', hexc('#0E0C12'), rough=0.05, coat=1.0)
        self.root = empty('wally_root', origin)
        r = 0.2 * height
        length = 0.62 * height
        self.body = capsule('wally_body', r, length, (0, 0, r + length / 2), material=self.porcelain, subdiv=2)
        parent(self.body, self.root)
        self.eyes = []
        for s in (-1, 1):
            e = capsule(f'wally_eye{s}', 0.017 * height, 0.05 * height, (s * 0.062 * height, -r * 0.985, r + length * 0.78),
                        material=self.ink, subdiv=1)
            e.scale = (1, 0.55, 1)
            parent(e, self.root)
            self.eyes.append(e)


# ================================================================= bedroom

def bedroom(clock_text='11:58'):
    floor_m = mat('floor', hexc('#2A2433'), rough=0.6)
    wall_m = mat('wall', hexc('#2E2A44'), rough=0.9)
    sheet_m = mat('sheet', hexc('#D9D4E6'), rough=0.9, sheen=0.4)
    blanket_m = mat('blanket', hexc('#5B4A8A'), rough=0.9, sheen=1.0)
    wood_m = mat('wood', hexc('#4A3A5A'), rough=0.6)
    box('floor', (8, 8, 0.02), (0, 0, -0.01), floor_m, bevel=0)
    box('wall_back', (8, 0.05, 4), (0, 1.2, 2), wall_m, bevel=0)
    box('wall_left', (0.05, 8, 4), (-1.8, 0, 2), wall_m, bevel=0)
    # bed
    box('bed_frame', (1.5, 2.2, 0.3), (0, 0.1, 0.15), wood_m, bevel=0.03)
    box('mattress', (1.42, 2.1, 0.2), (0, 0.1, 0.4), sheet_m, bevel=0.06)
    box('headboard', (1.6, 0.08, 1.0), (0, 1.15, 0.6), wood_m, bevel=0.03)
    sphere('pillow', 1.0, (0, 0.9, 0.55), scale=(0.45, 0.18, 0.1), material=sheet_m, subdiv=2)
    blanket = sphere('blanket', 1.0, (0, -0.35, 0.5), scale=(0.72, 0.62, 0.13), material=blanket_m, subdiv=2)
    d = blanket.modifiers.new('wrinkle', 'DISPLACE')
    tex = bpy.data.textures.new('wrinkles', 'CLOUDS')
    tex.noise_scale = 0.15
    d.texture = tex
    d.strength = 0.04
    # nightstand + digital clock
    box('nightstand', (0.45, 0.4, 0.5), (0.98, 0.85, 0.25), wood_m, bevel=0.02)
    box('clock_body', (0.16, 0.07, 0.07), (0.95, 0.8, 0.54), mat('clock', hexc('#1B1820'), rough=0.3, coat=0.6), bevel=0.01)
    bpy.ops.object.text_add(location=(0.95, 0.764, 0.525), rotation=(math.pi / 2, 0, 0))
    txt = bpy.context.active_object
    txt.name = 'clock_text'
    txt.data.body = clock_text
    txt.data.size = 0.045
    txt.data.align_x = 'CENTER'
    txt.data.align_y = 'CENTER'
    txt.data.extrude = 0.001
    txt.data.materials.append(mat('clock_led', (0, 0, 0), emit=hexc('#FF3B30'), emit_strength=8))
    point_light('clock_glow', (0.95, 0.7, 0.55), 0.3, color=hexc('#FF3B30'), radius=0.05)
    # window with moonlight
    win_m = mat('window_sky', (0, 0, 0), emit=hexc('#1B2350'), emit_strength=1.5)
    box('window', (0.9, 0.02, 1.1), (-0.95, 1.17, 1.55), win_m, bevel=0)
    frame_m = mat('frame', hexc('#CFC8DE'), rough=0.6)
    for (x, z, w, h) in [(-0.95, 2.1, 0.98, 0.05), (-0.95, 1.0, 0.98, 0.05), (-1.42, 1.55, 0.05, 1.15), (-0.48, 1.55, 0.05, 1.15),
                         (-0.95, 1.55, 0.03, 1.1), (-0.95, 1.55, 0.9, 0.03)]:
        box('wframe', (w, 0.04, h), (x, 1.15, z), frame_m, bevel=0.005)
    moon = area_light('moonlight', (-1.2, 2.5, 2.2), 220, color=hexc('#8FA8FF'), size=1.2, target=(0, 0, 0.8))
    area_light('fill', (1.5, -2.0, 1.8), 40, color=hexc('#6E62B8'), size=2.0, target=(0, 0.4, 1.0))
    return txt
