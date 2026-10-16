"""Fixed branch-card spruces, not billboards. Atlas: python3 FILE --atlas-only.

Geometry: blender --background --python FILE. No downloaded/AI source assets.
"""

import hashlib
import json
import math
from pathlib import Path
import random
import struct
import sys


ASSETS = Path(__file__).resolve().parents[1] / 'assets'
SEED = 74013


def atlas():
    from PIL import Image, ImageDraw

    scale = 2
    tile = 512
    image = Image.new('RGBA', (1024 * scale, 1024 * scale))
    draw = ImageDraw.Draw(image)
    rng = random.Random(SEED)
    for variant in range(4):
        ox, oy = (variant % 2) * tile, (variant // 2) * tile

        def point(x, y):
            return (round((ox + x) * scale), round((oy + y) * scale))

        def line(a, b, color, width):
            draw.line([point(*a), point(*b)], fill=(*color, 255), width=round(width * scale))

        line((256, 504), (256, 18), (82, 77, 46), 5)
        for rank in range(30):
            t = (rank + 1) / 32
            y = 493 - t * 470
            spread = 156 * math.sin(t * math.pi) ** 0.65 * rng.uniform(0.85, 1.1)
            for side in (-1, 1):
                end = (256 + side * spread, y - 52 - 25 * t)
                line((256, y), end, (72, 79, 43), 2.5)
                for needle in range(23):
                    u = (needle + 1) / 25
                    x, yy = 256 + (end[0] - 256) * u, y + (end[1] - y) * u
                    length = rng.uniform(22, 36) * (1 - 0.32 * t)
                    tint = rng.uniform(0.77, 1.2)
                    color = tuple(round(v * tint) for v in (78, 106, 55))
                    for edge in (-1, 1):
                        tip = (x + side * length * 0.65 + edge * length * 0.25,
                               yy - length * 0.6 + edge * length * 0.7)
                        line((x, yy), tip, color, rng.uniform(3.8, 6.2))
        for i in range(27):
            y = 40 + i * 16
            for side in (-1, 1):
                line((256, y), (256 + side * rng.uniform(13, 24), y - 19), (94, 119, 64), 2.8)
    image = image.resize((1024, 1024), Image.Resampling.LANCZOS)
    # Green RGB under transparent texels avoids black mip fringes.
    pixels = struct.iter_unpack('BBBB', image.tobytes())
    image.putdata([(r, g, b, a) if a > 8 else (69, 94, 49, a) for r, g, b, a in pixels])
    image.save(ASSETS / 'spruce-branches.png')


def geometry():
    import bpy
    from mathutils import Vector

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    image = bpy.data.images.load(str(ASSETS / 'spruce-branches.png'))
    needles = bpy.data.materials.new('Spruce branch cutout')
    needles.use_nodes = True
    nodes = needles.node_tree.nodes
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = image
    bsdf = nodes.get('Principled BSDF')
    needles.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    needles.node_tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    needles.surface_render_method = 'DITHERED'
    bsdf.inputs['Roughness'].default_value = 0.92
    bark = bpy.data.materials.new('Spruce furrowed bark')
    bark.diffuse_color = (0.09, 0.072, 0.052, 1)
    bark.use_nodes = True
    bark.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = bark.diffuse_color
    bark.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = 0.96
    summaries = []
    for variant in range(3):
        rng = random.Random(SEED + variant)
        wood_v, wood_f, leaf_v, leaf_f, uv = [], [], [], [], []
        height = (8.6, 7.2, 9.5)[variant]

        def tube(points, radii, sides=6):
            start = len(wood_v)
            for i, p in enumerate(points):
                axis = Vector(points[min(i + 1, len(points) - 1)]) - Vector(points[max(0, i - 1)])
                axis.normalize()
                u = axis.cross(Vector((0, 1, 0)))
                if u.length < 0.01:
                    u = axis.cross(Vector((1, 0, 0)))
                u.normalize()
                v = axis.cross(u)
                for j in range(sides):
                    a = j * math.tau / sides
                    wood_v.append(Vector(p) + (u * math.cos(a) + v * math.sin(a)) * radii[i])
                    if i:
                        k = start + i * sides + j
                        nxt = start + i * sides + (j + 1) % sides
                        wood_f.append((k - sides, nxt - sides, nxt, k))
            wood_f.append(tuple(start + (len(points) - 1) * sides + j for j in range(sides)))

        def card(root, direction, length, width, tile, tilt):
            direction = Vector(direction).normalized()
            cross = Vector((-direction.y, direction.x, 0)).normalized()
            # A bent ribbon follows a twig; it never rotates toward the camera.
            start = len(leaf_v)
            for ring in range(3):
                t = ring / 2
                center = root + direction * length * t + Vector((0, 0, math.sin(t * math.pi) * 0.045))
                for side in (-1, 0, 1):
                    p = center + cross * width * 0.5 * side
                    p.z += abs(side) * width * tilt
                    leaf_v.append(p)
                    uv.append(((tile % 2 + (side + 1) / 2) / 2, (tile // 2 + t) / 2))
            for ring in range(2):
                for col in range(2):
                    a = start + ring * 3 + col
                    leaf_f.append((a + 3, a + 4, a + 1, a))

        trunk_points = [(0.035 * math.sin(i * 0.9 + variant), 0.025 * math.sin(i), height * i / 14) for i in range(15)]
        tube(trunk_points, [0.19 * (1 - i / 15) ** 1.1 + 0.008 for i in range(15)], 12)
        branch_count = 0
        card_count = 0
        for tier in range(15):
            t = tier / 15
            z = height * (0.21 + 0.76 * t) + rng.uniform(-0.07, 0.07)
            reach = height * 0.32 * (1 - t) ** 0.83
            count = rng.randint(4, 6) if tier < 11 else rng.randint(3, 4)
            rotation = tier * 2.39 + variant
            for b in range(count):
                a = rotation + b * math.tau / count + rng.uniform(-0.18, 0.18)
                length = reach * rng.uniform(0.72, 1.13)
                direction = Vector((math.cos(a), math.sin(a), 0))
                lateral = Vector((-math.sin(a), math.cos(a), 0))
                root = Vector((0, 0, z))

                def branch_point(u):
                    return root + direction * length * u + Vector((0, 0, -0.24 * length * math.sin(u * math.pi * 0.85)))

                tube([branch_point(u) for u in (0, 0.32, 0.68, 1)], [0.028 * (1 - t) + 0.008, 0.024, 0.012, 0.002])
                branch_count += 1
                pairs = max(3, round(length * 3.3))
                for j in range(pairs):
                    u = 0.19 + j / pairs * 0.75
                    for side in (-1, 1):
                        sprig_length = (0.34 + length * 0.24 * (1 - u)) * rng.uniform(0.85, 1.2)
                        sprig_direction = (direction * 0.55 + lateral * side * 0.83 + Vector((0, 0, 0.16))).normalized()
                        origin = branch_point(u)
                        tube([origin, origin + sprig_direction * sprig_length], [0.006, 0.0015], 4)
                        card(origin, sprig_direction, sprig_length * 1.22, sprig_length * 0.85, rng.randrange(4), rng.uniform(-0.28, 0.20))
                        card(origin + Vector((0, 0, 0.035)), sprig_direction, sprig_length * 1.1, sprig_length * 0.6, rng.randrange(4), 0.45)
                        card_count += 2
                card(branch_point(0.65), direction + Vector((0, 0, 0.25)), length * 0.46, length * 0.25, rng.randrange(4), 0.18)
                card_count += 1
        for i in range(3):
            a = i * math.tau / 3
            card(Vector((0, 0, height * 0.9)), Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, 1)),
                 height * 0.11, 0.34, i, 0.12)
            card_count += 1
        # Exposed, twiggy lower branches break the perfect Christmas-tree profile.
        for j in range(7):
            a = rng.random() * math.tau
            root = Vector((0, 0, height * rng.uniform(0.12, 0.24)))
            end = root + Vector((math.cos(a), math.sin(a), -0.25)) * rng.uniform(0.5, 1.1)
            tube([root, end], [0.017, 0.002], 5)
        for label, vertices, faces, material, smooth in [
            ('Wood', wood_v, wood_f, bark, True),
            ('Needles', leaf_v, leaf_f, needles, False),
        ]:
            mesh = bpy.data.meshes.new(f'{label}{variant}')
            mesh.from_pydata(vertices, [], faces)
            mesh.materials.append(material)
            if label == 'Needles':
                layer = mesh.uv_layers.new()
                for polygon in mesh.polygons:
                    for loop in polygon.loop_indices:
                        layer.data[loop].uv = uv[mesh.loops[loop].vertex_index]
            for polygon in mesh.polygons:
                polygon.use_smooth = smooth
            obj = bpy.data.objects.new(f'Spruce{variant}{label}', mesh)
            bpy.context.collection.objects.link(obj)
        summaries.append({'variant': variant, 'height_m': height, 'primary_branches': branch_count,
                          'fixed_branch_cards': card_count, 'wood_vertices': len(wood_v),
                          'foliage_vertices': len(leaf_v), 'triangles': sum((len(f) - 2) for f in wood_f + leaf_f)})
    target = ASSETS / 'structured-spruces.glb'
    bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB', export_yup=True,
                              export_animations=False, export_cameras=False, export_lights=False)
    metadata = {'seed': SEED, 'variants': summaries, 'asset_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                'atlas_sha256': hashlib.sha256((ASSETS / 'spruce-branches.png').read_bytes()).hexdigest(),
                'provenance': 'Original procedural branch geometry and needle atlas. No AI images, downloaded meshes or third-party game assets.',
                'method': 'Tapered wood tubes and fixed bent alpha-scissor branch cards; no camera-facing transforms.'}
    (ASSETS / 'structured-spruces.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('STRUCTURED_SPRUCES:', json.dumps(metadata))


if __name__ == '__main__':
    if '--atlas-only' in sys.argv:
        atlas()
    else:
        geometry()
