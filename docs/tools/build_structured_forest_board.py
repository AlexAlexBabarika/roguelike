"""Arrange unpainted engine captures. Requires Pillow, not needed to run Godot."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


DOCS = Path(__file__).resolve().parents[1]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
board = Image.new('RGB', (1640, 1240), '#131d20')
draw = ImageDraw.Draw(board)
heading = ImageFont.truetype(FONT, 32)
label = ImageFont.truetype(FONT, 21)
small = ImageFont.truetype(FONT, 17)
draw.text((28, 23), 'STRUCTURE BEFORE ATMOSPHERE', font=heading, fill='#e5e1d1')
draw.text((28, 68), 'Actual Godot 4.5.1 / Compatibility captures — no AI paint-over or screen-space filter', font=small, fill='#9badac')
panels = [
    ('daylight', '01 / DAYLIGHT CONTEXT', 'No fog, rain or reflections. Original clinic/traveler retained.'),
    ('spruce', '02 / ISOLATED SPRUCE', 'Tapered trunk, woody boughs, fixed branch cutouts, real shadows.'),
    ('silhouette', '03 / SILHOUETTE CHECK', 'Same inspection camera. Crown gaps are geometry, not a filter.'),
    ('weather', '04 / OPTIONAL WEATHER', 'Same context camera. Atmosphere comes after the daylight proof.'),
]
for index, (name, title, note) in enumerate(panels):
    x = 28 + (index % 2) * 806
    y = 120 + (index // 2) * 536
    draw.text((x, y), title, font=label, fill='#d6cfb3')
    source = Image.open(DOCS / 'screenshots/structured-forest' / f'{name}.png').convert('RGB')
    source = source.resize((778, 486), Image.Resampling.LANCZOS)
    board.paste(source, (x, y + 34))
    draw.text((x, y + 522), note, font=ImageFont.truetype(FONT, 12), fill='#9badac')
draw.text((28, 1204), 'Original procedural assets / three spruce variants / llvmpipe is not target-device performance evidence.', font=small, fill='#9badac')
board.save(DOCS / 'boards/structured-forest.jpg', quality=93)
