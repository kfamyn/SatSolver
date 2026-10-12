

# ------------------------------------------------------------------ v2 extras
# overscroll bounce: the phone screen texture can slide (CLIP leaves a dark gap)
_snt = phone_tex.id_data
_tc = _snt.nodes.new('ShaderNodeTexCoord')
_map = _snt.nodes.new('ShaderNodeMapping')
_snt.links.new(_tc.outputs['UV'], _map.inputs['Vector'])
_snt.links.new(_map.outputs['Vector'], phone_tex.inputs['Vector'])
phone_tex.extension = 'CLIP'


def screen_offset(v):
    _map.inputs['Location'].default_value[1] = v


# the Scrollwall: a translucent violet force field that rises at the foot of the bed
WALL_W, WALL_H, WALL_Y, WALL_X = 1.75, 2.1, -0.6, -0.85
wme = bpy.data.meshes.new('scrollwall')
wme.from_pydata([(-WALL_W / 2, 0, 0), (WALL_W / 2, 0, 0), (WALL_W / 2, 0, WALL_H), (-WALL_W / 2, 0, WALL_H)], [], [(0, 1, 2, 3)])
wme.uv_layers.new(name='UVMap')
for li, uv in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
    wme.uv_layers['UVMap'].data[li].uv = uv
wall = bpy.data.objects.new('scrollwall', wme)
s.collection.objects.link(wall)
wall.location = (WALL_X, WALL_Y, -3.0)
wall.visible_shadow = False
wm = bpy.data.materials.new('scrollwall')
wm.use_nodes = True
nt = wm.node_tree
nt.nodes.clear()
_o = nt.nodes.new('ShaderNodeOutputMaterial')
_mix = nt.nodes.new('ShaderNodeMixShader')
_tr = nt.nodes.new('ShaderNodeBsdfTransparent')
_em = nt.nodes.new('ShaderNodeEmission')
_em.inputs['Strength'].default_value = 2.2
_wt = nt.nodes.new('ShaderNodeTexImage')
_wt.image = img('screens/forcefield')
_wt.interpolation = 'Closest'
_noise = nt.nodes.new('ShaderNodeTexNoise')
_noise.inputs['Scale'].default_value = 7.0
_gt = nt.nodes.new('ShaderNodeMath')
_gt.operation = 'GREATER_THAN'  # noise > dissolve threshold keeps the pixel
_m1 = nt.nodes.new('ShaderNodeMath')
_m1.operation = 'MULTIPLY'
_m2 = nt.nodes.new('ShaderNodeMath')
_m2.operation = 'MULTIPLY'
nt.links.new(_wt.outputs['Color'], _em.inputs['Color'])
nt.links.new(_noise.outputs['Fac'], _gt.inputs[0])
nt.links.new(_wt.outputs['Alpha'], _m1.inputs[0])
nt.links.new(_gt.outputs[0], _m1.inputs[1])
nt.links.new(_m1.outputs[0], _m2.inputs[0])
nt.links.new(_m2.outputs[0], _mix.inputs['Fac'])
nt.links.new(_tr.outputs[0], _mix.inputs[1])
nt.links.new(_em.outputs[0], _mix.inputs[2])
nt.links.new(_mix.outputs[0], _o.inputs['Surface'])
# readable from both sides: mirror u on back faces
_uv = nt.nodes.new('ShaderNodeTexCoord')
_geo = nt.nodes.new('ShaderNodeNewGeometry')
_sep = nt.nodes.new('ShaderNodeSeparateXYZ')
_comb = nt.nodes.new('ShaderNodeCombineXYZ')
_fu = nt.nodes.new('ShaderNodeMath')
_fu.operation = 'MULTIPLY_ADD'  # u * (1 - 2b) + b
_fb = nt.nodes.new('ShaderNodeMath')
_fb.operation = 'MULTIPLY_ADD'
_fb.inputs[1].default_value = -2.0
_fb.inputs[2].default_value = 1.0
nt.links.new(_uv.outputs['UV'], _sep.inputs[0])
nt.links.new(_geo.outputs['Backfacing'], _fb.inputs[0])
nt.links.new(_sep.outputs[0], _fu.inputs[0])
nt.links.new(_fb.outputs[0], _fu.inputs[1])
nt.links.new(_geo.outputs['Backfacing'], _fu.inputs[2])
nt.links.new(_fu.outputs[0], _comb.inputs[0])
nt.links.new(_sep.outputs[1], _comb.inputs[1])
nt.links.new(_comb.outputs[0], _wt.inputs['Vector'])
wme.materials.append(wm)
wl = bpy.data.lights.new('wall_light', 'AREA')
wl.color, wl.size, wl.size_y = (0.6, 0.4, 1.0), WALL_W, WALL_H
wl.shape = 'RECTANGLE'
wlo = bpy.data.objects.new('wall_light', wl)
s.collection.objects.link(wlo)
wlo.parent = wall
wlo.location = (0, 0.05, WALL_H / 2)
wlo.rotation_euler = (math.radians(90), 0, 0)  # faces +Y, toward the bed


