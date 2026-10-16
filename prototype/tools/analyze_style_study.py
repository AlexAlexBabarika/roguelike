"""Sample matched frames; report descriptive image metrics, not playability scores."""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
FRAMES = ROOT / "docs/screenshots/style-study"
OUTPUT = ROOT / "artifacts/style-study"
ROIS = {
    "crown": [0.20, 0.35, 0.26, 0.43],
    "roof": [0.57, 0.33, 0.615, 0.37],
    "ground": [0.20, 0.81, 0.24, 0.85],
    "path": [0.369, 0.898, 0.385, 0.919],
    "cloak": [0.407, 0.706, 0.422, 0.732],
    "rock": [0.520, 0.735, 0.526, 0.748],
    "enemy": [0.459, 0.718, 0.468, 0.745],
    "enemy_floor": [0.477, 0.779, 0.486, 0.793],
    "warning": [0.442, 0.783, 0.456, 0.790],
    "window": [0.414, 0.440, 0.422, 0.453],
    "blade": [0.436, 0.713, 0.451, 0.732],
}
MATRICES = {
    "protan": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
    "deutan": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
    "tritan": [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
}


def linear(rgb):
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def encode(rgb):
    rgb = np.clip(rgb, 0, 1)
    return np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - 0.055)


def crop(image, box):
    height, width = image.shape[:2]
    x0, y0, x1, y1 = [round(v * (width if i % 2 == 0 else height)) for i, v in enumerate(box)]
    return image[y0:y1, x0:x1]


def luma(rgb):
    return linear(rgb) @ np.array([0.2126, 0.7152, 0.0722])


def measure(rgb):
    results = {}
    for name, box in ROIS.items():
        region = crop(rgb, box)
        values = luma(region)
        results[name] = round(float(encode(values.mean()) * 255), 2)
        if name == "roof":
            encoded = encode(values) * 255
            results["roof_edge_energy"] = round(float(np.mean(abs(np.diff(encoded, axis=0)))
                                                     + np.mean(abs(np.diff(encoded, axis=1)))), 3)
        if name == "blade":
            results["blade_p99"] = round(float(encode(np.percentile(values, 99)) * 255), 2)
    results["cloak_path_delta"] = round(results["cloak"] - results["path"], 2)
    results["enemy_floor_delta"] = round(results["enemy_floor"] - results["enemy"], 2)
    results["crown_roof_ground_min_gap"] = round(min(abs(results[a] - results[b])
        for a, b in [("crown", "roof"), ("crown", "ground"), ("roof", "ground")]), 2)
    return results


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    result = {"method": "Linear-light Rec.709 ROI mean, encoded back to sRGB 0-255. Hand-picked normalized rectangles; not a perceptual/playability score.",
              "rois": ROIS, "color_vision": "Machado et al. 2009 severity 1.0; linear RGB transforms clipped to display gamut.",
              "matrices": MATRICES, "arms": {}}
    for arm in ["A0", "A1", "G1", "M1", "G1H", "M1H"]:
        path = FRAMES / f"{arm}-wide-1920x1080.png"
        if not path.exists():
            continue
        rgb = np.asarray(Image.open(path).convert("RGB"), dtype=float) / 255
        result["arms"][arm] = {"color": measure(rgb)}
        for name, matrix in MATRICES.items():
            converted = encode(linear(rgb) @ np.array(matrix).T)
            result["arms"][arm][name] = measure(converted)
        annotated = Image.open(path).convert("RGB")
        draw = ImageDraw.Draw(annotated)
        for name, box in ROIS.items():
            coords = [round(v * (annotated.width if i % 2 == 0 else annotated.height)) for i, v in enumerate(box)]
            draw.rectangle(coords, outline="white", width=2)
            draw.text((coords[0], coords[1] - 14), name, fill="white", stroke_width=2, stroke_fill="black")
        annotated.save(OUTPUT / f"{arm}-roi-map.jpg", quality=90)
    anchor_a = FRAMES / "G1-anchor-0-clinic-1920x1080.png"
    anchor_b = FRAMES / "G1-anchor-64-clinic-1920x1080.png"
    if anchor_a.exists() and anchor_b.exists():
        a = np.asarray(Image.open(anchor_a).convert("RGB"), dtype=float)
        b = np.asarray(Image.open(anchor_b).convert("RGB"), dtype=float)
        # Static roof, safely away from silhouettes. Pan moves the scene 64 pixels left.
        box = [0.57, 0.30, 0.62, 0.34]
        shifted = np.zeros_like(a)
        shifted[:, 64:] = b[:, :-64]
        result["anchor"] = {"roi": box, "pan_pixels": 64,
                            "aligned_mae_0_255": float(np.abs(crop(a, box) - crop(shifted, box)).mean()),
                            "unaligned_mae_0_255": float(np.abs(crop(a, box) - crop(b, box)).mean()),
                            "scope": "Emission-only pigment diagnostic on a static roof; not whole-scene or foliage temporal stability."}
    (FRAMES / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
