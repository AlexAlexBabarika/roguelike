"""Build the deterministic painted spruce-card atlas and tree anchors for I1."""

import ast
import hashlib
import json
import math
import random
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/build_mock_scene.py"
OUT = ROOT / "assets"
TILE = 256


def crowns():
    tree = ast.parse(SOURCE.read_text())
    forest = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "forest")
    positions = ast.literal_eval(forest.body[0].value)
    return [
        {
            "position": [x, -0.05 + 0.075 * math.sin(x * 0.65) * math.cos(y * 0.6)
                         + 0.06 * math.sin(y * 0.37), -y],
            "height": h,
        }
        for x, y, h in positions
    ]


def paint_tile(seed):
    rng = random.Random(40217 + seed)
    mask = Image.new("L", (TILE, TILE))
    ink = ImageDraw.Draw(mask)
    widths = []
    for row in range(12):
        y = 36 + row * 16
        width = 91 * math.sin(math.pi * (row + 0.5) / 12) ** 0.7
        widths.append(width * rng.uniform(0.88, 1.1))
        ink.ellipse((128 - width, y - 12, 128 + width, y + 15), fill=245)
    for _ in range(75):
        y = rng.uniform(42, 205)
        row = min(11, max(0, int((y - 36) / 16)))
        side = rng.choice((-1, 1))
        x = 128 + side * rng.uniform(0.4, 0.95) * widths[row]
        ink.ellipse((x - rng.uniform(8, 18), y - rng.uniform(6, 14),
                     x + rng.uniform(8, 18), y + rng.uniform(9, 22)), fill=220)
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    tile = Image.new("RGBA", (TILE, TILE), (31, 54, 49, 0))
    tile.putalpha(mask)
    strokes = Image.new("RGBA", tile.size)
    brush = ImageDraw.Draw(strokes)
    for _ in range(75):
        y = rng.uniform(42, 205)
        row = min(11, max(0, int((y - 36) / 16)))
        x = 128 + rng.uniform(-0.86, 0.86) * widths[row]
        shade = rng.choice([(82, 111, 91, 80), (107, 126, 95, 75),
                            (17, 38, 39, 78), (45, 76, 68, 105)])
        brush.line((x, y, x + rng.uniform(-18, 18), y + rng.uniform(7, 25)),
                   fill=shade, width=rng.randint(5, 12))
    tile = Image.alpha_composite(tile, strokes.filter(ImageFilter.GaussianBlur(1)))
    # Strokes must not reintroduce rectangular alpha outside the silhouette.
    tile.putalpha(mask)
    return tile


def main():
    atlas = Image.new("RGBA", (TILE * 2, TILE * 2))
    for index in range(4):
        atlas.paste(paint_tile(index), ((index % 2) * TILE, (index // 2) * TILE))
    source = OUT / "painted-boughs-source.png"
    if source.exists():
        atlas = Image.open(source).convert("RGBA")
        pixels = []
        for r, g, b, _ in struct.iter_unpack("BBBB", atlas.tobytes()):
            chroma = min(r, b) - g
            alpha = round(255 * min(1, max(0, (140 - chroma) / 100)))
            value = min(1, max(0, g / 150))
            color = tuple(round(a + (b - a) * value) for a, b in zip((16, 31, 31), (105, 127, 91)))
            pixels.append((*color, alpha))
        atlas.putdata(pixels)
    image_path = OUT / "painted-crowns.png"
    atlas.save(image_path, optimize=True)
    (OUT / "painted-crowns.json").write_text(json.dumps({
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "seed": 40217, "crowns": crowns(),
        "atlas_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "texture_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else None,
        "note": ("AI-generated gouache bough atlas (gpt-image-2.5-flare), used as an in-engine texture. "
                 "Procedural Blender geometry, not AI mesh evidence.") if source.exists()
                else "Procedural paint stamps, not AI concept art or AI mesh evidence.",
    }, indent=2) + "\n")
    print(f"PAINTED_CROWNS: {len(crowns())} crowns, 4 stamps")


if __name__ == "__main__":
    main()