def set_wall(h=1.0, fade=1.0, dissolve=0.0):
    """h: 0 = sunk below the floor, 1 = fully up (may overshoot). dissolve 0..1 eats it in patches."""
    wall.location.z = -WALL_H * 1.05 * (1 - h)
    on = h > 0.02 and fade > 0.01 and dissolve < 0.99
    wall.hide_render = not on
    wlo.hide_render = not on
    _gt.inputs[1].default_value = -0.05 + 1.1 * dissolve
    _m2.inputs[1].default_value = fade
    wl.energy = 70 * fade * (1 - dissolve) * min(1.0, max(0.0, h))


def rise(x):
    """0->1 with a springy overshoot (back-out ease)."""
    x = max(0.0, min(1.0, x))
    c = 2.2
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def spring(x):
    """overscroll: snaps out, wobbles back to 0."""
    if x <= 0:
        return 0.0
    return math.exp(-x * 5) * math.sin(x * 14) * 1.0


WALL_C = Vector((WALL_X, WALL_Y, 1.05))
_M0 = {}
_reset_pose0 = reset_pose
FING = os.environ.get('FING', '2345')
THUMB = False


def reset_pose():
    """also tuck the phone hand's fingers so they don't cover the screen in inserts."""
    _reset_pose0()
    for f in FING:
        sc = 0.35
        rig.pose.bones[f'finger{f}-1.L'].scale = (sc, sc, sc)
    if not THUMB:  # thumb off the screen unless it's tapping
        rig.pose.bones['metacarpal1.L'].scale = (0.3, 0.3, 0.3)
    bpy.context.view_layer.update()


def recoil(r):
    """head and torso jerk back from the wall (after pose_bed)."""
    if r <= 0:
        return
    for nm in ('spine02', 'spine01'):
        point_bone(nm, (0, 0.28 + 0.35 * r, 1.0))
    point_bone('head', (0, 0.25 * r, 1.0))


def front_face(t, k, dist=(0.42, 0.34), lens=(34, 38), side=0.36):
    f = eyes() + Vector((0, 0, -0.03))
    a = Vector((side, -1.0, 0.05)).normalized()
    move(k, (f + a * dist[0], f), (f + a * dist[1], f), lens)


def insert(k, a=0.8, b=0.72, lens=32):
    p, e = wpos(obj=phone), eyes()
    place_up(p + (e - p) * (a + (b - a) * ease(k)), p, phone_up(phone), lens)


PH_LOC0, PH_ROT0 = phone.location.copy(), phone.rotation_euler.copy()


def attach_phone():
    if phone.parent is None:
        phone.parent = rig
        phone.parent_type = 'BONE'
        phone.parent_bone = 'wrist.L'
        phone.rotation_mode = 'XYZ'
        phone.location = PH_LOC0
        phone.rotation_euler = PH_ROT0


