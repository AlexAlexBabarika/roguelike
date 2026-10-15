"""Original forest/clinic kit. Run with Blender --background --python this_file."""

import json
import math
import random
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
RNG = random.Random(40217)
GROUPS = defaultdict(list)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def pigment(name, hex_color, roughness=0.9, emission=0):
    rgb = tuple(int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    linear = tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb)
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*linear, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*linear, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*linear, 1)
        bsdf.inputs["Emission Strength"].default_value = emission
    return mat


SOIL = [pigment(f"Peat {i}", c) for i, c in enumerate(("454b3e", "4c5142", "505447", "414a3c", "555847"))]
MUD = [pigment(f"Wet earth {i}", c, 0.36) for i, c in enumerate(("4f5048", "55574f", "606054"))]
PLASTER = [pigment(f"Limewash {i}", c) for i, c in enumerate(("b5b69f", "a8ad97", "c2c2aa", "9dA68f", "969c87"))]
WOOD = [pigment(f"Weathered wood {i}", c) for i, c in enumerate(("636f65", "798174", "879080", "555f55"))]
SLATE = [pigment(f"Blue slate {i}", c, 0.66) for i, c in enumerate(("46565e", "4b5c65", "52616a", "43515b", "55626b"))]
STONE = [pigment(f"Granite {i}", c) for i, c in enumerate(("858d7e", "747e72", "9cA18f", "636e66"))]
NEEDLES = [pigment(f"Fir needles {i}", c) for i, c in enumerate(("344f43", "43604c", "516c52", "5c7758", "385747"))]
BARK = pigment("Dark spruce bark", "3b4139")
BIRCH = pigment("Birch chalk bark", "b1b7a3")
INK = pigment("Door recess and iron", "252f2f")
MOSS = pigment("Moss", "76815b")
LEAF = pigment("Late October leaf", "a48a4b")
RUST = pigment("Dull rust", "766149")
GLASS = pigment("Warm glass", "ffb357", 0.3, 0.9)
PALE = pigment("Ivory enamel", "d9d6b5")
COAT = [pigment(f"Traveler cloak {i}", c) for i, c in enumerate(("b6ad83", "958e6c", "c9bd8c", "7d8066"))]
LEATHER = pigment("Traveler leather", "55493a")
BLADE = pigment("Brushed steel", "d6e3da", 0.27)
DEEP_RED = pigment("Faded clinic cross", "986b54")


