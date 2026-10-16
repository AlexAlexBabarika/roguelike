"""Bake a terrain material field from pinned CC0 maps; never process the screen.

Requires NumPy and Pillow only to rebuild. Runtime uses two ordinary textures.
"""

import hashlib
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'assets/reference-forest'
TARGET = ROOT / 'assets/grove-terrain'
SPAN = 64.0
SIZE = 2048
SOURCE_RESOLUTION = 64


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def smooth(a, b, value):
    f = np.clip((value - a) / (b - a), 0, 1)
    return f * f * (3 - 2 * f)


def fract(value):
    return value - np.floor(value)


def noise(x, y):
    ix, iy = np.floor(x), np.floor(y)
    fx, fy = smooth(0, 1, fract(x)), smooth(0, 1, fract(y))

    def point(a, b):
        return fract(np.sin(a * 127.1 + b * 311.7) * 43758.5453)

    return ((point(ix, iy) * (1 - fx) + point(ix + 1, iy) * fx) * (1 - fy)
            + (point(ix, iy + 1) * (1 - fx) + point(ix + 1, iy + 1) * fx) * fy)


def load_map(name, normal=False):
    # Prefilter source detail to the field's texel density before random sampling.
    image = Image.open(SOURCES / name).convert('RGB').resize(
        (SOURCE_RESOLUTION, SOURCE_RESOLUTION), Image.Resampling.LANCZOS
    )
    values = np.asarray(image, dtype=np.float32) / 255
    if not normal:
        values = np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4)
    return values


def sample(image, u, v):
    x, y = fract(u) * image.shape[1], fract(v) * image.shape[0]
    ix, iy = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - ix)[..., None], (y - iy)[..., None]
    height, width = image.shape[:2]
    a, b = image[iy % height, ix % width], image[iy % height, (ix + 1) % width]
    c, d = image[(iy + 1) % height, ix % width], image[(iy + 1) % height, (ix + 1) % width]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def patch_samples(image, x, z, scale, vertices, weights):
    result = np.zeros((*x.shape, 3))
    for (a, b), weight in zip(vertices, weights):
        u = fract(np.sin(a * 127.1 + b * 311.7) * 43758.5453) * 17
        v = fract(np.sin(a * 269.5 + b * 183.3) * 43758.5453) * 17
        result += sample(image, x * scale + u, z * scale + v) * weight[..., None]
    return result


def lerp(a, b, weight):
    return a * (1 - weight[..., None]) + b * weight[..., None]


def layout():
    source = (ROOT / 'clinic_grove.gd').read_text().split('const FIR_PLACEMENTS := [')[1].split('\n]')[0]
    pattern = r'Vector3\(([-\d.]+), 0, ([-\d.]+)\), \d, [-\d.]+, ([-\d.]+)'
    result = [[float(x), float(z), float(size) * 5] for x, z, size in re.findall(pattern, source)]
    if len(result) != 19:
        raise ValueError('Expected nineteen tree roots for this terrain revision')
    return result


