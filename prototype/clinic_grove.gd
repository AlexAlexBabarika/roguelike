extends "res://forest_slice.gd"

const ASSET_ROOT := "res://assets/reference-forest/"
const GROVE_SURFACE = preload("res://shaders/grove_surface.gdshader")
const GROVE_GROUND = preload("res://shaders/grove_ground.gdshader")
const CLINIC_SURFACE = preload("res://shaders/grove_clinic.gdshader")
const PREPARED_CLINIC = preload("res://assets/forest-clinic-prepared.glb")
const FIRS := [
	preload("res://assets/reference-forest/fir_tree_01_a_LOD2.glb"),
	preload("res://assets/reference-forest/fir_tree_01_b_LOD2.glb"),
	preload("res://assets/reference-forest/fir_tree_01_c_LOD2.glb"),
]
const ROCKS := [
	preload("res://assets/reference-forest/rock_moss_set_01_0.glb"),
	preload("res://assets/reference-forest/rock_moss_set_01_1.glb"),
	preload("res://assets/reference-forest/rock_moss_set_01_2.glb"),
]
const FERNS := [
	preload("res://assets/reference-forest/fern_02_0.glb"),
	preload("res://assets/reference-forest/fern_02_1.glb"),
	preload("res://assets/reference-forest/fern_02_2.glb"),
	preload("res://assets/reference-forest/fern_02_3.glb"),
]
const GROVE_VIEWS := {
	"wide": [Vector3(-0.6, 3.0, -1.5), 20.5, 0.57, 0.62],
	"tree": [Vector3(6.0, 4.7, 2.0), 11.8, 0.6, 0.24],
	"grove": [Vector3(-0.5, 2.2, 0.8), 16.5, 0.72, 0.42],
	"overview": [Vector3(-0.6, 3.4, -1.5), 25.0, 0.57, 0.62],
}
const FIR_PLACEMENTS := [
	[Vector3(6.0, 0, 2.0), 0, 0.0, 0.51],
	[Vector3(7.4, 0, -2.5), 2, 1.9, 0.69],
	[Vector3(4.7, 0, -8.4), 1, 0.7, 0.69],
	[Vector3(-1.0, 0, -10.6), 0, 2.1, 0.58],
	[Vector3(-6.3, 0, -8.7), 1, 4.2, 0.72],
	[Vector3(-8.0, 0, -3.2), 2, 1.3, 0.68],
	[Vector3(-7.5, 0, 3.4), 1, 3.0, 0.60],
	[Vector3(9.5, 0, -6.5), 0, 4.1, 0.54],
	[Vector3(-9.9, 0, -7.2), 0, 2.8, 0.55],
	[Vector3(1.8, 0, -12.3), 2, 0.3, 0.70],
	[Vector3(-9.0, 0, 0.2), 0, 1.2, 0.48],
	[Vector3(9.4, 0, 0.9), 1, 3.4, 0.61],
	[Vector3(-4.9, 0, -12.8), 0, 1.5, 0.62],
	[Vector3(-8.0, 0, -11.4), 1, 0.8, 0.60],
	[Vector3(-11.2, 0, -10.3), 2, 2.8, 0.80],
	[Vector3(7.5, 0, -11.2), 0, 3.5, 0.57],
	[Vector3(11.5, 0, -7.6), 1, 1.7, 0.65],
	[Vector3(-9.7, 0, 5.9), 2, 4.5, 0.40],
	[Vector3(9.3, 0, 6.0), 1, 0.9, 0.34],
]

var texture_cache: Dictionary = {}
var material_cache: Dictionary = {}
var cover: Node3D


func _ready() -> void:
	super._ready()
	print("GROVE_READY: CC0 authored conifers, textured terrain; daylight; no screen filter")


func _process(delta: float) -> void:
	super._process(delta)
	for material in foliage_materials:
		material.set_shader_parameter("clock", elapsed)


