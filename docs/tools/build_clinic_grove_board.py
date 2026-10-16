"""Arrange unmodified Godot captures; no synthesis, crop or retouching."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


DOCS = Path(__file__).resolve().parents[1]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
board = Image.new('RGB', (1840, 1390), '#151e20')
draw = ImageDraw.Draw(board)
heading = ImageFont.truetype(FONT, 32)
label = ImageFont.truetype(FONT, 21)
small = ImageFont.truetype(FONT, 17)
draw.text((30, 23), 'BETTER SOURCE ASSETS, NOT A STRONGER FILTER', font=heading, fill='#e6e0d0')
draw.text((30, 70), 'Actual Godot 4.5.1 / Compatibility viewports. No AI paint-over or screen-space treatment.', font=small, fill='#aab6b1')
panels = [
    ('structured-forest/daylight', '01 / EARLIER PROCEDURAL SLICE', 'Preserved capture: regular crown tiers and mostly bare ground.'),
    ('clinic-grove-v1/daylight', '02 / AUTHORED CONIFERS + TEXTURED GROUND', 'Identical camera; assets, dressing, materials and lighting changed.'),
    ('clinic-grove-v1/tree', '03 / ISOLATED ASSET IN DAYLIGHT', 'CC0 Poly Haven fir LOD2; fixed geometry, lit needle cutouts.'),
    ('clinic-grove-v1/approach', '04 / APPROACH CAMERA', 'Open path, grounded rocks and ferns; original clinic/traveler retained.'),
]
for index, (path, title, note) in enumerate(panels):
    x = 30 + (index % 2) * 900
    y = 120 + (index // 2) * 605
    draw.text((x, y), title, font=label, fill='#d8d2bb')
    source = Image.open(DOCS / 'screenshots' / (path + '.png')).convert('RGB')
    board.paste(source.resize((870, 544), Image.Resampling.LANCZOS), (x, y + 34))
    draw.text((x, y + 581), note, font=ImageFont.truetype(FONT, 15), fill='#aab6b1')
draw.text((30, 1342), 'Visual candidate, not final art. Higher geometry cost; llvmpipe is not target-device performance evidence.', font=small, fill='#aab6b1')
board.save(DOCS / 'boards/clinic-grove-comparison.jpg', quality=93)