def main():
    TARGET.mkdir(exist_ok=True)
    roots = layout()
    names = ['forest_floor', 'mossy_rock', 'forrest_ground_01']
    colors = [load_map(name + '_diff.jpg') for name in names]
    normals = [load_map(name + '_nor_gl.jpg', normal=True) for name in names]
    output = np.empty((SIZE, SIZE, 3), dtype=np.uint8)
    normal_output = np.empty_like(output)
    for start in range(0, SIZE, 64):
        x, z = np.meshgrid((np.arange(SIZE) + 0.5) / SIZE * SPAN - SPAN / 2,
                           (np.arange(start, min(start + 64, SIZE)) + 0.5) / SIZE * SPAN - SPAN / 2)
        gx, gz = (x - z * 0.57735) * 0.23, z * 1.1547 * 0.23
        cx, cz, fx, fz = np.floor(gx), np.floor(gz), fract(gx), fract(gz)
        upper = fx + fz > 1
        vertices = [(cx + upper, cz + upper), (cx + 1, cz), (cx, cz + 1)]
        weights = np.array([np.where(upper, fx + fz - 1, 1 - fx - fz),
                            np.where(upper, 1 - fz, fx), np.where(upper, 1 - fx, fz)])
        weights = np.maximum(weights, 0) ** 5
        weights /= weights.sum(axis=0)
        n = noise(x * 0.21, z * 0.21) * 0.7 + noise(x * 1.3, z * 1.3) * 0.3
        edge = np.abs(x + 0.55 - np.sin(np.maximum(z - 0.8, 0) * 0.23) * 1.05)
        path = (1 - smooth(0.7, 1.55, edge + (noise(x * 2, z * 2) - 0.5) * 0.35)) * smooth(-0.9, 0.6, z)
        under_trees = np.zeros_like(x)
        for tx, tz, radius in roots:
            under_trees = np.maximum(under_trees, 1 - smooth(0.4, radius, np.hypot(x - tx, z - tz)))
        litter = np.clip(under_trees * 0.85 + smooth(0.4, 0.75, n) * 0.3, 0, 1) * (1 - path)
        moss = smooth(0.3, 0.7, n) * (1 - path) * (1 - litter * 0.75)
        scales = [0.38, 0.304, 0.418]
        leaves, green, dirt = [patch_samples(im, x, z, scale, vertices, weights)
                               for im, scale in zip(colors, scales)]
        luminance = np.array([0.2126, 0.7152, 0.0722])
        leaves = ((leaves @ luminance)[..., None] * 0.42 + leaves * 0.58) * [0.57, 0.61, 0.48]
        dirt = (dirt @ luminance)[..., None] * [0.70, 0.64, 0.53]
        dirt *= (1 - path * 0.4)[..., None]
        green *= [0.48, 0.80, 0.34]
        color = lerp(lerp(dirt, green, np.clip(moss * 1.3, 0, 1)), leaves, litter)
        color *= (0.76 + n * 0.42)[..., None]
        color = np.where(color <= 0.0031308, color * 12.92, 1.055 * np.maximum(color, 0) ** (1 / 2.4) - 0.055)
        output[start:start + len(x)] = np.round(np.clip(color, 0, 1) * 255).astype(np.uint8)
        a, b, c = [patch_samples(im, x, z, scale, vertices, weights) for im, scale in zip(normals, scales)]
        normal = lerp(lerp(c, b, np.clip(moss * 1.3, 0, 1)), a, litter) * 2 - 1
        normal /= np.maximum(np.linalg.norm(normal, axis=2, keepdims=True), 0.0001)
        normal_output[start:start + len(x)] = np.round((normal * 0.5 + 0.5) * 255).astype(np.uint8)
    for filename, array in [('color.jpg', output), ('normal.jpg', normal_output)]:
        Image.fromarray(array).save(TARGET / filename, quality=90, subsampling=2)
    record = {'revision': '02-refined', 'world_span_m': SPAN, 'resolution': SIZE,
              'source_filter_resolution': SOURCE_RESOLUTION,
              'source_license': 'CC0-1.0', 'roots_xz_radius': roots,
              'method': 'Offline triangular patch blending; no histogram transform or screen filtering.',
              'builder_sha256': digest(Path(__file__)),
              'sources': {name + suffix: digest(SOURCES / (name + suffix))
                          for name in names for suffix in ['_diff.jpg', '_nor_gl.jpg']},
              'runtime_files': {name: digest(TARGET / name) for name in ['color.jpg', 'normal.jpg']}}
    (TARGET / 'terrain.json').write_text(json.dumps(record, indent=2) + '\n')
    print('BAKED', SIZE, 'x', SIZE, 'terrain material; two runtime texture samples')


if __name__ == '__main__':
    main()
