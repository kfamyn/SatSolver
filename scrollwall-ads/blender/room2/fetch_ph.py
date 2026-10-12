"""Download CC0 assets from Poly Haven (textures: diffuse 1k jpg; models: glTF 1k).
Usage: python3 fetch_ph.py <out_dir>"""
import json
import os
import sys
import urllib.request

OUT = sys.argv[1]
TEX = ['laminate_floor_02', 'beige_wall_001', 'beige_wall_002', 'fabric_pattern_07', 'cotton_jersey', 'dirty_carpet',
       'oak_veneer_01', 'black_walnut_veneer_01', 'crepe_satin', 'curly_teddy_checkered', 'denim_fabric', 'plywood',
       # reel 2: subway car
       'rubber_tiles', 'blue_metal_plate', 'metal_plate', 'metal_plate_02', 'velour_velvet', 'fabric_pattern_05', 'terrazzo_tiles',
       'painted_metal_shutter']
MODELS = ['wall_clock', 'alarm_clock_01', 'classic_laptop', 'gaming_console', 'gamepad', 'television_02', 'desk_lamp_arm_01',
          'painted_wooden_nightstand', 'wooden_bookshelf_worn', 'decorative_book_set_01', 'book_encyclopedia_set_01',
          'potted_plant_01', 'potted_plant_04', 'hanging_picture_frame_01', 'standing_picture_frame_01', 'throw_pillows_01',
          'wicker_basket_01', 'cardboard_box_01', 'trashbag', 'office_notepads', 'binder_notebook', 'WoodenTable_02',
          'modern_arm_chair_01', 'modern_ceiling_lamp_01', 'boombox', 'Shelf_01', 'drawer_cabinet',
          # reel 2: subway car
          'mounted_fluorescent_lights']


def get(url, path):
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'scrollwall-ads/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, 'wb') as f:
        f.write(r.read())


def files(asset):
    req = urllib.request.Request(f'https://api.polyhaven.com/files/{asset}', headers={'User-Agent': 'scrollwall-ads/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


for t in TEX:
    try:
        f = files(t)
        url = f['Diffuse']['1k']['jpg']['url']
        get(url, os.path.join(OUT, 'textures', f'{t}.jpg'))
        print('tex', t, flush=True)
    except Exception as e:
        print('tex FAIL', t, e, flush=True)

for m in MODELS:
    try:
        f = files(m)
        g = f['gltf']['1k']['gltf']
        base = os.path.join(OUT, 'models', m)
        get(g['url'], os.path.join(base, os.path.basename(g['url'])))
        for rel, info in g.get('include', {}).items():
            get(info['url'], os.path.join(base, rel))
        print('model', m, flush=True)
    except Exception as e:
        print('model FAIL', m, e, flush=True)
