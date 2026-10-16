"""Adapt downloaded CC0 source geometry, preserving authored silhouettes and UVs.

blender --background --python FILE -- --cache /absolute/cache
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'reference-forest'


def restore_uv(mesh):
    attr = mesh.attributes.get('UVMap')
    if attr is not None and attr.domain == 'CORNER' and attr.data_type == 'FLOAT_VECTOR':
        coords = [tuple(item.vector)[:2] for item in attr.data]
        mesh.attributes.remove(attr)
        layer = mesh.uv_layers.new(name='UVMap')
        for item, uv in zip(layer.data, coords):
            item.uv = uv


def export(obj, name):
    original_name = obj.name
    bpy.ops.object.select_all(action='DESELECT')
    obj.hide_set(False)
    obj.hide_viewport = False
    obj.hide_render = False
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    obj.location = Vector((0, 0, 0))
    restore_uv(obj.data)
    if not obj.data.uv_layers:
        raise ValueError('Missing export UVs: ' + obj.name)
    for index, mat in enumerate(obj.data.materials):
        placeholder = bpy.data.materials.get('Export_' + mat.name)
        if placeholder is None:
            placeholder = bpy.data.materials.new('Export_' + mat.name)
            placeholder.diffuse_color = (0.25, 0.3, 0.2, 1)
        obj.data.materials[index] = placeholder
    obj.data.calc_loop_triangles()
    triangles = len(obj.data.loop_triangles)
    obj.name = name
    path = ASSETS / (name + '.glb')
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                              export_vertex_color='NONE', export_materials='EXPORT',
                              export_animations=False, export_cameras=False, export_lights=False)
    if path.stat().st_size > 6000 * 1024:
        raise ValueError('Runtime mesh exceeds repository limit: ' + name)
    return {'file': path.name, 'triangles': triangles, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_object': original_name, 'dimensions_m': list(obj.dimensions)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    outputs = []
    bpy.ops.wm.open_mainfile(filepath=str(args.cache / 'fir_tree_01_1k.blend'))
    for variant in ['a', 'b', 'c']:
        name = f'fir_tree_01_{variant}_LOD2'
        outputs.append(export(bpy.data.objects[name], name))
    for source in ['rock_moss_set_01', 'fern_02']:
        bpy.ops.wm.open_mainfile(filepath=str(args.cache / (source + '_1k.blend')))
        candidates = [obj for obj in bpy.data.objects if obj.type == 'MESH' and len(obj.data.polygons) > 100]
        print('SOURCE_OBJECTS', source, [(o.name, len(o.data.polygons)) for o in candidates])
        if source == 'rock_moss_set_01':
            candidates = sorted(candidates, key=lambda o: o.name)[:3]
        for index, obj in enumerate(candidates):
            if obj.modifiers:
                bpy.context.view_layer.objects.active = obj
                obj.hide_set(False)
                obj.select_set(True)
                bpy.ops.object.convert(target='MESH')
            outputs.append(export(obj, source + '_' + str(index)))
    (ASSETS / 'meshes.json').write_text(json.dumps({'meshes': outputs}, indent=2) + '\n')
    print('REFERENCE_FOREST_MESHES', json.dumps(outputs))


if __name__ == '__main__':
    main()