def throw_phone(m0, dt, v=(1.4, -0.25, 3.0)):
    """cartoon toss: ballistic arc with spin, one bounce, then flat on the floor.
    Returns 'land' on the frame it hits the floor (for the clatter)."""
    p0 = m0.translation
    vx, vy, vz = v
    floor = 0.015
    tl = (vz + math.sqrt(vz * vz + 2 * 9.8 * (p0.z - floor))) / 9.8
    q0 = m0.to_quaternion()
    phone.parent = None
    phone.rotation_mode = 'QUATERNION'
    ev = None
    if dt <= tl:
        pos = Vector((p0.x + vx * dt, p0.y + vy * dt, p0.z + vz * dt - 4.9 * dt * dt))
        rot = Quaternion(Vector((0.3, 1.0, 0.5)).normalized(), dt * 22) @ q0
    else:
        d2 = dt - tl
        base = Vector((p0.x + vx * tl, p0.y + vy * tl, floor))
        b = 0.9 * d2 - 4.9 * d2 * d2
        slide = min(d2, 0.35)
        pos = base + Vector((vx * 0.35 * slide, vy * 0.35 * slide, max(0.0, b)))
        flat = Euler((math.radians(-90), 0, 0.6)).to_quaternion()  # screen up
        rot = flat if b <= 0 else Quaternion(Vector((1, 0, 0)), d2 * 12) @ flat
        if 0 <= d2 < 1 / 30 or (0.9 / 4.9 <= d2 < 0.9 / 4.9 + 1 / 30):
            ev = 'land'
    phone.location = pos
    phone.rotation_quaternion = rot
    return ev


def fling_arms(a):
    if a <= 0:
        return
    for side, sg in (('L', 1), ('R', -1)):
        cur_u = Vector((sg * 0.5, 0.1, 1.0))
        point_bone(f'upperarm01.{side}', Vector((sg * 0.22, -0.45, -1.0)).lerp(cur_u, a))
        point_bone(f'lowerarm01.{side}', Vector((sg * -0.3, -0.8, 0.5)).lerp(Vector((sg * 0.25, 0.15, 1.0)), a))


