"""Generate a separate prepared kit from the original seeded construction functions."""

import ast
import hashlib
import json
import math
import struct
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/build_mock_scene.py"


def normalize_colors(path):
    raw = path.read_bytes()
    length = struct.unpack_from("<I", raw, 12)[0]
    document = json.loads(raw[20:20 + length])
    binary = raw[28 + length:]
    used, color_indices = set(), set()
    for model in document["meshes"]:
        for primitive in model["primitives"]:
            attributes = primitive["attributes"]
            # Blender reserves a white COLOR_0 when the active color isn't in a material.
            attributes["COLOR_0"] = attributes.pop("COLOR_1")
            color_indices.add(attributes["COLOR_0"])
            used.update(attributes.values())
            used.add(primitive["indices"])
    accessors, views, packed, mapping = [], [], bytearray(), {}
    for index in sorted(used):
        accessor = document["accessors"][index].copy()
        view = document["bufferViews"][accessor["bufferView"]]
        assert accessor.get("byteOffset", 0) == 0 and "byteStride" not in view
        data = binary[view.get("byteOffset", 0):view.get("byteOffset", 0) + view["byteLength"]]
        if index in color_indices:
            assert accessor["componentType"] == 5123 and accessor["normalized"]
            data = bytes(round(v / 257) for (v,) in struct.iter_unpack("<H", data))
            accessor["componentType"] = 5121
        packed.extend(b"\0" * (-len(packed) % 4))
        views.append({"buffer": 0, "byteOffset": len(packed), "byteLength": len(data)})
        accessor["bufferView"] = len(views) - 1
        mapping[index] = len(accessors)
        accessors.append(accessor)
        packed.extend(data)
    for model in document["meshes"]:
        for primitive in model["primitives"]:
            primitive["attributes"] = {key: mapping[value] for key, value in primitive["attributes"].items()}
            primitive["indices"] = mapping[primitive["indices"]]
    document.update(accessors=accessors, bufferViews=views, buffers=[{"byteLength": len(packed)}])
    encoded = json.dumps(document, separators=(",", ":")).encode()
    encoded += b" " * (-len(encoded) % 4)
    packed.extend(b"\0" * (-len(packed) % 4))
    path.write_bytes(struct.pack("<III", 0x46546C67, 2, 28 + len(encoded) + len(packed))
                     + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
                     + struct.pack("<II", len(packed), 0x004E4942) + packed)


tree = ast.parse(SOURCE.read_text())
boundary = next(i for i, node in enumerate(tree.body)
                if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name) and node.value.func.id == "terrain")
namespace = {"__file__": str(SOURCE), "__name__": "style_kit_source"}
exec(compile(ast.Module(body=tree.body[:boundary], type_ignores=[]), str(SOURCE), "exec"), namespace)


def recolor(material, rgb):
    material.diffuse_color = (*rgb, 1)
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)


for key, variation, value in (("NEEDLES", 0.24, 1), ("SLATE", 0.14, 1),
                              ("COAT", 0, 1), ("STONE", 0.35, 0.66)):
    materials = namespace[key]
    mean = Vector(tuple(sum(m.diffuse_color[j] for m in materials) / len(materials) for j in range(3)))
    for material in materials:
        rgb = (mean.lerp(Vector(material.diffuse_color[:3]), variation) * value)
        recolor(material, rgb)

original_mesh = namespace["mesh"]
original_beam = namespace["beam"]
original_spruce = namespace["spruce"]
prepared_fronds = 0
shortened_trunks = 0


