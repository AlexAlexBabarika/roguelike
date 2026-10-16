"""Build a labelled derived board without modifying the archived engine frames."""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "docs/screenshots/style-study"


def main():
    board = Image.new("RGB", (1920, 1860), "#101a1b")
    draw = ImageDraw.Draw(board)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 26)
    small = ImageFont.truetype(font_path, 20)
    draw.text((24, 18), "BEFORE · G1 / rejected material-only result", font=font, fill="#e1e6dd")
    draw.text((984, 18), "FOLLOW-UP · I1 / painted crowns + selective filter", font=font, fill="#e1e6dd")
    sources = {}
    for row, view in enumerate(["wide", "clinic", "traveler"]):
        y = 74 + row * 576
        draw.text((24, y - 24), view.upper(), font=small, fill="#a8c6b7")
        for column, arm in enumerate(["G1", "I1"]):
            path = FOLDER / f"{arm}-{view}-1920x1080.png"
            sources[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            with Image.open(path) as image:
                board.paste(image.convert("RGB").resize((960, 540), Image.Resampling.LANCZOS),
                            (column * 960, y))
    draw.text((24, 1810), "Actual Godot frames · matched cameras/light/weather · I1 uses an AI foliage texture, not an AI paint-over", font=small, fill="#c4cec4")
    destination = ROOT / "docs/boards/painted-forest-comparison.jpg"
    board.save(destination, quality=95, subsampling=0)
    (FOLDER / "painted-board.json").write_text(json.dumps({
        "kind": "Script-derived board: labelled and resized Godot captures, no generative retouching",
        "sources": sources,
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
    }, indent=2) + "\n")
    manifest_path = ROOT / "docs/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    entry = {"path": "boards/painted-forest-comparison.jpg",
             "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}
    manifest["boards"] = [item for item in manifest["boards"] if item["path"] != entry["path"]] + [entry]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
