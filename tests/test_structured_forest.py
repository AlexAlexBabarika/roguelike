"""Source/capture provenance and geometry checks; no artistic-success assertion."""

import hashlib
import json
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'prototype/assets'
CAPTURES = ROOT / 'docs/screenshots/structured-forest'


class StructuredForestTests(unittest.TestCase):
    def test_asset_fingerprints(self):
        record = json.loads((ASSETS / 'structured-spruces.json').read_text())
        for key, name in [('asset_sha256', 'structured-spruces.glb'), ('atlas_sha256', 'spruce-branches.png')]:
            self.assertEqual(record[key], hashlib.sha256((ASSETS / name).read_bytes()).hexdigest())
        self.assertEqual(len(record['variants']), 3)

    def test_real_branch_geometry(self):
        data = (ASSETS / 'structured-spruces.glb').read_bytes()
        length = struct.unpack_from('<I', data, 12)[0]
        gltf = json.loads(data[20:20 + length])
        self.assertEqual(len(gltf['meshes']), 6)
        actual_triangles = sum(gltf['accessors'][p['indices']]['count'] // 3
                               for mesh in gltf['meshes'] for p in mesh['primitives'])
        record = json.loads((ASSETS / 'structured-spruces.json').read_text())
        self.assertEqual(actual_triangles, sum(v['triangles'] for v in record['variants']))
        for variant in record['variants']:
            self.assertGreater(variant['primary_branches'], 50)
            self.assertGreater(variant['fixed_branch_cards'], 500)
            self.assertLess(variant['triangles'], 30000)

    def test_capture_provenance(self):
        assets = json.loads((ASSETS / 'structured-spruces.json').read_text())
        names = ['daylight', 'spruce', 'silhouette', 'grove', 'weather']
        for name in names:
            with self.subTest(name=name):
                image = (CAPTURES / f'{name}.png').read_bytes()
                record = json.loads((CAPTURES / f'{name}.json').read_text())
                self.assertEqual(record['capture_sha256'], hashlib.sha256(image).hexdigest())
                self.assertEqual(record['resolution'], list(struct.unpack('>II', image[16:24])))
                self.assertEqual(record['asset_sha256'], assets['asset_sha256'])
                self.assertEqual(record['atlas_sha256'], assets['atlas_sha256'])
                self.assertEqual(record['scene'], 'res://forest_slice.tscn')
                self.assertEqual(record['projection'], 'orthographic')
                self.assertFalse(record['screen_filter'])
                self.assertFalse(record['wind'])
                self.assertTrue(record['shadows'])
                self.assertEqual(record['fog'], name == 'weather')
                self.assertEqual(record['rain'], name == 'weather')
                self.assertEqual(record['silhouette'], name == 'silhouette')
        day = json.loads((CAPTURES / 'daylight.json').read_text())
        weather = json.loads((CAPTURES / 'weather.json').read_text())
        for key in ['target', 'size', 'yaw_radians', 'elevation_radians', 'resolution']:
            self.assertEqual(day[key], weather[key])

    def test_lit_not_screen_filtered(self):
        shader = (ROOT / 'prototype/shaders/forest_needles.gdshader').read_text()
        self.assertNotIn('unshaded', shader)
        self.assertNotIn('hint_screen_texture', shader)
        self.assertNotIn('CAMERA', shader)
        self.assertIn('ALPHA_SCISSOR_THRESHOLD', shader)
        scene = (ROOT / 'prototype/forest_slice.gd').read_text()
        self.assertNotIn('painted_pass', scene)
        self.assertIn('SHADOW_CASTING_SETTING_DOUBLE_SIDED', scene)


if __name__ == '__main__':
    unittest.main()
