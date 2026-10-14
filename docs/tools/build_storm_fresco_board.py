"""Compose a derived comparison board from the archived engine captures."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DOCS = Path(__file__).resolve().parents[1]
SHOTS = DOCS / "screenshots" / "storm-fresco"
OUTPUT = DOCS / "boards" / "storm-fresco-engine-comparison-board.jpg"
PAPER = "#f4f1ea"
INK = "#20241f"
MUTED = "#545a52"
MARGIN = 44
GAP = 32
WIDTH = 2400
COLUMN = (WIDTH - 2 * MARGIN - 2 * GAP) // 3


def build(font_dir):
    def font(size, bold=False):
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(str(font_dir / name), size)

    board = Image.new("RGB", (WIDTH, 3500), PAPER)
    draw = ImageDraw.Draw(board)

    def text(x, y, value, size=28, bold=False, color=INK):
        draw.text((x, y), value, font=font(size, bold), fill=color)

    def image(name, x, y, width, crop=None):
        with Image.open(SHOTS / (name + ".png")) as source:
            frame = source.convert("RGB")
        if crop:
            frame = frame.crop(crop)
        height = round(frame.height * width / frame.width)
        frame = frame.resize((width, height), Image.Resampling.LANCZOS)
        board.paste(frame, (x, y))
        return height

    text(MARGIN, 34, "Storm Fresco — cheap models through the combat camera", 52, True)
    text(MARGIN, 109, "Actual Godot captures, not concept illustrations. Same assets, pose, camera and rain in A / B / C.", 29, color=MUTED)
    text(MARGIN, 152, "Blender 4.5.3  /  Godot 4.5.1 Compatibility  /  orthographic size 19  /  source captures 1920 × 1080", 26, color=MUTED)

    treatments = [
        ("A_october_wind_up", "01  A / Matte fresco", "No world print; broad forms stay quieter.", "Solid blade and warning; weak enemy facing."),
        ("B_october_wind_up", "02  B / Global print", "Strongest print character; busier ground/trees.", "Gameplay bypasses the dotted world."),
        ("C_october_wind_up", "03  C / Local print", "Fresco outside the warning/echo radius.", "Useful compromise; ellipse is conspicuous."),
    ]
    for index, (name, title, first, second) in enumerate(treatments):
        x = MARGIN + index * (COLUMN + GAP)
        text(x, 220, title, 34, True)
        height = image(name, x, 275, COLUMN)
        text(x, 275 + height + 16, first, 25)
        text(x, 275 + height + 54, second, 25, color=MUTED)

    text(MARGIN, 810, "Combat detail / derived crops, not additional resolution", 35, True)
    text(MARGIN, 862, "Identical 480 × 320 source region; enlarged for model and pattern inspection. No retouching.", 27, color=MUTED)
    for index, (name, _, _, _) in enumerate(treatments):
        x = MARGIN + index * (COLUMN + GAP)
        image(name, x, 920, COLUMN, crop=(750, 390, 1230, 710))
    text(MARGIN, 1440, "The damage boundary is the thin sector keyline—not C’s surrounding print ellipse. Facing still needs work.", 28)

    text(MARGIN, 1530, "Held-pose and title studies / Godot", 35, True)
    studies = [
        ("B_october_strike_echo", "B / Strike + light-ink echo", "A frozen pose, not validated combat motion."),
        ("C_october_mid_dodge", "C / Mid-dodge", "Blade remains solid outside the print layer."),
        ("B_october_title_card", "October / Model silhouette", "Godot typography; not a painted reference."),
    ]
    for index, (name, title, caption) in enumerate(studies):
        x = MARGIN + index * (COLUMN + GAP)
        height = image(name, x, 1590, COLUMN)
        text(x, 1590 + height + 14, title, 28, True)
        text(x, 1590 + height + 56, caption, 24, color=MUTED)

    text(MARGIN, 2130, "Month swaps / B world print, identical danger red", 35, True)
    month_width = (WIDTH - 2 * MARGIN - 3 * GAP) // 4
    for index, (name, month) in enumerate([
        ("B_month_may", "May / mint green"),
        ("B_month_august", "August / amber"),
        ("B_october_wind_up", "October / ochre"),
        ("B_month_november", "November / pale earth"),
    ]):
        x = MARGIN + index * (month_width + GAP)
        height = image(name, x, 2190, month_width)
        text(x, 2190 + height + 12, month, 26, True)

    text(MARGIN, 2600, "Accessibility spot check / C combat detail", 35, True)
    text(MARGIN, 2652, "Derived greyscale and deuteranopia simulation; still-image comparison, not accessibility certification.", 27, color=MUTED)
    accessibility = [
        ("C_october_wind_up", "C / Original color"),
        ("derived_greyscale_C_october_wind_up", "Derived / Rec.709 greyscale"),
        ("derived_deuteranopia_C_october_wind_up", "Derived / Deuteranopia simulation"),
    ]
    for index, (name, title) in enumerate(accessibility):
        x = MARGIN + index * (COLUMN + GAP)
        height = image(name, x, 2710, COLUMN, crop=(750, 390, 1230, 710))
        text(x, 2710 + height + 14, title, 27, True)

    footer_y = 2710 + round(320 * COLUMN / 480) + 95
    draw.line((MARGIN, footer_y, WIDTH - MARGIN, footer_y), fill="#d0cec4", width=2)
    text(MARGIN, footer_y + 20, "DERIVED BOARD / resized and cropped from real engine captures. Full-resolution PNGs are archived separately.", 26, True)
    text(MARGIN, footer_y + 67, "Still-image look-dev only: overlay ignores world occlusion; no motion, live reflections or device performance validation.", 25, color=MUTED)
    text(MARGIN, footer_y + 108, "No art direction selected. See docs/STORM_FRESCO.md for measurements, greyscale/deuteranopia examples and provenance.", 25, color=MUTED)
    return board.crop((0, 0, WIDTH, footer_y + 165))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font-dir", type=Path, default=Path("/usr/share/fonts/truetype/dejavu"))
    args = parser.parse_args()
    build(args.font_dir).save(OUTPUT, quality=95, subsampling=0)
    print(OUTPUT)
