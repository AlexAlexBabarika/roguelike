"""Integrity checks for the separate Blender/Godot art mock; stdlib only."""

import hashlib
import json
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
CAPTURES = ROOT / "docs/screenshots/forest-clinic"
GROUPS = {"Ground", "Clinic", "Windows", "Porch", "Roof", "Forest",
          "Undergrowth", "Props", "Traveler"}


class MockSceneTests(unittest.TestCase):
    def test_embedded_original_kit(self):
        path = ROOT / "prototype/assets/forest-clinic.glb"
        data = path.read_bytes()
        self.assertLess(len(data), 6000 * 1024)
        self.assertEqual(struct.unpack("<4sII", data[:12]), (b"glTF", 2, len(data)))
        length, kind = struct.unpack("<I4s", data[12:20])
        self.assertEqual(kind, b"JSON")
        gltf = json.loads(data[20:20 + length])
        self.assertEqual({node["name"] for node in gltf["nodes"] if "mesh" in node}, GROUPS)
        self.assertFalse(gltf.get("images"), "The kit should not depend on image textures")
        self.assertFalse(gltf.get("skins"), "The traveler is not advertised as rigged")
        for buffer in gltf["buffers"]:
            self.assertNotIn("uri", buffer, "The kit must be self-contained")
        metadata = json.loads(path.with_suffix(".json").read_text())
        self.assertEqual(metadata["seed"], 40217)
        self.assertEqual(metadata["blender"], "4.5.3 LTS")
        self.assertEqual(set(metadata["groups"]), GROUPS)
        for counts in metadata["groups"].values():
            self.assertGreater(counts["vertices"], 100)
            self.assertGreater(counts["polygons"], 100)

    def test_engine_captures_and_source_fingerprints(self):
        provenance = json.loads((CAPTURES / "provenance.json").read_text())
        self.assertEqual(provenance["seed"], 40217)
        self.assertEqual(provenance["msaa_samples"], 4)
        self.assertEqual(provenance["capture_settle_frames"], 20)
        names = {"wide.png", "clinic.png", "traveler.png"}
        self.assertEqual({path.name for path in CAPTURES.glob("*.png")}, names)
        self.assertEqual({item["path"] for item in provenance["captures"]}, names)
        for item in provenance["sources"]:
            path = (ROOT / item["path"]).resolve()
            self.assertTrue(path.is_relative_to(ROOT))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
        for item in provenance["captures"]:
            with self.subTest(capture=item["path"]):
                data = (CAPTURES / item["path"]).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(struct.unpack(">II", data[16:24]), (1920, 1080))
                self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])
                self.assertEqual(item["kind"], "Godot capture")
                self.assertIn("Compatibility", item["driver"])
                settings = item["settings"]
                self.assertTrue(settings["engine"].startswith("4.5.1"))
                self.assertEqual(settings["resolution"], [1920, 1080])
                self.assertEqual(settings["projection"], "orthographic")
                self.assertEqual(settings["clock_seconds"], 6)
                self.assertEqual(settings["preset"], Path(item["path"]).stem)
                self.assertTrue(all(settings[flag] for flag in ("rain", "wind", "reflections")))


if __name__ == "__main__":
    unittest.main()
