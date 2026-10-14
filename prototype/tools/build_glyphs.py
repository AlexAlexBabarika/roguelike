"""Optional atlas regeneration: python tools/build_glyphs.py [monospace.ttf]."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
font_path = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
font = ImageFont.truetype(font_path, 22)
glyphs = " .,:;+=ox%#@/\\()~-|-"
assert len(glyphs) == 20
atlas = Image.new("RGB", (20 * 18, 28), "black")
draw = ImageDraw.Draw(atlas)
for index, glyph in enumerate(glyphs):
    draw.text((index * 18 + 9, 14), glyph, font=font, anchor="mm", fill="white")
atlas.save(ROOT / "assets" / "glyph-atlas.png")
print("Wrote 20-glyph atlas")