def mesh(name, vertices, faces, materials, group, indices=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    for mat in materials:
        data.materials.append(mat)
    if indices:
        for polygon, index in zip(data.polygons, indices):
            polygon.material_index = index % len(materials)
    GROUPS[group].append(obj)
    return obj


def box(name, pos, size, mat, group="Clinic", angle=0, bevel=0):
    vertices = []
    for x, y, z in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                    (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
        x, y, z = x * size[0] / 2, y * size[1] / 2, z * size[2] / 2
        vertices.append((pos[0] + x * math.cos(angle) - y * math.sin(angle),
                         pos[1] + x * math.sin(angle) + y * math.cos(angle), pos[2] + z))
    obj = mesh(name, vertices, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                               (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], [mat], group)
    if bevel:
        mod = obj.modifiers.new("Soft crafted edges", "BEVEL")
        mod.width, mod.segments = bevel, 2
    return obj


def beam(a, b, radius, mat=BARK, group="Forest", end_radius=None, sides=7):
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    u = axis.cross(Vector((0, 0, 1)))
    if u.length < 0.01:
        u = axis.cross(Vector((0, 1, 0)))
    u.normalize()
    v = axis.cross(u).normalized()
    vertices = []
    for center, r in ((a, radius), (b, end_radius if end_radius is not None else radius * 0.7)):
        for i in range(sides):
            vertices.append(center + r * (u * math.cos(i * math.tau / sides) + v * math.sin(i * math.tau / sides)))
    faces = [tuple(range(sides - 1, -1, -1)), tuple(range(sides, 2 * sides))]
    faces += [(i, (i + 1) % sides, (i + 1) % sides + sides, i + sides) for i in range(sides)]
    return mesh("Tapered timber", vertices, faces, [mat], group)


def rock(pos, scale, mat=None, group="Undergrowth"):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1, location=pos)
    obj = bpy.context.object
    obj.name = "Weathered stone"
    obj.scale = scale
    obj.rotation_euler = (RNG.uniform(-0.3, 0.3), RNG.uniform(-0.2, 0.2), RNG.random() * math.tau)
    for material in ([mat] if mat else STONE):
        obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.material_index = RNG.randrange(len(obj.data.materials))
    GROUPS[group].append(obj)
    return obj


def height(x, y):
    return -0.05 + 0.075 * math.sin(x * 0.65) * math.cos(y * 0.6) + 0.06 * math.sin(y * 0.37)


def terrain():
    vertices = []
    n, step = 70, 0.8
    for j in range(n + 1):
        for i in range(n + 1):
            x, y = (i - n / 2) * step, (j - n / 2) * step
            vertices.append((x, y, height(x, y)))
    faces, indices = [], []
    for j in range(n):
        for i in range(n):
            k = j * (n + 1) + i
            faces.extend(((k, k + 1, k + n + 2), (k, k + n + 2, k + n + 1)))
            index = int((math.sin(i * 0.25) + math.cos(j * 0.4)) * 1.1 + 2)
            indices.extend((index, index))
    mesh("Uneven forest floor", vertices, faces, SOIL, "Ground", indices)
    vertices, faces = [], []
    for i in range(35):
        y = -13 + i * 0.46
        x = 0.3 + math.sin(y * 0.37) * 0.6
        width = 1.25 + 0.2 * math.sin(i * 0.75)
        for side in (-1, 1):
            px = x + side * width
            vertices.append((px, y, height(px, y) + 0.028))
        if i:
            k = 2 * i
            faces.append((k - 2, k - 1, k + 1, k))
    mesh("Winding muddy approach", vertices, faces, MUD, "Ground", [RNG.randrange(3) for _ in faces])


def window(x, y, z, width=1.2, side=False, boarded=False):
    group = "Windows"

    def part(name, dx, dz, w, h, mat, depth=0.1, dy=0):
        pos = (x + dx, y - dy, z + dz)
        size = (w, depth, h)
        if side:
            pos = (x + dy, y + dx, z + dz)
            size = (depth, w, h)
        return box(name, pos, size, mat, group)

    part("Deep window pocket", 0, 0, width + 0.22, 1.65, INK, 0.12)
    part("Amber interior panes", 0, 0, width, 1.42, GLASS if not boarded else WOOD[0], 0.04, 0.09)
    for offset in (-width / 2 - 0.04, width / 2 + 0.04):
        part("Painted window jamb", offset, 0, 0.10, 1.72, WOOD[2], dy=0.14)
    for offset in (-0.82, 0.82):
        part("Painted window rail", 0, offset, width + 0.3, 0.12, WOOD[2], dy=0.14)
    part("Window mullion", 0, 0, 0.065, 1.48, WOOD[0], dy=0.16)
    part("Window crossbar", 0, 0, width, 0.065, WOOD[0], dy=0.17)
    part("Stone drip sill", 0, -0.91, width + 0.4, 0.12, STONE[0], 0.32, 0.09)
    if boarded:
        for dz in (-0.4, 0.25):
            part("Barricade plank", 0, dz, width + 0.5, 0.18, WOOD[1], dy=0.23)


def roof(cx, cy, half_width, half_depth, eaves, ridge, group="Roof"):
    for side in (-1, 1):
        for row in range(14):
            near = row / 14
            far = (row + 1.11) / 14
            x0, x1 = cx + side * half_width * near, cx + side * half_width * min(far, 1.02)
            z0 = ridge - (ridge - eaves) * near + 0.045
            z1 = ridge - (ridge - eaves) * min(far, 1.02) + 0.045
            for col in range(19):
                y0 = max(cy - half_depth, cy - half_depth + (col - (0.5 if row % 2 else 0)) * (2 * half_depth / 18))
                y1 = min(cy + half_depth, y0 + 2 * half_depth / 18 + 0.018)
                if y1 - y0 < 0.02:
                    continue
                obj = mesh("Individual slate course", [(x0, y0, z0), (x1, y0, z1), (x1, y1, z1), (x0, y1, z0)],
                           [(0, 1, 2, 3) if side == 1 else (3, 2, 1, 0)], [RNG.choice(SLATE)], group)
                solid = obj.modifiers.new("Slate thickness", "SOLIDIFY")
                solid.thickness = 0.045
        beam((cx, cy - half_depth - 0.03, ridge + 0.06), (cx, cy + half_depth + 0.03, ridge + 0.06), 0.12, SLATE[3], group, 0.12)
        beam((cx + side * half_width, cy - half_depth, eaves), (cx + side * half_width, cy + half_depth, eaves), 0.09, INK, group, 0.09)
        for y in (cy - half_depth, cy + half_depth):
            beam((cx, y, ridge), (cx + side * half_width, y, eaves), 0.11, WOOD[0], group, 0.11)


def clinic():
    cx, cy, front = -1.4, 4.1, 1.4
    for row in range(2):
        for col in range(11):
            box("Uneven foundation block", (-5.3 + col * 0.79, front - 0.03, 0.12 + row * 0.24),
                (0.77, 0.55, 0.23), RNG.choice(STONE), bevel=0.025)
    box("Clinic main walls", (cx, cy, 2.16), (8.4, 5.4, 3.55), PLASTER[0], bevel=0.045)
    for y in (front - 0.01, cy + 2.71):
        mesh("Gable infill", [(cx - 4.2, y, 3.94), (cx + 4.2, y, 3.94), (cx, y, 6.35)],
             [(0, 1, 2), (2, 1, 0)], [PLASTER[1]], "Clinic")
    for row in range(14):
        z = 0.58 + row * 0.24
        box("Front weatherboard shadowline", (cx, front - 0.035, z), (8.38, 0.065, 0.035), WOOD[1])
        box("East weatherboard shadowline", (cx + 4.215, cy, z), (0.065, 5.38, 0.035), WOOD[1])
    for x in (cx - 4.21, cx + 4.21):
        box("Corner post", (x, front - 0.08, 2.2), (0.18, 0.16, 3.7), WOOD[2])
    for _ in range(36):
        x, z = RNG.uniform(-5.5, 2.7), RNG.uniform(0.6, 3.8)
        box("Faded peeling limewash", (x, front - 0.038, z), (RNG.uniform(0.12, 0.55), 0.012, RNG.uniform(0.08, 0.22)), RNG.choice(PLASTER))
    window(-3.7, front - 0.07, 2.3, 1.35)
    window(1.45, front - 0.07, 2.3, 1.25, boarded=True)
    window(2.83, 3.5, 2.3, 1.25, side=True)
    window(2.83, 5.65, 2.3, 1.25, side=True)
    window(cx, front - 0.045, 4.72, 0.8, boarded=True)
    box("Doorway darkness", (-0.55, front - 0.09, 1.64), (1.46, 0.12, 2.65), INK)
    for i in range(6):
        box("Heavy door planks", (-1.15 + i * 0.22, front - 0.17, 1.63), (0.213, 0.11, 2.5), WOOD[i % 4])
    box("Door observation window", (-0.55, front - 0.24, 2.12), (0.8, 0.06, 0.68), GLASS)
    for x in (-1.31, 0.22):
        box("Door frame", (x, front - 0.24, 1.68), (0.14, 0.24, 2.82), PALE)
    box("Door frame lintel", (-0.55, front - 0.24, 3.08), (1.68, 0.24, 0.15), PALE)
    box("Iron door handle", (-0.05, front - 0.31, 1.5), (0.055, 0.09, 0.25), INK)
    for step in range(3):
        box("Worn front steps", (-0.55, -0.85 + step * 0.48, 0.04 + step * 0.10),
            (2.7, 0.62, 0.22 + step * 0.12), RNG.choice(STONE), "Porch", bevel=0.04)
    for i in range(13):
        box("Porch floorboards", (-2.1 + i * 0.26, 0.38, 0.43), (0.245, 1.85, 0.14), WOOD[i % 4], "Porch")
    for x in (-2.18, 1.08):
        box("Porch turned upright", (x, -0.29, 1.83), (0.17, 0.17, 2.82), WOOD[2], "Porch", bevel=0.02)
        beam((x, -0.3, 2.4), (x + (0.5 if x < 0 else -0.5), -0.3, 3.12), 0.055, WOOD[1], "Porch", 0.055)
    roof(-0.55, 0.65, 1.95, 1.14, 2.98, 3.66, "Porch")
    roof(cx, cy, 4.6, 3.12, 3.98, 6.4)
    box("Chimney", (-3.5, 5.1, 6.1), (0.65, 0.7, 2.3), STONE[1], "Roof", bevel=0.03)
    for z in (5.3, 5.65, 6, 6.35, 6.7):
        box("Chimney mortar band", (-3.5, 5.1, z), (0.69, 0.74, 0.045), STONE[3], "Roof")
    box("Chimney cap", (-3.5, 5.1, 7.28), (0.87, 0.9, 0.15), STONE[2], "Roof")
    box("Clinic sign enamel", (-0.55, -0.65, 3.12), (2.5, 0.13, 0.45), INK)
    text = bpy.data.curves.new("Clinic lettering", "FONT")
    text.body, text.align_x, text.size, text.extrude = "FIELD CLINIC", "CENTER", 0.30, 0.003
    obj = bpy.data.objects.new("Clinic lettering", text)
    bpy.context.collection.objects.link(obj)
    obj.location = (-0.55, -0.73, 3.01)
    obj.rotation_euler.x = math.pi / 2
    obj.data.materials.append(PALE)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    GROUPS["Clinic"].append(bpy.context.object)
    box("Side annex", (4.45, 5.0, 1.65), (3.2, 4.1, 2.7), PLASTER[3], bevel=0.03)
    window(6.06, 4.8, 1.8, 1.25, side=True)
    roof(4.45, 5, 1.9, 2.32, 3.0, 3.8)
    for y in (2.45, 6.4):
        beam((2.97, y, 3.85), (2.97, y, 0.3), 0.065, INK, "Clinic", 0.065)
    box("Medical sign bracket", (2.9, 0.65, 3.65), (0.13, 1.5, 0.12), INK)
    box("Hanging clinic sign", (2.91, 0.02, 2.95), (0.15, 0.85, 0.92), PALE)
    box("Medical cross upright", (3.005, 0.02, 2.95), (0.035, 0.18, 0.62), DEEP_RED)
    box("Medical cross arm", (3.01, 0.02, 2.95), (0.035, 0.61, 0.18), DEEP_RED)


def spruce(x, y, h, group):
    z = height(x, y)
    lean = RNG.uniform(-0.25, 0.25)
    beam((x, y, z), (x + lean, y, z + h), h * 0.027, BARK, group, h * 0.006, 8)
    vertices, faces, indices = [], [], []
    for tier in range(11):
        t = tier / 10
        base_z = z + h * (0.17 + t * 0.82 + RNG.uniform(-0.012, 0.012))
        reach = h * 0.28 * max(0.015, 1 - t) ** 0.9
        phase = tier * 1.7 + RNG.random()
        count = 8 if tier < 8 else 6
        for branch in range(count):
            angle = branch * math.tau / count + phase
            length = reach * RNG.uniform(0.72, 1.18)
            d = Vector((math.cos(angle), math.sin(angle), 0))
            cross = Vector((-d.y, d.x, 0))
            origin = Vector((x + lean * t, y, base_z))
            tip = origin + d * length + Vector((0, 0, -length * 0.14))
            if tier < 5:
                beam(origin, tip, h * 0.008, BARK, group, h * 0.002, 5)
            for frond in range(3 if tier < 7 else 2):
                a = frond / 3
                center = origin.lerp(tip, a)
                width = length * (1 - a) * 0.38
                base = len(vertices)
                vertices += [center + Vector((0, 0, length * 0.12)),
                             center + d * length * 0.38 + cross * width,
                             center + d * length * 0.6 + Vector((0, 0, -length * 0.12)),
                             center + d * length * 0.38 - cross * width,
                             center + d * length * 0.28 + Vector((0, 0, length * 0.05))]
                faces += [(base + 4, base + 1, base), (base + 4, base + 2, base + 1),
                          (base + 4, base + 3, base + 2), (base + 4, base, base + 3)]
                shade = RNG.choices(range(5), weights=(3, 5, 4, 1, 3))[0]
                indices += [shade, (shade + 1) % 5, shade, shade]
    mesh("Asymmetric drooping spruce boughs", vertices, faces, NEEDLES, group, indices)


def birch(x, y, h, group):
    z = height(x, y)
    lean = RNG.uniform(-0.5, 0.5)
    beam((x, y, z), (x + lean, y + 0.12, z + h), 0.14, BIRCH, group, 0.055, 9)
    for i in range(12):
        bz = z + 0.5 + i * h / 13
        beam((x + lean * i / 13 - 0.105, y - 0.02, bz),
             (x + lean * i / 13 + 0.1, y - 0.06, bz + RNG.uniform(-0.06, 0.06)), 0.025, BARK, group, 0.018, 5)
    for i in range(8):
        angle, level = i * 2.4, z + h * (0.45 + i * 0.055)
        a = Vector((x + lean * 0.6, y, level))
        b = a + Vector((math.cos(angle) * h * 0.22, math.sin(angle) * h * 0.19, h * 0.18))
        beam(a, b, 0.05, BIRCH, group, 0.018, 6)
        for j in range(4):
            end = b + Vector((math.cos(angle + j) * 0.65, math.sin(angle + j) * 0.65, 0.4))
            beam(b, end, 0.018, BARK, group, 0.006, 5)
            for _ in range(5):
                center = end + Vector((RNG.uniform(-0.4, 0.4), RNG.uniform(-0.4, 0.4), RNG.uniform(-0.1, 0.3)))
                mesh("Last birch leaves", [center + Vector((-0.12, 0, 0)), center + Vector((0, -0.08, 0.04)),
                                           center + Vector((0.16, 0, 0.02)), center + Vector((0, 0.12, -0.02))],
                     [(0, 1, 2, 3), (3, 2, 1, 0)], [LEAF], group)


def forest():
    positions = [(-10, -6, 8), (-8.4, -2, 9), (-9, 2.8, 10), (-7.8, 6, 9),
                 (-8, 10, 11), (-5.5, 10.6, 10), (-2, 11.5, 11.8), (1.3, 11.5, 10.7),
                 (5, 11.2, 11.5), (8.7, 10, 10), (9, 6.7, 10), (9.6, 2.5, 8),
                 (9, -2.5, 8), (10.5, -7, 9), (-12, 0, 10), (-12, 7, 11),
                 (12, 6, 10), (12, 12, 12), (-10, 14, 12), (-5, 15, 12), (1, 15, 13), (7, 15, 13)]
    for x, y, h in positions:
        spruce(x, y, h, "Forest")
    for x, y, h in ((-6.5, -3.4, 6.8), (6.9, -0.5, 6.5), (-6.7, 7, 7.8), (7.9, 7, 8.0)):
        birch(x, y, h, "Forest")
    for _ in range(110):
        x, y = RNG.uniform(-12, 12), RNG.uniform(-11, 11)
        if (-6 < x < 6.5 and 0 < y < 8) or abs(x) < 2.2:
            continue
        s = RNG.uniform(0.13, 0.48)
        rock((x, y, height(x, y) + s * 0.25), (s * 1.5, s, s * 0.75))
    vertices, faces, indices = [], [], []
    for _ in range(1600):
        x, y = RNG.uniform(-12, 12), RNG.uniform(-12, 12)
        if (-6 < x < 6.5 and 0.0 < y < 8) or abs(x - 0.3 - math.sin(y * 0.37) * 0.6) < 1.7:
            continue
        z = height(x, y)
        for blade in range(3):
            angle = RNG.random() * math.tau
            dx, dy, h = math.cos(angle) * 0.1, math.sin(angle) * 0.1, RNG.uniform(0.12, 0.36)
            k = len(vertices)
            vertices.extend(((x - dx, y - dy, z), (x + dx, y + dy, z), (x + dy, y - dx, z + h)))
            faces.append((k, k + 1, k + 2))
            indices.append(RNG.randrange(3))
    mesh("Fine grass at path margins", vertices, faces, [NEEDLES[2], MOSS, NEEDLES[1]], "Undergrowth", indices)


def props():
    for side in (-1, 1):
        for i in range(5):
            x, y = side * (3.3 + i * 0.9), -1.6 + i * 0.38
            box("Sagging fence post", (x, y, 0.65), (0.15, 0.17, 1.38), WOOD[0], "Props", angle=RNG.uniform(-0.1, 0.1))
            if i < 4:
                for z in (0.55, 1.05):
                    beam((x, y, z), (x + side * 0.9, y + 0.38, z - 0.07), 0.065, WOOD[1], "Props", 0.065, 4)
    for y in (-7.7, -6.8, -2.1):
        rock((0.35 + RNG.uniform(-0.5, 0.5), y, height(0, y) + 0.015), (0.7, 0.4, 0.07), STONE[0], "Props")
    for i in range(7):
        box("Leaning firewood", (-4.5 + i * 0.19, 0.85, 0.48), (0.17, 0.7, 0.65 + RNG.random() * 0.1), WOOD[i % 4], "Props")
    box("Bench top", (4.1, 1.4, 0.63), (1.8, 0.5, 0.14), WOOD[2], "Props", bevel=0.02)
    for x in (3.45, 4.75):
        box("Bench legs", (x, 1.4, 0.3), (0.15, 0.45, 0.6), WOOD[0], "Props")
    for y in (1.16, 1.65):
        beam((3.42, y, 0.62), (4.8, y, 0.62), 0.025, INK, "Props", 0.025)
    beam((-5.8, -0.9, 0), (-5.8, -0.9, 3.25), 0.065, INK, "Props", 0.05)
    beam((-5.8, -0.9, 3.25), (-5.3, -0.9, 3.25), 0.05, INK, "Props", 0.05)
    box("Lantern housing", (-5.28, -0.9, 2.95), (0.32, 0.32, 0.48), INK, "Props", bevel=0.025)
    box("Lantern glow", (-5.28, -1.07, 2.95), (0.23, 0.025, 0.32), GLASS, "Props")
    for i in range(38):
        x, y = RNG.uniform(-6, 7), RNG.uniform(-9, 0)
        if abs(x) < 1.1:
            continue
        z, s, a = height(x, y) + 0.06, RNG.uniform(0.06, 0.14), RNG.random() * math.tau
        mesh("Fallen October leaves", [(x - s, y, z), (x, y - s * 0.4, z + 0.02),
                                       (x + s, y, z), (x, y + s * 0.5, z + 0.015)],
             [(0, 1, 2, 3)], [LEAF], "Props")


def traveler():
    ox, oy, oz = -0.5, -4.45, height(-0.5, -4.45)

    def p(x, y, z):
        return (x + ox, y + oy, z + oz)

    for side in (-1, 1):
        box("Traveler boots", p(side * 0.2, 0.02 + side * 0.08, 0.22), (0.27, 0.48, 0.42), LEATHER, "Traveler", bevel=0.06)
        beam(p(side * 0.2, 0, 0.35), p(side * 0.17, 0.01, 1.0), 0.115, WOOD[0], "Traveler", 0.12, 9)
    vertices, faces, indices = [], [], []
    rings = [(0.56, 0.37, 0.63), (0.48, 0.32, 0.98), (0.34, 0.27, 1.5), (0.53, 0.3, 1.86), (0.21, 0.17, 2.03)]
    n = 16
    for ring, (rx, ry, z) in enumerate(rings):
        for i in range(n):
            a = i * math.tau / n
            fold = 1.0 + (0.1 if i % 2 else -0.06)
            vertices.append(p(math.cos(a) * rx * fold, math.sin(a) * ry * fold,
                              z + (0.05 * math.sin(a * 3) if ring == 0 else 0)))
            if ring:
                j = ring * n + i
                faces.append((j - n, ring * n + (i + 1) % n - n, ring * n + (i + 1) % n, j))
                indices.append((i // 3 + ring) % 4)
    faces.append(tuple(range((len(rings) - 1) * n, len(rings) * n)))
    indices.append(0)
    mesh("Tailored folded traveler cloak", vertices, faces, COAT, "Traveler", indices)
    beam(p(-0.45, 0, 1.77), p(-0.52, 0.1, 1.16), 0.14, COAT[1], "Traveler", 0.095, 9)
    beam(p(0.44, 0, 1.77), p(0.63, 0.17, 1.32), 0.14, COAT[1], "Traveler", 0.09, 9)
    rock(p(0, 0, 2.1), (0.24, 0.23, 0.3), INK, "Traveler")
    beam(p(0, 0.02, 2.27), p(0, 0.02, 2.53), 0.32, COAT[1], "Traveler", 0.21, 12)
    beam(p(0, 0.02, 2.24), p(0, 0.02, 2.29), 0.48, COAT[0], "Traveler", 0.48, 16)
    box("Scarf tail", p(-0.3, -0.3, 1.75), (0.22, 0.12, 0.7), COAT[2], "Traveler", angle=-0.22)
    box("Worn satchel", p(-0.38, -0.31, 1.26), (0.4, 0.2, 0.48), LEATHER, "Traveler", bevel=0.06)
    beam(p(-0.3, -0.35, 1.45), p(0.27, -0.3, 1.9), 0.038, LEATHER, "Traveler", 0.038, 5)
    beam(p(0.62, 0.15, 1.34), p(0.79, 0.42, 1.02), 0.045, LEATHER, "Traveler", 0.045)
    beam(p(0.60, 0.52, 0.99), p(0.98, 0.28, 0.99), 0.045, PALE, "Traveler", 0.045, 5)
    mesh("Traveler tapered sword", [p(0.73, 0.4, 1.02), p(0.87, 0.48, 1.02), p(1.31, 1.21, 0.5),
                                    p(1.35, 1.31, 0.45), p(1.22, 1.18, 0.48), p(0.8, 0.44, 1.07)],
         [(0, 5, 4), (5, 2, 4), (2, 3, 4), (5, 1, 2), (4, 2, 1, 0)], [BLADE, PALE], "Traveler", [0, 1, 0, 0, 1])


terrain()
clinic()
forest()
props()
traveler()

for group, objects in GROUPS.items():
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        for modifier in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    bpy.context.object.name = group
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

output = ROOT / "assets" / "forest-clinic.glb"
bpy.ops.export_scene.gltf(filepath=str(output), export_format="GLB", export_yup=True,
                          export_apply=True, export_animations=False, export_cameras=False,
                          export_lights=False, export_extras=False)
summary = {"seed": 40217, "asset": "forest-clinic.glb", "blender": bpy.app.version_string,
           "groups": {obj.name: {"vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons)}
                      for obj in bpy.context.scene.objects if obj.type == "MESH"},
           "provenance": "Original procedurally modeled geometry; no downloaded meshes, AI images or texture assets."}
(ROOT / "assets" / "forest-clinic.json").write_text(json.dumps(summary, indent=2) + "\n")
print("MOCK_ASSETS:", json.dumps(summary))
