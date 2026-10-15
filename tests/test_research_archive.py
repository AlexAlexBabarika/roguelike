"""Offline checks for the migrated research library; standard library only."""

import base64
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MANIFEST = json.loads((DOCS / "manifest.json").read_text())
REPORT_NAMES = {
    "last-window-art-directions.html",
    "art-directions.html",
    "isometric-art-directions.html",
    "new-art-directions.html",
    "shader-production-guide.html",
    "game-loop-design-report.html",
}
BOARD_NAMES = {
    "three-directions.png",
    "art-directions-board.jpg",
    "isometric-art-directions-board.jpg",
    "new-art-directions-board.jpg",
    "storm-fresco-engine-comparison-board.jpg",
    "style-study-comparison.html",
    "painted-forest-comparison.jpg",
}
CAPTURE_NAMES = {
    "A_october_wind_up.png",
    "B_october_wind_up.png",
    "C_october_wind_up.png",
    "B_october_strike_echo.png",
    "C_october_mid_dodge.png",
    "B_month_may.png",
    "B_month_august.png",
    "B_month_november.png",
    "B_october_title_card.png",
    "derived_greyscale_C_october_wind_up.png",
    "derived_deuteranopia_C_october_wind_up.png",
}
MECHANICS_BRIEF = (
    "You know I was also thinking about building a souls like game with isometric "
    "perspective which would combine some rogue like elements from games like Dead "
    "Cells. It would also combine scaling/multiplication mechanics from Balatro where "
    "the games forces a player to experiment with builds, effects (such as card "
    "effects), buffs, and right experiments would lead to crazily fun experience"
)


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)


class ResearchArchiveTests(unittest.TestCase):
    def test_complete_inventory(self):
        paths = [item["path"] for item in MANIFEST["reports"]]
        self.assertEqual(len(paths), 6)
        self.assertEqual({Path(path).name for path in paths}, REPORT_NAMES)
        self.assertEqual(
            {path.name for path in (DOCS / "reports").glob("*.html")},
            REPORT_NAMES,
        )
        self.assertEqual(len(MANIFEST["boards"]), len(BOARD_NAMES))
        self.assertEqual({Path(item["path"]).name for item in MANIFEST["boards"]}, BOARD_NAMES)
        self.assertEqual({path.name for path in (DOCS / "boards").iterdir()}, BOARD_NAMES)
        for item in MANIFEST["reports"]:
            with self.subTest(report=item["path"]):
                self.assertTrue(item["title"])
                self.assertTrue(item["status"])
                self.assertTrue(item["description"])

    def test_fingerprints_and_local_paths(self):
        for item in (MANIFEST["reports"] + MANIFEST["boards"]
                     + MANIFEST["captures"] + MANIFEST["supporting_documents"]):
            with self.subTest(path=item["path"]):
                path = (DOCS / item["path"]).resolve()
                self.assertTrue(path.is_relative_to(DOCS))
                self.assertTrue(path.is_file())
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"]
                )

    def test_engine_capture_inventory_and_provenance(self):
        folder = DOCS / "screenshots" / "storm-fresco"
        self.assertEqual({path.name for path in folder.glob("*.png")}, CAPTURE_NAMES)
        self.assertEqual(len(MANIFEST["captures"]), len(CAPTURE_NAMES))
        self.assertEqual({Path(item["path"]).name for item in MANIFEST["captures"]}, CAPTURE_NAMES)
        provenance = json.loads((folder / "provenance.json").read_text())
        records = {item["path"]: item for item in provenance["captures"]}
        self.assertEqual(len(records), len(CAPTURE_NAMES))
        self.assertEqual(sum(item["kind"] == "Godot capture" for item in records.values()), 9)
        self.assertEqual(sum(item["kind"] == "script-derived accessibility image"
                             for item in records.values()), 2)
        for item in MANIFEST["captures"]:
            with self.subTest(capture=item["path"]):
                record = records[item["path"]]
                self.assertEqual(record["sha256"], item["sha256"])
                self.assertEqual(record["kind"], item["kind"])
                data = (DOCS / item["path"]).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(data[12:16], b"IHDR")
                self.assertEqual(struct.unpack(">II", data[16:24]), (1920, 1080))
                self.assertEqual(record["resolution"], [1920, 1080])
                self.assertIn(record["source_capture"], CAPTURE_NAMES)
                self.assertTrue(record["overlay_ignores_world_occlusion"])
        self.assertTrue((DOCS / provenance["board"]["generator"]).is_file())
        self.assertTrue((DOCS / provenance["board"]["path"]).is_file())

    def test_complete_self_contained_documents(self):
        for item in MANIFEST["reports"]:
            with self.subTest(report=item["path"]):
                source = (DOCS / item["path"]).read_text()
                parser = ReportParser()
                parser.feed(source)
                tags = {tag for tag, _ in parser.elements}
                self.assertTrue({"html", "head", "body", "h1"}.issubset(tags))
                ids = [attrs["id"] for _, attrs in parser.elements if "id" in attrs]
                self.assertEqual(len(ids), len(set(ids)), "Duplicate HTML IDs")
                for tag, attrs in parser.elements:
                    for attribute in ("src", "srcset", "poster"):
                        if attribute in attrs:
                            value = attrs[attribute]
                            self.assertTrue(value.startswith("data:"), (tag, attribute))
                            if ";base64," in value:
                                base64.b64decode(value.split(",", 1)[1], validate=True)
                    if tag == "link":
                        self.assertNotIn("stylesheet", attrs.get("rel", ""))
                    href = attrs.get("href", "")
                    if href.startswith("#") and len(href) > 1:
                        self.assertIn(href[1:], ids, "Broken local reference")
                forbidden = (
                    r"\bfetch\s*\(",
                    r"\bXMLHttpRequest\b",
                    r"\bWebSocket\b",
                    r"\bEventSource\b",
                    r"\bsendBeacon\b",
                    r"\bimport\s*\(",
                    r"@import\s",
                    r"url\s*\(\s*[\"']?(https?:|//)",
                )
                for pattern in forbidden:
                    self.assertIsNone(re.search(pattern, source), pattern)

    def test_verbatim_mechanics_brief(self):
        parser = ReportParser()
        parser.feed((DOCS / "reports" / "game-loop-design-report.html").read_text())
        self.assertIn(MECHANICS_BRIEF, " ".join(parser.text))

    def test_markdown_local_links(self):
        for path in [ROOT / "README.md", *DOCS.glob("*.md"), ROOT / "prototype" / "README.md"]:
            for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
                if re.match(r"^[a-z]+://", link) or link.startswith("#"):
                    continue
                with self.subTest(document=path.name, link=link):
                    self.assertTrue((path.parent / link.split("#", 1)[0]).exists())


if __name__ == "__main__":
    unittest.main()
