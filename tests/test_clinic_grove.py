"""Source licensing, export UVs and actual-engine evidence, not a visual quality score."""

import hashlib
import json
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'prototype/assets/reference-forest'
CAPTURES = ROOT / 'docs/screenshots/clinic-grove'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ClinicGroveTests(unittest.TestCase):
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
                self.assertEqual(record['scene_sha256'], digest(ROOT / 'prototype/clinic_grove.gd'))
                for shader, expected in record['shaders'].items():
                    self.assertEqual(digest(ROOT / f'prototype/shaders/{shader}.gdshader'), expected)
        before = json.loads((ROOT / 'docs/screenshots/structured-forest/daylight.json').read_text())
        after = json.loads((CAPTURES / 'daylight.json').read_text())
        weather = json.loads((CAPTURES / 'weather.json').read_text())
        for key in ['target', 'size', 'yaw_radians', 'elevation_radians', 'resolution']:
            self.assertEqual(before[key], after[key], key)
            self.assertEqual(after[key], weather[key], key)

    def test_materials_are_lit_and_not_screen_filtered(self):
        for shader in ['grove_surface', 'grove_ground', 'grove_clinic']:
            source = (ROOT / f'prototype/shaders/{shader}.gdshader').read_text()
            for disallowed in ['hint_screen_texture', 'unshaded', 'INV_VIEW_MATRIX']:
                self.assertNotIn(disallowed, source)
        self.assertIn('ALPHA_SCISSOR_THRESHOLD', (ROOT / 'prototype/shaders/grove_surface.gdshader').read_text())


if __name__ == '__main__':
    unittest.main()