def mesh(name, vertices, faces, materials, group, indices=None):
    global prepared_fronds
    if name == "Asymmetric drooping spruce boughs":
        indices = [indices[(i // 4) * 4] for i in range(len(faces))]
        prepared_fronds += len(faces) // 4
    obj = original_mesh(name, vertices, faces, materials, group, indices)
    if group == "Traveler" and ("cloak" in name.lower() or name == "Tapered timber"):
        for polygon in obj.data.polygons:
            polygon.use_smooth = len(polygon.vertices) == 4
    return obj


def beam(a, b, radius, mat=None, group="Forest", end_radius=None, sides=7):
    global shortened_trunks
    mat = namespace["BARK"] if mat is None else mat
    a, b = Vector(a), Vector(b)
    if mat == namespace["BARK"] and b.z - a.z > 4 and (b - a).xy.length < 0.6:
        b.z -= (b.z - a.z) * 0.09
        shortened_trunks += 1
    return original_beam(a, b, radius, mat, group, end_radius, sides)


def spruce(x, y, height, group):
    start = len(namespace["GROUPS"][group])
    original_spruce(x, y, height, group)
    for obj in namespace["GROUPS"][group][start:]:
        obj["crown_center"] = [x, y, namespace["height"](x, y) + height * 0.55]
        obj["crown_height"] = height


namespace.update(mesh=mesh, beam=beam, spruce=spruce)
for name in ("terrain", "clinic", "forest", "props", "traveler"):
    namespace[name]()

for obj in list(bpy.context.scene.objects):
    if obj.type != "MESH":
        continue
    data = obj.data
    data.update()
    foliage = obj.name.startswith("Asymmetric drooping spruce")
    center = Vector(obj.get("crown_center", (0, 0, 0)))
    height = obj.get("crown_height", 1)
    if foliage:
        normals = []
        for vertex in data.vertices:
            p = vertex.co - center
            normal = Vector((p.x, p.y, p.z * 0.25 + height * 0.08)).normalized()
            normals.append(normal)
        for polygon in data.polygons:
            polygon.use_smooth = True
        data.normals_split_custom_set_from_vertices(normals)
    colors = data.color_attributes.new(name="COLOR_0", type="FLOAT_COLOR", domain="CORNER")
    values = []
    for loop in data.loops:
        vertex = data.vertices[loop.vertex_index]
        world = obj.matrix_world @ vertex.co
        normal = vertex.normal
        occlusion = max(0, 1 - world.z / 1.1) * 0.7
        if foliage:
            radius = height * 0.25
            radial = (vertex.co - center).xy.length
            occlusion = max(0, 1 - radial / radius) * 0.75
            normal = Vector(normals[loop.vertex_index])
        exposure = max(0, normal.z)
        # Analytic study masks, not ray-traced/baked AO or a shelter simulation.
        if obj.name.startswith(("Window", "Inset", "Porch")):
            exposure *= 0.25
        seed = math.sin(obj.location.x * 12.9898 + obj.location.y * 78.233 + len(data.vertices)) * 43758.5453
        values.extend((min(1, occlusion), exposure, 0, seed % 1))
    colors.data.foreach_set("color", values)
    data.color_attributes.active_color = colors

for group, objects in namespace["GROUPS"].items():
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

output = ROOT / "assets/forest-clinic-prepared.glb"
bpy.ops.export_scene.gltf(
    filepath=str(output), export_format="GLB", export_yup=True, export_apply=True,
    export_animations=False, export_cameras=False, export_lights=False, export_extras=False,
    export_all_vertex_colors=True,
)
normalize_colors(output)
summary = {
    "source": "tools/build_mock_scene.py", "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "seed": 40217, "blender": bpy.app.version_string, "fronds_unified": prepared_fronds,
    "trunks_shortened": shortened_trunks,
    "masks": {"R": "analytic occlusion/interior", "G": "analytic exposure, not shelter raycasting",
              "B": "reserved edge wear (zero)", "A": "object pigment seed"},
    "changes": ["one pigment per four-triangle frond", "narrower slate and fir palette",
                "lower-value rocks", "unified cloak swatch and smooth side normals",
                "foliage crown proxy normals", "trunk tips shortened within crowns"],
    "limitations": "Procedural Blender stand-in, not representative AI meshes. No new silhouette loops, AO bake, skinning or animation.",
    "asset_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
}
output.with_suffix(".json").write_text(json.dumps(summary, indent=2) + "\n")
print("STYLE_KIT:", json.dumps(summary))
