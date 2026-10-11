"""Turn a modern asset into a PS1-era one: fewer polygons, tiny textures,
nearest-neighbour sampling, no normal maps."""
import bpy

_done = set()


def shrink_image(img, max_px):
    if img is None or img.name in _done or img.size[0] == 0:
        return
    w, h = img.size
    k = max_px / max(w, h)
    if k < 1:
        img.scale(max(8, int(w * k)), max(8, int(h * k)))
    _done.add(img.name)


def ps1fy(objects=None, decimate=0.35, tex_px=128, skip_decimate=('male1591', 'low-poly', 'eyebrow')):
    objs = objects or [o for o in bpy.data.objects if o.type == 'MESH']
    for o in objs:
        if decimate < 1 and not any(k in o.name for k in skip_decimate):
            m = o.modifiers.new('ps1_decimate', 'DECIMATE')
            m.ratio = decimate
        for slot in o.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue
            for n in list(mat.node_tree.nodes):
                if n.type == 'TEX_IMAGE':
                    n.interpolation = 'Closest'
                    shrink_image(n.image, tex_px)
                if n.type == 'NORMAL_MAP':
                    for l in list(n.outputs[0].links):
                        mat.node_tree.links.remove(l)
