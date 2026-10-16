"""Arrange unmodified Godot captures from both revisions; no image retouching."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


DOCS = Path(__file__).resolve().parents[1]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
board = Image.new('RGB', (1840, 1390), '#151e20')
draw = ImageDraw.Draw(board)
heading = ImageFont.truetype(FONT, 32)
label = ImageFont.truetype(FONT, 21)
small = ImageFont.truetype(FONT, 17)
draw.text((30, 23), '02 REFINED / THE CLINIC GROVE IN DAYLIGHT', font=heading, fill='#e6e0d0')
draw.text((30, 70), 'Actual Godot 4.5.1 Compatibility captures. Matched camera and resolution; no fog or screen filter.', font=small, fill='#aab6b1')
panels = [
    ('clinic-grove-v1/daylight', '02A / PRIOR AUTHORED CONTEXT', 'Repeated bright leaf-litter texture; weak path separation.'),
    ('clinic-grove/daylight', '02B / REFINED AUTHORED CONTEXT', 'Worn approach, mottled moss/litter, deeper tree clusters.'),
    ('clinic-grove-v1/approach', '04A / PRIOR APPROACH', 'Earlier ground treatment and brighter traveler/clinic.'),
    ('clinic-grove/approach', '04B / REFINED APPROACH', 'Same camera; dry daylight, real shadows, stronger path.'),
]
for index, (path, title, note) in enumerate(panels):
    x = 30 + (index % 2) * 900
    y = 120 + (index // 2) * 605
    draw.text((x, y), title, font=label, fill='#d8d2bb')
    source = Image.open(DOCS / 'screenshots' / (path + '.png')).convert('RGB')
    board.paste(source.resize((870, 544), Image.Resampling.LANCZOS), (x, y + 34))
    draw.text((x, y + 581), note, font=ImageFont.truetype(FONT, 15), fill='#aab6b1')
draw.text((30, 1342), 'Not a shader-only A/B: terrain, trees, lighting, clinic color and dressing changed. llvmpipe is not target-device proof.', font=small, fill='#aab6b1')
board.save(DOCS / 'boards/clinic-grove-refinement.jpg', quality=93)