# ------------------------------------------------------------------ shots
def shot(i, t, n):
    k = t / max(1, n - 1)
    sid = T['shots'][i]['id']
    meta = {}
    hide_coins()
    attach_phone()
    desk_phone.hide_render = True
    show_phone(True)
    screen_offset(0.0)
    set_wall(0.0)
    if sid == 'wide':
        set_time(15.0)
        pose_bed(t * 1.6, scroll=2.0)
        feed(t, 2)
        move(k, ((1.35, -1.55, 1.75), (-0.6, 0.9, 0.85)), ((1.05, -1.2, 1.6), (-0.65, 0.9, 0.85)), (16, 19))
    elif sid == 'swipe_pov':
        set_time(15.1)
        pose_bed(t * 1.6 + 40, scroll=2.0)
        feed(t + 40, 3)
        e, p = eyes(), wpos(obj=phone)
        d = (p - e).normalized()
        place_up(e + d * (0.04 + 0.08 * ease(k)) + Vector((0.02, 0, 0.03)), p, phone_up(phone), 28)
    elif sid == 'clock':
        set_time(15.3 + k * 3.0)
        pose_bed(t)
        c = wpos(obj=clock_root)
        move(k, (c + Vector((0.14, -0.95, -0.08)), c), (c + Vector((0.08, -0.6, -0.05)), c), (32, 38))
        meta['tick'] = True
    elif sid == 'overhead':
        set_time(16.5 + k * 2.0)
        pose_bed(t * 1.6, scroll=2.0)
        feed(t, 2)
        cc = Vector((-0.85, 0.75, 0.6))
        place(cc + Vector((0, 0, 1.85)), cc, 15 + 3 * ease(k), roll=math.radians(10 + 45 * ease(k)))
        cam.location.z = 2.45
    elif sid == 'limit':
        set_time(18.4)
        pose_bed(t, scroll=0.0, free_arm_down=True)
        phone_tex.image = img('screens/limit')
        insert(k, 0.85, 0.7)
    elif sid == 'face_blank':
        set_time(18.4)
        pose_bed(t, scroll=0.0, free_arm_down=True, look=0.6)
        phone_tex.image = img('screens/limit')
        front_face(t, k)
    elif sid == 'ignore_tap':
        set_time(18.4)
        pose_bed(t, scroll=0.0, free_arm_down=True)
        if k < 0.4:
            phone_tex.image = img('screens/limit')
        elif k < 0.6:
            phone_tex.image = img('screens/limit_tap')
        else:
            feed(t, 3)
        meta['tap'] = t == int(0.4 * (n - 1)) + 1
        insert(k, 0.75, 0.68)
    elif sid == 'swipe_bounce':
        set_time(18.5)
        x = (t - 9) / 30
        pose_bed(t * 1.6 if t < 9 else 14, scroll=2.5 if t < 9 else 0.0)
        if t < 9:
            feed(t, 3)
        else:
            feed(9, 3)
            screen_offset(-0.35 * spring(x))
        meta['thud'] = t == 9
        insert(k, 0.72, 0.62)
        if 9 <= t < 13:
            meta['shake'] = 0.5 * (1 - (t - 9) / 4)
    elif sid == 'wall_rise':
        set_time(18.6)
        pose_bed(t, scroll=0.0)
        feed(9, 3)
        set_wall(rise(t / 10))
        meta['wall_hit'] = t == 6
        if 6 <= t < 14:
            meta['shake'] = 1 - (t - 6) / 8
            meta['flash'] = max(0.0, 0.6 - (t - 6) * 0.2)
        move(k, ((0.75, -1.6, 0.45), (-0.75, 0.0, 1.05)), ((0.7, -1.5, 0.5), (-0.78, 0.0, 1.1)), (17, 18), roll=(0.06, 0.02))
    elif sid == 'face_recoil':
        set_time(18.6)
        pose_bed(t, scroll=0.0, look=0.3)
        recoil(ease(t / 4))
        feed(9, 3)
        set_wall(1.0)
        front_face(t, k, (0.36, 0.33), (32, 34), side=0.15)
        if t < 5:
            meta['shake'] = 0.4
    elif sid == 'wall_hero':
        set_time(18.6)
        pose_bed(t, scroll=0.0, look=0.25)
        recoil(1.0)
        point_bone('upperarm01.L', (0.3, -0.15, -1.0))
        point_bone('lowerarm01.L', (0.15, -1.0, -0.25))
        phone_tex.image = img('screens/shield_12')
        set_wall(1.0)
        h = wpos('head')
        move(k, (h + Vector((0.3, 0.2, 0.2)), WALL_C), (h + Vector((0.2, 0.1, 0.12)), WALL_C + Vector((0, 0, -0.05))), (20, 24))
    elif sid == 'shield':
        set_time(18.6)
        pose_bed(t, scroll=0.0, free_arm_down=True)
        set_wall(1.0)
        phone_tex.image = img(f'screens/shield_{min(12, t):02d}')
        insert(k, 0.72, 0.6)
    elif sid == 'face_stare':
        set_time(18.6)
        pose_bed(t, scroll=0.0, look=0.65)
        phone_tex.image = img('screens/shield_12')
        set_wall(1.0, 0.85)
        front_face(t, k, (0.4, 0.32), (36, 42), side=-0.25)
    elif sid == 'desk':
        set_time(18.7)
        pose_desk(t * 2)
        show_phone(False)
        set_wall(1.0, 0.7)
        desk_phone.hide_render = False
        desk_tex.image = img('screens/balance_00')
        move(k, ((-0.15, -0.95, 1.45), (1.25, 0.45, 0.85)), ((0.2, -0.6, 1.35), (1.25, 0.45, 0.85)), (20, 24))
    elif sid == 'desk_top':
        set_time(18.8 + k * 0.6)
        pose_desk(t * 3)
        show_phone(False)
        desk_phone.hide_render = False
        desk_tex.image = img(f'screens/balance_{min(20, int(k * 5) * 5):02d}')
        for ci, c in enumerate(coins):
            tt = (t - ci * 1.5) / 6
            if tt < 0:
                continue
            tt = min(1.0, tt)
            c.location = (1.12 + (ci % 4) * 0.05, 0.45 + (ci // 4) * 0.06, 1.3 - 0.52 * tt * tt)
            c.rotation_euler = ((1 - tt) * 9 + ci, 0, ci)
        cc = Vector((1.25, 0.5, 0.76))
        place(cc + Vector((0, 0, 1.6 - 0.3 * ease(k))), cc, 18, roll=math.radians(90 + 30 * ease(k)))
        meta['coins'] = True
    elif sid == 'coins':
        set_time(19.0 + k * 0.2)
        pose_desk(t * 3)
        show_phone(False)
        desk_phone.hide_render = False
        desk_tex.image = img(f'screens/balance_{min(45, 20 + int(k * 6) * 5):02d}')
        p = wpos(obj=desk_phone)
        for ci, c in enumerate(coins):
            tt = (t - ci * 2) / 7
            if tt < 0:
                continue
            tt = min(1.0, tt)
            ang = ci * 2.4
            land = p + Vector((math.cos(ang) * (0.12 + 0.01 * ci), math.sin(ang) * (0.1 + 0.01 * ci), -0.005 + 0.004 * (ci % 3)))
            c.location = land + Vector((0, 0, 0.5 * (1 - tt * tt)))
            c.rotation_euler = ((1 - tt) * 11 + ci, 0, ci)
        a, b = p + Vector((-0.08, -0.4, 0.38)), p + Vector((-0.06, -0.3, 0.28))
        place_up(a.lerp(b, ease(k)), p, phone_up(desk_phone), 26 + 4 * ease(k))
        meta['coins'] = True
    elif sid == 'balance':
        set_time(19.3)
        pose_desk(t)
        show_phone(False)
        desk_phone.hide_render = False
        desk_tex.image = img('screens/balance_50')
        p = wpos(obj=desk_phone)
        move(k, (p + Vector((0.0, -0.01, 0.42)), p), (p + Vector((0.0, -0.01, 0.3)), p), (34, 38), roll=(math.pi / 2, math.pi / 2))
        meta['ding'] = t == 3
    elif sid == 'pay_pov':
        set_time(19.4)
        pose_desk(t, holding=True)
        phone_tex.image = img('screens/unlock_offer' if k < 0.55 else 'screens/unlock_tilt')
        meta['tap'] = t == int(0.55 * (n - 1)) + 1
        e, p = eyes(), wpos(obj=phone)
        d = (p - e).normalized()
        place_up(e + d * (0.04 + 0.08 * ease(k)), p, phone_up(phone), 28)
    elif sid == 'tilt':
        set_time(19.5)
        tilt = ease(k / 0.45) * (1 - ease((k - 0.7) / 0.25))
        pose_desk(t, holding=True, tilt=tilt)
        phone_tex.image = img('screens/unlock_done' if k > 0.55 else 'screens/unlock_tilt')
        p, nrm = wpos(obj=phone), screen_normal(phone)
        place(p + nrm * 0.07, p + nrm * 1.0, 18)
        meta['cctv'] = {'cam': 'FRONT CAM', 'box': face_box(), 'clock': 19.5 * 3600 + t / 30,
                        'tag': 'PAID 40 COINS' if k > 0.55 else 'TILT TO SPEND'}
        meta['chime'] = t == int(0.55 * (n - 1)) + 1
    elif sid == 'unlocked':
        set_time(19.5)
        pose_desk(t, holding=True)
        phone_tex.image = img('screens/unlock_done')
        p, e = wpos(obj=phone), eyes()
        place_up(p + (e - p) * (0.7 - 0.12 * ease(k)), p, phone_up(phone), 32)
    elif sid == 'wall_open':
        set_time(19.6)
        pose_desk(t, holding=True)
        phone_tex.image = img('screens/unlock_done')
        dz = ease((k - 0.12) / 0.6)
        set_wall(1.0, 1.0, dz)
        meta['dissolve'] = t == int(0.12 * (n - 1))
        move(k, ((1.45, 0.05, 1.35), WALL_C), ((1.2, -0.1, 1.3), WALL_C + Vector((0, 0.3, -0.1))), (18, 20))
    elif sid == 'golden':
        set_time(19.0)
        pose_bed(t, scroll=0.5, look=0.45)
        feed(t, 0.6)
        move(k, ((-0.35, -1.2, 1.3), (-0.85, 1.0, 0.85)), ((-0.4, -1.5, 1.35), (-0.85, 1.0, 0.88)), (19, 18))
    elif sid == 'wall_back':
        # 0-12 still scrolling | 12 music cuts, he freezes | slowly looks up | 34 SLAM, phone flies
        set_time(19.1)
        cut, hit = 12, 34
        pose_bed(min(t, cut) + 40, scroll=0.5 if t < cut else 0.0,
                 look=0.45 - 0.4 * ease((t - cut - 4) / 14))
        feed(min(t, cut) + 40, 0.6)
        if t >= hit:
            bpy.context.view_layer.update()
            m0 = _M0.get('m') if _M0.get('m') is not None else phone.matrix_world.copy()
            recoil(ease((t - hit) / 3))
            fling_arms(ease((t - hit) / 3))
            if throw_phone(m0, (t - hit) / 30) == 'land':
                meta['clatter'] = True
            meta['whoosh'] = t == hit + 1
        else:
            bpy.context.view_layer.update()
            _M0['m'] = phone.matrix_world.copy()
        meta['cut'] = t == cut
        set_wall(rise((t - hit + 6) / 10) if t >= hit - 6 else 0.0)
        meta['wall_hit'] = t == hit
        if hit <= t < hit + 8:
            meta['shake'] = 1 - (t - hit) / 8
            meta['flash'] = max(0.0, 0.6 - (t - hit) * 0.2)
        # static comic wide (locked-off), tiny creep in during the silence
        z = ease((t - cut) / (hit - cut))
        place(Vector((0.95, -1.35, 1.3)).lerp(Vector((0.85, -1.2, 1.27)), z), (-0.6, 0.45, 0.85), 16)
    elif sid == 'endcard':
        set_time(19.2)
        pose_bed(0, scroll=0.0, look=0.05)
        recoil(1.0)
        fling_arms(1.0)
        show_phone(False)
        set_wall(1.0)
        place((WALL_X, -1.62, 1.1), (WALL_X, 0.5, 1.0), 18)
        meta['endcard'] = True
    return meta


def main():
    meta = {}
    g = 0
    for sh in T['shots']:
        i, n = sh['i'], sh['frames']
        for t in range(n):
            g += 1
            if ONLY and i not in ONLY:
                continue
            if MID:
                if t != n // 2:
                    continue
            elif (g - 1) % STEP:
                continue
            if sh['id'] == 'endcard' and t > 0 and not MID:
                continue
            s.frame_set(g)
            m = shot(i, t, n) or {}
            m['shot'] = i
            meta[g] = m
            s.render.filepath = os.path.join(FR, f'{g:04d}.png')
            bpy.ops.render.render(write_still=True)
            print(f'shot {i:02d} {sh["id"]} frame {g}', flush=True)
    if MID:
        return
    old = {}
    mp = os.path.join(REEL, 'meta.json')
    if os.path.exists(mp) and ONLY:
        old = {int(k): v for k, v in json.load(open(mp))['frames'].items()}
    old.update(meta)
    json.dump({'total': T['total_frames'], 'frames': old}, open(mp, 'w'))
    print('TOTAL', T['total_frames'], flush=True)


main()
