"""Integrity checks for the separate, prepared look-development kit."""

import hashlib
import json
import struct
import unittest
from pathlib import Path

from test_research_archive import ReportParser


ROOT = Path(__file__).resolve().parents[1]


class StyleStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.asset = ROOT / "prototype/assets/forest-clinic-prepared.glb"
        cls.raw = cls.asset.read_bytes()
        length = struct.unpack_from("<I", cls.raw, 12)[0]
        cls.document = json.loads(cls.raw[20:20 + length])
        cls.binary = cls.raw[28 + length:]

    def test_prepared_kit_provenance(self):
        metadata = json.loads(self.asset.with_suffix(".json").read_text())
        self.assertEqual(metadata["seed"], 40217)
        self.assertEqual(metadata["asset_sha256"], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(metadata["source_sha256"], hashlib.sha256(
            (ROOT / "prototype/tools/build_mock_scene.py").read_bytes()).hexdigest())
        self.assertEqual(metadata["trunks_shortened"], 22)
        self.assertEqual(metadata["fronds_unified"], 4840)
        self.assertLess(len(self.raw), 6000 * 1024)

    def test_masks_are_not_white_placeholder(self):
        masks = []
        for mesh in self.document["meshes"]:
            for primitive in mesh["primitives"]:
                attributes = primitive["attributes"]
                self.assertIn("NORMAL", attributes)
                self.assertIn("COLOR_0", attributes)
                self.assertNotIn("COLOR_1", attributes)
                accessor = self.document["accessors"][attributes["COLOR_0"]]
                self.assertEqual(accessor["componentType"], 5121)
                self.assertTrue(accessor["normalized"])
                view = self.document["bufferViews"][accessor["bufferView"]]
                data = self.binary[view["byteOffset"]:view["byteOffset"] + view["byteLength"]]
                masks.extend(data[::4])
                self.assertTrue(all(value == 0 for value in data[2::4]))
        self.assertEqual(min(masks), 0)
        self.assertGreater(max(masks), 100)
        self.assertLess(max(masks), 255)

    def test_original_scene_is_still_default(self):
        project = (ROOT / "prototype/project.godot").read_text()
        self.assertIn('run/main_scene="res://main.tscn"', project)
        self.assertNotIn("style_study", project)
        self.assertNotIn("images", self.document)
        self.assertNotIn("animations", self.document)

    def test_still_capture_matrix_and_fingerprints(self):
        folder = ROOT / "docs/screenshots/style-study"
        drivers, kits = set(), {}
        expected = {"test1": 32, "test2": 8, "anchor": 2}
        for phase, count in expected.items():
            data = json.loads((folder / f"{phase}-provenance.json").read_text())
            self.assertEqual(len(data["captures"]), count)
            for record in data["captures"]:
                with self.subTest(capture=record["file"]):
                    image = ROOT / record["file"]
                    self.assertEqual(record["sha256"], hashlib.sha256(image.read_bytes()).hexdigest())
                    width, height = struct.unpack(">II", image.read_bytes()[16:24])
                    self.assertEqual(record["resolution"], [width, height])
                    self.assertIn([width, height], [[1920, 1080], [1280, 720]])
                    self.assertEqual(record["frames"][0]["clock"], 6.0)
                    self.assertEqual(record["movie"], "")
                    self.assertTrue(record["godot_version"].startswith("4.5.1."))
                    self.assertAlmostEqual(record["ambient"], 0.28)
                    self.assertAlmostEqual(record["fog_density"], 0.004)
                    drivers.add(record["driver"])
                    kits.setdefault(record["arm"], set()).add(record["asset_sha256"])
        self.assertEqual(len(drivers), 1)
        self.assertEqual(kits["A1"], kits["G1"])
        self.assertEqual(kits["G1"], kits["M1"])
        self.assertNotEqual(kits["A0"], kits["A1"])

    def test_comparison_is_self_contained(self):
        path = ROOT / "docs/boards/style-study-comparison.html"
        source = path.read_text()
        parser = ReportParser()
        parser.feed(source)
        for tag, attributes in parser.elements:
            for name in ["src", "srcset"]:
                if name in attributes:
                    self.assertTrue(attributes[name].startswith("data:"), (tag, attributes))
            self.assertNotEqual(attributes.get("rel"), "stylesheet")
        for pattern in [r"\bfetch\s*\(", r"\bXMLHttpRequest\b", r"\bWebSocket\b",
                        r"\bEventSource\b", r"\bsendBeacon\b", r"\bimport\s*\(",
                        r"@import\s", r"url\s*\(\s*[\"']?(https?:|//)"]:
            self.assertNotRegex(source, pattern)
        self.assertLess(path.stat().st_size, 6000 * 1024)

    def test_static_pigment_is_camera_anchored(self):
        metrics = json.loads((ROOT / "docs/screenshots/style-study/metrics.json").read_text())
        self.assertLess(metrics["anchor"]["aligned_mae_0_255"], 0.05)
        self.assertGreater(metrics["anchor"]["unaligned_mae_0_255"], 1.0)

    def test_motion_matrix_and_derived_boards(self):
        folder = ROOT / "docs/screenshots/style-study"
        records = json.loads((folder / "motion-provenance.json").read_text())["captures"]
        self.assertEqual(len(records), 15)
        matrix = set()
        for record in records:
            arm = record["arm"] + ("H" if record["atmosphere"] else "")
            matrix.add((arm, record["movie"]))
            self.assertEqual(record["fps"], 15)
            self.assertEqual(len(record["frames"]), 120)
            self.assertEqual(len(record["frame_sha256"]), 120)
            self.assertEqual(record["encoded_video"]["nb_frames"], "120")
            self.assertEqual(record["encoded_video"]["r_frame_rate"], "15/1")
            self.assertEqual(float(record["encoded_video"]["duration"]), 8.0)
            self.assertEqual(record["resolution"], [1280, 720])
            self.assertTrue(record["rain"] and record["wind"] and record["reflections"])
            for index, frame in enumerate(record["frames"]):
                self.assertAlmostEqual(frame["clock"], 6 + index / 15)
            start, end = record["frames"][0], record["frames"][-1]
            if record["movie"] == "orbit":
                self.assertAlmostEqual(start["yaw"], 0.07)
                self.assertAlmostEqual(end["yaw"], 1.07)
                self.assertEqual(start["size"], 20.5)
            elif record["movie"] == "zoom":
                self.assertEqual(start["size"], 5.0)
                self.assertEqual(end["size"], 13.5)
                self.assertEqual(start["yaw"], end["yaw"])
            else:
                self.assertEqual(start["size"], end["size"])
                self.assertEqual(start["yaw"], end["yaw"])
        self.assertEqual(matrix, {(arm, movie) for arm in ["A0", "A1", "G1", "M1", "G1H"]
                                  for movie in ["orbit", "weather", "zoom"]})
        boards = json.loads((folder / "motion-boards.json").read_text())["boards"]
        self.assertEqual(len(boards), 6)
        for board in boards:
            path = ROOT / board["file"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), board["sha256"])
            self.assertLess(path.stat().st_size, 6000 * 1024)


if __name__ == "__main__":
    unittest.main()
