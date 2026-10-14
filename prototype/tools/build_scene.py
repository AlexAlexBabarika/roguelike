"""Run with Blender --background --python tools/build_scene.py."""

import math
import random
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
RNG = random.Random(7301)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)


def material(name, color, roughness=0.85):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


stones = [material(f"Stone_{i}", (0.29 + i * 0.027, 0.34 + i * 0.027, 0.39 + i * 0.025)) for i in range(4)]
soil = material("Ground", (0.018, 0.035, 0.023))
slate = material("WetSlate", (0.15, 0.20, 0.24), 0.26)
bark = material("Bark", (0.10, 0.12, 0.15))
wood = material("Wood", (0.23, 0.17, 0.12))
meshes = {"Architecture": [], "Ground": [], "Trees": [], "Props": []}


def finish(obj, mat, group):
    obj.data.materials.append(mat)
    meshes[group].append(obj)
    return obj


def box(name, pos, size, mat, group="Architecture", bevel=0.035):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("Chipped edges", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return finish(obj, mat, group)


def branch(a, b, radius):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=radius, radius2=radius * 0.58, depth=(b - a).length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    finish(obj, bark, "Trees")


# Blender uses Z-up. glTF export converts to Godot's Y-up.
for pos, size in [((-8, 0, -0.22), (8, 22, 0.4)), ((8, 0, -0.22), (8, 22, 0.4)), ((0, -7.5, -0.22), (8, 7, 0.4)), ((0, 7, -0.22), (8, 8, 0.4))]:
    box("Terrain", pos, size, soil, "Ground", 0)
box("PoolBed", (0, 0, -0.65), (8, 6, 0.25), slate, "Ground", 0)

# A deliberately legible, two-sided arch instead of a generated illustration.
for side in (-1, 1):
    for row in range(6):
        box("Arch pier", (side * 2.38, 6.8, 0.4 + row * 0.75), (1.05, 1.10, 0.72), RNG.choice(stones))
for i in range(13):
    theta = (i + 0.5) * math.pi / 13
    obj = box("Arch voussoir", (2.4 * math.cos(theta), 6.8, 4.4 + 2.4 * math.sin(theta)), (0.63, 1.12, 0.87), RNG.choice(stones))
    obj.rotation_euler[1] = theta - math.pi / 2
for side in (-1, 1):
    for col in range(5):
        for row in range(3 + (col % 2)):
            box("Ruined wall", (side * (3.3 + col * 1.05), 6.8, 0.4 + row * 0.77), (1.01, 1.0, 0.72), RNG.choice(stones))

for z in (-3.25, 3.25):
    for x in range(-4, 5):
        box("Pool coping", (x, z, 0.10), (0.94, 0.48, 0.26), RNG.choice(stones))
for x in (-4.25, 4.25):
    for z in range(-2, 3):
        box("Pool coping", (x, z, 0.10), (0.48, 0.94, 0.26), RNG.choice(stones))

for z in (-8, -6.8, -5.6, -4.4, 4.3, 5.4):
    for x in (-0.55, 0.55):
        obj = box("Path slab", (x + RNG.uniform(-0.06, 0.06), z, 0.035), (1.05, 0.98, 0.12), slate, "Props")
        obj.rotation_euler[2] = RNG.uniform(-0.05, 0.05)

for x, y in [(-7, 2), (8, 5), (-8, -6), (7, -7), (-9, 8)]:
    branch((x, y, 0), (x + 0.25, y, 4.8), 0.22)
    for i in range(5):
        h = 1.8 + i * 0.55
        angle = i * 2.1
        end = (x + math.cos(angle) * 2.2, y + math.sin(angle) * 1.7, h + 1.5)
        branch((x + 0.15, y, h), end, 0.09)
        branch(end, (end[0] + math.cos(angle + 0.8) * 0.75, end[1] + math.sin(angle + 0.8) * 0.8, end[2] + 0.7), 0.045)

for _ in range(22):
    x, y = RNG.uniform(-10, 10), RNG.uniform(-9, 9)
    if abs(x) < 5 and abs(y) < 4:
        continue
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=RNG.uniform(0.18, 0.5), location=(x, y, 0.14))
    obj = bpy.context.object
    obj.scale.z = 0.55
    finish(obj, RNG.choice(stones), "Props")

for x, y in [(-5.5, 4.5), (5.6, -4.8)]:
    box("Bench seat", (x, y, 0.65), (2.1, 0.65, 0.18), wood, "Props")
    for dx in (-0.75, 0.75):
        box("Bench foot", (x + dx, y, 0.30), (0.15, 0.5, 0.6), bark, "Props")

for group, objects in meshes.items():
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    bpy.context.object.name = group
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

ROOT.joinpath("assets").mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(ROOT / "assets" / "courtyard.glb"), export_format="GLB", export_yup=True, export_apply=True)
print("Exported original courtyard geometry to assets/courtyard.glb")