func _texture(name: String) -> Texture2D:
	if not texture_cache.has(name):
		var source := load(ASSET_ROOT + name) as Texture2D
		var image := source.get_image()
		if not image.has_mipmaps():
			image.generate_mipmaps()
		texture_cache[name] = ImageTexture.create_from_image(image)
	return texture_cache[name]


func _surface(prefix: String, leaves := false) -> ShaderMaterial:
	if material_cache.has(prefix):
		return material_cache[prefix]
	var material := ShaderMaterial.new()
	material.shader = GROVE_SURFACE
	material.set_shader_parameter(
		"color_map", _texture(prefix + ("_diff.png" if leaves else "_diff.jpg"))
	)
	material.set_shader_parameter("normal_map", _texture(prefix + "_nor_gl.jpg"))
	material.set_shader_parameter("foliage", leaves)
	if leaves:
		foliage_materials.append(material)
		material.set_shader_parameter("normal_strength", 0.35)
		material.set_shader_parameter("tint", Color("a9b9a6"))
	material_cache[prefix] = material
	tree_materials.append(material)
	return material


func _setup_kit() -> void:
	context = Node3D.new()
	context.name = "ClinicContext"
	add_child(context)
	_setup_clinic()
	_setup_earth()
	for placement in FIR_PLACEMENTS:
		var tree := FIRS[placement[1]].instantiate() as Node3D
		tree.name = "AuthoredFir%d" % trees.size()
		tree.position = placement[0]
		tree.position.y = _height(tree.position.x, tree.position.z) - 0.03
		tree.rotation.y = placement[2]
		tree.scale = Vector3.ONE * placement[3]
		for part in tree.find_children("*", "MeshInstance3D", true, false):
			for index in range(part.mesh.get_surface_count()):
				var base := part.mesh.surface_get_material(index) as StandardMaterial3D
				var prefix := base.resource_name.trim_prefix("Export_")
				if prefix.ends_with("dead_branches"):
					prefix = "fir_tree_01_bark"
				part.set_surface_override_material(
					index, _surface(prefix, prefix.ends_with("twig"))
				)
			part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		add_child(tree)
		trees.append(tree)
	branch_texture = texture_cache["fir_tree_01_twig_diff.png"]
	_setup_cover()
	_setup_grass()
	_apply_silhouette()


func _setup_clinic() -> void:
	var kit := PREPARED_CLINIC.instantiate()
	context.add_child(kit)
	for part in kit.find_children("*", "MeshInstance3D", true, false):
		if part.name in ["Ground", "Forest", "Undergrowth"]:
			part.queue_free()
			continue
		for index in range(part.mesh.get_surface_count()):
			var base := part.mesh.surface_get_material(index) as StandardMaterial3D
			if base == null:
				continue
			var name := base.resource_name.replace("_", " ")
			if (
				name.begins_with("Limewash")
				or name.begins_with("Weathered wood")
				or name.begins_with("Blue slate")
				or name.begins_with("Granite")
			):
				var material := ShaderMaterial.new()
				material.shader = CLINIC_SURFACE
				material.set_shader_parameter("wood", _texture("weathered_planks_diff.jpg"))
				material.set_shader_parameter("metal", _texture("rusty_metal_sheet_diff.jpg"))
				material.set_shader_parameter("stone", _texture("mossy_rock_diff.jpg"))
				var kind := 1 if name.begins_with("Weathered wood") else 0
				if name.begins_with("Blue slate"):
					kind = 2
				elif name.begins_with("Granite"):
					kind = 3
				material.set_shader_parameter("surface_kind", kind)
				material.set_shader_parameter(
					"base_color", Color("808879") if kind == 0 else Color("35434a")
				)
				part.set_surface_override_material(index, material)
			else:
				var material := base.duplicate() as StandardMaterial3D
				material.vertex_color_use_as_albedo = false
				material.roughness = maxf(material.roughness, 0.85)
				material.metallic_specular = 0.12
				if name.begins_with("Traveler cloak"):
					material.albedo_color = Color("817c63")
				if material.emission_enabled:
					material.emission_energy_multiplier = 0.35
					material.albedo_color = Color("9b824f")
					material.emission = Color("cd9b59")
				part.set_surface_override_material(index, material)


