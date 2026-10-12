"""Builds the main character from MakeHuman (MPFB) assets and saves a .blend.

Body/skin/eyes/rig: MakeHuman system assets (CC0).
Hoodie: "Hooded sweat jacket" by Elvaerwyn (CC-BY 4.0)  -> credit required.
Pants: cortu_cargo_pants (CC0). Hair: cortu_short_messy_hair (CC0). Shoes: shoes01 (CC0).

Usage: python build_scroller.py <out.blend>
"""
import os
import sys

import bpy

OUT = sys.argv[-1] if sys.argv[-1].endswith('.blend') else '/home/user/mh/scroller.blend'
DATA = '/root/.config/blender/5.2/extensions/.user/user_default/mpfb/data'

bpy.ops.wm.read_factory_settings(use_empty=False)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')

from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService

macro = TargetService.get_default_macro_info_dict()
macro.update({'gender': 1.0, 'age': 0.45, 'muscle': 0.42, 'weight': 0.48, 'proportions': 0.55, 'height': 0.55})
macro['race'] = {'asian': 0.2, 'caucasian': 0.6, 'african': 0.2}
base = HumanService.create_human(macro_detail_dict=macro, scale=0.1)
print('human', base.name, flush=True)

HumanService.add_builtin_rig(base, 'default')
print('rig ok', flush=True)


def add(path, kind='Clothes'):
    obj = HumanService.add_mhclo_asset(os.path.join(DATA, path), base, asset_type=kind, subdiv_levels=0, material_type='MAKESKIN')
    print('added', path, flush=True)
    return obj


PROXY = os.environ.get('PROXY', 'male1591')
add(f'proxymeshes/{PROXY}/{PROXY}.proxy', 'Proxymeshes')
add('eyes/low-poly/low-poly.mhclo', 'Eyes')
add('eyebrows/eyebrow001/eyebrow001.mhclo', 'Eyebrows')
add('clothes/elvs_hooded_sweat_jacket1/elvs_hooded_sweat_jacket1.mhclo')
add('clothes/cortu_cargo_pants/cortu_cargo_pants.mhclo')
add('clothes/shoes01/shoes01.mhclo')
HAIRSTYLE = os.environ.get('HAIRSTYLE', 'short02')
add(f'hair/{HAIRSTYLE}/{HAIRSTYLE}.mhclo', 'Hair')
try:
    skin = os.path.join(DATA, 'skins', 'young_caucasian_male', 'young_caucasian_male.mhmat')
    if os.path.exists(skin):
        HumanService.set_character_skin(skin, base, skin_type='GAMEENGINE')
        print('skin ok', flush=True)
except Exception as e:  # skin is cosmetic; keep going
    print('skin failed', e, flush=True)

base.hide_render = True  # the low-poly proxy is what we render
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('saved', OUT, [o.name for o in bpy.data.objects], flush=True)
