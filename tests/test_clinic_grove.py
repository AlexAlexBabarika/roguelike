"""Source licensing, export UVs and actual-engine evidence, not a visual quality score."""

import hashlib
import json
from pathlib import Path
import re
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'prototype/assets/reference-forest'
CAPTURES = ROOT / 'docs/screenshots/clinic-grove'
ARCHIVE = ROOT / 'docs/screenshots/clinic-grove-v1'
TERRAIN = ROOT / 'prototype/assets/grove-terrain'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ClinicGroveTests(unittest.TestCase):
    def test_baked_terrain_is_reproducible_and_traced_to_cc0_sources(self):
        record = json.loads((TERRAIN / 'terrain.json').read_text())
        self.assertEqual(record['source_license'], 'CC0-1.0')
        self.assertEqual(record['world_span_m'], 64.0)
        self.assertEqual(record['resolution'], 2048)
        self.assertEqual(record['builder_sha256'], digest(ROOT / 'prototype/tools/build_grove_terrain.py'))
        for name, expected in record['runtime_files'].items():
            self.assertEqual(digest(TERRAIN / name), expected)
            self.assertTrue((TERRAIN / name).read_bytes().startswith(b'\xff\xd8'))
        for name, expected in record['sources'].items():
            self.assertEqual(digest(ASSETS / name), expected)
        scene = (ROOT / 'prototype/clinic_grove.gd').read_text()
        placements = scene.split('const FIR_PLACEMENTS := [')[1].split('\n]')[0]
        pattern = r'Vector3\(([-\d.]+), 0, ([-\d.]+)\), \d, [-\d.]+, ([-\d.]+)'
        roots = [[float(x), float(z), float(size) * 5]
                 for x, z, size in re.findall(pattern, placements)]
        self.assertEqual(len(roots), 19)
        self.assertEqual(record['roots_xz_radius'], roots)

    def test_prior_capture_is_preserved_with_its_original_provenance(self):
        for name in ['daylight', 'tree', 'silhouette', 'approach', 'weather']:
            with self.subTest(name=name):
                path = ARCHIVE / (name + '.png')
                record = json.loads(path.with_suffix('.json').read_text())
                self.assertEqual(record['capture_sha256'], digest(path))
                self.assertEqual(record['scene'], 'res://clinic_grove.tscn')
                self.assertNotIn('revision', record)

    def test_licensed_sources_and_maps(self):
        record = json.loads((ASSETS / 'sources.json').read_text())
        self.assertEqual(record['license'], 'CC0-1.0')
        for source in record['sources']:
            self.assertEqual(source['license'], 'CC0-1.0')
            self.assertTrue(source['authors'])
            self.assertTrue(source['url'].startswith('https://polyhaven.com/a/'))
            for entry in source['files']:
                self.assertEqual(len(entry['md5']), 32)
                self.assertTrue(entry['url'].startswith('https://dl.polyhaven.org/file/ph-assets/'))
        for name, expected in record['runtime_files'].items():
            self.assertEqual(digest(ASSETS / name), expected, name)
        self.assertEqual(set(record['runtime_files']), {p.name for p in ASSETS.iterdir()
                                                       if p.suffix in ['.png', '.jpg']})

    def test_real_geometry_uvs_and_budget(self):
        record = json.loads((ASSETS / 'meshes.json').read_text())
        self.assertEqual(len(record['meshes']), 10)
        for mesh in record['meshes']:
            path = ASSETS / mesh['file']
            self.assertEqual(digest(path), mesh['sha256'])
            raw = path.read_bytes()
            self.assertLess(len(raw), 6000 * 1024)
            self.assertEqual(raw[:4], b'glTF')
            length = struct.unpack_from('<I', raw, 12)[0]
            gltf = json.loads(raw[20:20 + length])
            primitives = [p for item in gltf['meshes'] for p in item['primitives']]
            triangles = sum(gltf['accessors'][p['indices']]['count'] // 3 for p in primitives)
            self.assertEqual(triangles, mesh['triangles'], mesh['file'])
            for primitive in primitives:
                attributes = primitive['attributes']
                self.assertIn('NORMAL', attributes)
                self.assertIn('TEXCOORD_0', attributes)
                self.assertEqual(gltf['accessors'][attributes['POSITION']]['count'],
                                 gltf['accessors'][attributes['TEXCOORD_0']]['count'])
                self.assertNotIn('COLOR_0', attributes)
        firs = [m for m in record['meshes'] if m['file'].startswith('fir_tree')]
        self.assertEqual(len(firs), 3)
        self.assertTrue(all(30000 < m['triangles'] < 75000 for m in firs))

    def test_captures_are_engine_output_with_source_fingerprints(self):
        for name in ['daylight', 'tree', 'silhouette', 'approach', 'weather']:
            with self.subTest(name=name):
                path = CAPTURES / (name + '.png')
                record = json.loads(path.with_suffix('.json').read_text())
                self.assertEqual(record['capture_sha256'], digest(path))
                self.assertEqual(record['scene'], 'res://clinic_grove.tscn')
                self.assertEqual(record['resolution'], list(struct.unpack('>II', path.read_bytes()[16:24])))
                self.assertFalse(record['screen_filter'])
                self.assertFalse(record['wind'])
                self.assertTrue(record['shadows'])
                self.assertEqual(record['rain'], name == 'weather')
                self.assertEqual(record['fog'], name == 'weather')
                self.assertEqual(record['source_manifest_sha256'], digest(ASSETS / 'sources.json'))
                self.assertEqual(record['mesh_manifest_sha256'], digest(ASSETS / 'meshes.json'))
                self.assertEqual(record['revision'], '02-refined')
                self.assertEqual(record['tree_count'], 19)
                self.assertEqual(record['terrain_manifest_sha256'], digest(TERRAIN / 'terrain.json'))
                self.assertGreater(record['sun_energy'], 0.0)
                self.assertEqual(record['scene_sha256'], digest(ROOT / 'prototype/clinic_grove.gd'))
                for shader, expected in record['shaders'].items():
                    self.assertEqual(digest(ROOT / f'prototype/shaders/{shader}.gdshader'), expected)
        before = json.loads((ROOT / 'docs/screenshots/structured-forest/daylight.json').read_text())
        after = json.loads((CAPTURES / 'daylight.json').read_text())
        weather = json.loads((CAPTURES / 'weather.json').read_text())
        for key in ['target', 'size', 'yaw_radians', 'elevation_radians', 'resolution']:
            self.assertEqual(before[key], after[key], key)
            self.assertEqual(after[key], weather[key], key)
        original = json.loads((ARCHIVE / 'daylight.json').read_text())
        earlier_approach = json.loads((ARCHIVE / 'approach.json').read_text())
        refined_approach = json.loads((CAPTURES / 'approach.json').read_text())
        for key in ['target', 'size', 'yaw_radians', 'elevation_radians', 'resolution']:
            self.assertEqual(original[key], after[key], key)
            self.assertEqual(earlier_approach[key], refined_approach[key], key)

    def test_materials_are_lit_and_not_screen_filtered(self):
        for shader in ['grove_surface', 'grove_ground', 'grove_clinic']:
            source = (ROOT / f'prototype/shaders/{shader}.gdshader').read_text()
            for disallowed in ['hint_screen_texture', 'unshaded', 'INV_VIEW_MATRIX']:
                self.assertNotIn(disallowed, source)
        self.assertIn('ALPHA_SCISSOR_THRESHOLD', (ROOT / 'prototype/shaders/grove_surface.gdshader').read_text())


if __name__ == '__main__':
    unittest.main()