func _height(x: float, z: float) -> float:
	var clearing := smoothstep(5.5, 10.0, absf(x))
	return -0.08 + clearing * (0.24 + 0.22 * sin(x * 0.53) * cos(z * 0.45))


func _setup_earth() -> void:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for z in range(-64, 64):
		for x in range(-64, 64):
			for offset in [
				Vector2(0, 0),
				Vector2(1, 1),
				Vector2(0, 1),
				Vector2(0, 0),
				Vector2(1, 0),
				Vector2(1, 1)
			]:
				var p: Vector2 = Vector2(x, z) + offset
				surface.set_uv(p * 0.25)
				surface.add_vertex(Vector3(p.x, _height(p.x, p.y), p.y))
	surface.generate_normals()
	surface.generate_tangents()
	var floor_part := MeshInstance3D.new()
	floor_part.name = "EarthFloor"
	floor_part.mesh = surface.commit()
	floor_part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var soil := ShaderMaterial.new()
	soil.shader = GROVE_GROUND
	soil.set_shader_parameter("litter", _texture("forest_floor_diff.jpg"))
	soil.set_shader_parameter("litter_normal", _texture("forest_floor_nor_gl.jpg"))
	soil.set_shader_parameter("moss", _texture("mossy_rock_diff.jpg"))
	soil.set_shader_parameter("moss_normal", _texture("mossy_rock_nor_gl.jpg"))
	floor_part.material_override = soil
	add_child(floor_part)


func _scatter(
	asset: PackedScene, pos: Vector3, scale_factor: float, angle: float, material: Material
) -> void:
	var prop := asset.instantiate() as Node3D
	prop.position = pos
	prop.position.y += _height(pos.x, pos.z)
	prop.scale = Vector3.ONE * scale_factor
	prop.rotation.y = angle
	for mesh in prop.find_children("*", "MeshInstance3D", true, false):
		mesh.material_override = material
	cover.add_child(prop)


func _setup_cover() -> void:
	cover = Node3D.new()
	cover.name = "GroundCover"
	context.add_child(cover)
	var rock_material := _surface("rock_moss_set_01")
	var fern_material := _surface("fern_02", true)
	for item in [
		[Vector3(-5.8, -0.16, 4.5), 0.72],
		[Vector3(4.2, -0.10, 5.7), 0.53],
		[Vector3(-7.3, -0.10, -1.5), 0.52],
		[Vector3(7.5, -0.20, -0.5), 0.82],
		[Vector3(-6.4, -0.15, 5.8), 0.32],
		[Vector3(3.7, -0.12, 6.4), 0.23],
		[Vector3(6.9, -0.17, 6.6), 0.65],
		[Vector3(-4.5, -0.18, -7.5), 0.65],
	]:
		_scatter(ROCKS[rng.randi_range(0, 2)], item[0], item[1], rng.randf() * TAU, rock_material)
	for index in range(210):
		var x := rng.randf_range(-12.0, 12.0)
		var z := rng.randf_range(-12.0, 11.0)
		var path_center := -0.55 + sin(z * 0.3) * 0.9
		if (x > -6.0 and x < 6.6 and z < 0.5 and z > -8.6) or absf(x - path_center) < 2.1:
			continue
		_scatter(
			FERNS[index % 4],
			Vector3(x, 0, z),
			rng.randf_range(0.9, 1.8),
			rng.randf() * TAU,
			fern_material
		)


func _set_view(preset: String) -> void:
	if not GROVE_VIEWS.has(preset):
		preset = "wide"
	camera_target = GROVE_VIEWS[preset][0]
	camera_size = GROVE_VIEWS[preset][1]
	yaw = GROVE_VIEWS[preset][2]
	elevation = GROVE_VIEWS[preset][3]
	_update_cameras()


func _setup_grass() -> void:
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for index in range(2500):
		var x := rng.randf_range(-14.0, 14.0)
		var z := rng.randf_range(-14.0, 12.0)
		var path_center := -0.55 + sin(z * 0.3) * 0.9
		if (absf(x) < 6.6 and z < 0.5 and z > -8.6) or absf(x - path_center) < 2.2:
			continue
		var center := Vector3(x, _height(x, z), z)
		for blade in range(5):
			var angle := rng.randf() * TAU
			var sideways := Vector3(cos(angle), 0, sin(angle)) * rng.randf_range(0.015, 0.035)
			var lean := Vector3(-sin(angle), 0, cos(angle)) * rng.randf_range(0.07, 0.16)
			var height := rng.randf_range(0.16, 0.35)
			var foot := (
				center + Vector3(rng.randf_range(-0.18, 0.18), 0, rng.randf_range(-0.18, 0.18))
			)
			var mid := foot + Vector3.UP * height * 0.6 + lean * 0.3
			var tip := foot + Vector3.UP * height + lean
			var shade := Color("526044").lerp(Color("8c8b59"), rng.randf())
			for vertex in [
				foot - sideways,
				mid - sideways * 0.6,
				foot + sideways,
				foot + sideways,
				mid - sideways * 0.6,
				mid + sideways * 0.6,
				mid - sideways * 0.6,
				tip,
				mid + sideways * 0.6
			]:
				surface.set_color(shade)
				surface.add_vertex(vertex)
	surface.generate_normals()
	var grass := MeshInstance3D.new()
	grass.name = "PathMarginGrass"
	grass.mesh = surface.commit()
	grass.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := StandardMaterial3D.new()
	material.vertex_color_use_as_albedo = true
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.roughness = 1.0
	material.metallic_specular = 0.0
	grass.material_override = material
	context.add_child(grass)


func _apply_conditions() -> void:
	var atmospheric := weather and not isolated and not silhouette
	environment.fog_enabled = atmospheric
	environment.fog_density = 0.006 if atmospheric else 0.0
	environment.ambient_light_color = Color("b7c6ce")
	environment.ambient_light_energy = 0.44 if not atmospheric else 0.38
	sun.light_energy = 1.2 if not atmospheric else 0.8
	sun.light_color = Color("fff4e4") if not atmospheric else Color("d6e2e5")
	sun.shadow_enabled = shadows_enabled
	rain_enabled = atmospheric
	if is_instance_valid(rain):
		rain.visible = atmospheric


func _setup_hud() -> void:
	super._setup_hud()
	var overlay := hud.get_child(0)
	(overlay.get_child(0) as Label).text = "THE LAST LIGHT\nClinic grove / authored conifers"
	(overlay.get_child(1) as Label).text = (
		"1 context · 2 tree · 3 approach · Q/E orbit · wheel zoom\n"
		+ "I isolate · S silhouette · L shadows · T weather · Space pause · H HUD\n"
		+ "Actual Godot render · CC0 Poly Haven assets + original clinic · no screen filter"
	)


func _capture_record(image: Image) -> Dictionary:
	var record := super._capture_record(image)
	record.scene = "res://clinic_grove.tscn"
	record.erase("asset_sha256")
	record.erase("atlas_sha256")
	record["source_manifest_sha256"] = FileAccess.get_sha256(ASSET_ROOT + "sources.json")
	record["mesh_manifest_sha256"] = FileAccess.get_sha256(ASSET_ROOT + "meshes.json")
	record["content"] = "CC0 Poly Haven conifers, rocks, ferns, PBR maps; original clinic/traveler"
	record["scene_sha256"] = FileAccess.get_sha256("res://clinic_grove.gd")
	record["shaders"] = {}
	for path in ["grove_surface", "grove_ground", "grove_clinic"]:
		record.shaders[path] = FileAccess.get_sha256("res://shaders/" + path + ".gdshader")
	return record
