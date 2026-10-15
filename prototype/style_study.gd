extends "res://mock_scene.gd"

const PREPARED = preload("res://assets/forest-clinic-prepared.glb")
const GOUACHE = preload("res://shaders/study_gouache.gdshader")
const MINIATURE = preload("res://shaders/study_miniature.gdshader")

var arm := "A0"
var atmosphere := false
var movie := ""
var fps := 15
var pigment_debug := false
var pan_pixels := 0
var probes := true
var study_materials: Array[ShaderMaterial] = []


func _read_options() -> void:
	super._read_options()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--arm="):
			arm = arg.trim_prefix("--arm=")
		elif arg == "--atmosphere":
			atmosphere = true
		elif arg.begins_with("--movie="):
			movie = arg.trim_prefix("--movie=")
		elif arg.begins_with("--fps="):
			fps = int(arg.trim_prefix("--fps="))
		elif arg == "--pigment-debug":
			pigment_debug = true
		elif arg.begins_with("--pan="):
			pan_pixels = int(arg.trim_prefix("--pan="))
		elif arg == "--no-probes":
			probes = false
	assert(arm in ["A0", "A1", "G1", "M1"])


func _setup_kit() -> void:
	super._setup_kit()
	if arm != "A0":
		get_node("OriginalBlenderKit").free()
		foliage_materials.clear()
		var kit := PREPARED.instantiate()
		kit.name = "PreparedBlenderKit"
		add_child(kit)
		for node in kit.find_children("*", "MeshInstance3D", true, false):
			var part := node as MeshInstance3D
			if part.name == "Ground":
				part.layers = 2
			for index in range(part.mesh.get_surface_count()):
				var base := part.mesh.surface_get_material(index) as StandardMaterial3D
				if base == null:
					continue
				var material := _material(base, part.name)
				part.set_surface_override_material(index, material)
	if probes:
		_setup_probes()


func _material(base: StandardMaterial3D, group: String) -> Material:
	var name_tag := base.resource_name
	if group == "Ground":
		var ground := ShaderMaterial.new()
		ground.shader = load("res://shaders/study_ground.gdshader") if atmosphere else GROUND
		ground.set_shader_parameter("mud", name_tag.begins_with("Wet earth"))
		return ground
	var clean := base.duplicate() as StandardMaterial3D
	clean.vertex_color_use_as_albedo = false
	if name_tag == "Warm glass":
		clean.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		clean.albedo_color = Color("ffb357")
		clean.emission_enabled = false
		return clean
	var is_foliage := name_tag.begins_with("Fir needles")
	if arm == "A1":
		if not is_foliage:
			return clean
		var foliage_material := ShaderMaterial.new()
		foliage_material.shader = FOLIAGE
		foliage_material.set_shader_parameter("pigment", base.albedo_color)
		foliage_material.set_shader_parameter("wind_enabled", wind_enabled)
		foliage_materials.append(foliage_material)
		return foliage_material
	if name_tag == "Brushed steel" or (group == "Traveler" and not "cloak" in name_tag):
		return clean
	var material := ShaderMaterial.new()
	material.shader = GOUACHE if arm == "G1" else MINIATURE
	material.set_shader_parameter("gouache", arm == "G1")
	material.set_shader_parameter("pigment", base.albedo_color)
	material.set_shader_parameter("foliage", is_foliage)
	material.set_shader_parameter("actor", group == "Traveler")
	material.set_shader_parameter("roof", group == "Roof")
	material.set_shader_parameter("atmosphere", atmosphere)
	material.set_shader_parameter("wind_enabled", wind_enabled)
	material.set_shader_parameter("pigment_debug", pigment_debug)
	study_materials.append(material)
	return material


func _setup_reflection() -> void:
	super._setup_reflection()
	if atmosphere:
		water_material.shader = load("res://shaders/study_water.gdshader")
		water_material.set_shader_parameter("reflection_texture", mirror_view.get_texture())
		_set_reflections(reflections_enabled)
		_update_cameras()


func _setup_probes() -> void:
	var enemy := MeshInstance3D.new()
	enemy.name = "NonGameplayEnemyProbe"
	var capsule := CapsuleMesh.new()
	capsule.radius = 0.27
	capsule.height = 1.65
	enemy.mesh = capsule
	enemy.position = Vector3(1.55, 1.02, 4.35)
	var dark := StandardMaterial3D.new()
	dark.albedo_color = Color("292c30")
	dark.roughness = 1.0
	enemy.material_override = dark
	add_child(enemy)
	var warning := MeshInstance3D.new()
	warning.name = "NonGameplayWarningProbe"
	var vertices := PackedVector3Array([Vector3.ZERO])
	var triangles := PackedInt32Array()
	for i in range(25):
		var angle := -0.5 + float(i) / 24.0
		vertices.append(Vector3(sin(angle), 0, cos(angle)) * 1.45)
		if i > 0:
			triangles.append_array(PackedInt32Array([0, i + 1, i]))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_INDEX] = triangles
	var sector := ArrayMesh.new()
	sector.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	warning.mesh = sector
	warning.position = Vector3(1.55, 0.24, 4.35)
	var bright := StandardMaterial3D.new()
	bright.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	bright.albedo_color = Color("f1c9a0")
	bright.disable_fog = true
	bright.cull_mode = BaseMaterial3D.CULL_DISABLED
	warning.material_override = bright
	add_child(warning)


func _process(delta: float) -> void:
	super._process(delta)
	for material in study_materials:
		material.set_shader_parameter("clock", elapsed)
		material.set_shader_parameter("raining", rain_enabled)
		material.set_shader_parameter("wind_enabled", wind_enabled)


func _capture() -> void:
	hud.visible = false
	for frame in range(20):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	if pan_pixels != 0:
		var height := float(get_viewport().get_texture().get_image().get_height())
		camera_target += camera.global_basis.x * float(pan_pixels) * camera.size / height
		_update_cameras()
	var records := []
	var count := fps * 8 if not movie.is_empty() else 1
	var start_yaw := yaw
	for frame in range(count):
		var ratio := float(frame) / maxf(1, count - 1)
		if not movie.is_empty():
			elapsed = 6.0 + float(frame) / fps
			if movie == "orbit":
				yaw = start_yaw + lerpf(-0.5, 0.5, ratio)
			elif movie == "zoom":
				camera_size = lerpf(5.0, 13.5, ratio)
		_update_cameras()
		_process(0.0)
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var image := get_viewport().get_texture().get_image()
		var path := capture_path
		if not movie.is_empty():
			path = capture_path.path_join("%04d.png" % frame)
		var error := image.save_png(path)
		assert(error == OK, "Capture failed: " + path)
		records.append({"frame": frame, "clock": elapsed, "yaw": yaw, "size": camera_size})
	var lights := []
	for child in get_children():
		if child is Light3D:
			lights.append([child.get_class(), var_to_str(child.position), child.light_energy])
	var record := {
		"arm": arm,
		"atmosphere": atmosphere,
		"view": capture_view,
		"movie": movie,
		"resolution": [get_viewport().size.x, get_viewport().size.y],
		"fps": fps,
		"rain": rain_enabled,
		"wind": wind_enabled,
		"reflections": reflections_enabled,
		"fog_density": environment.fog_density,
		"ambient": environment.ambient_light_energy,
		"lights": lights,
		"frames": records,
		"probes": probes,
		"pan_pixels": pan_pixels,
		"asset_sha256":
		FileAccess.get_sha256(
			(
				"res://assets/forest-clinic.glb"
				if arm == "A0"
				else "res://assets/forest-clinic-prepared.glb"
			)
		),
	}
	var metadata := FileAccess.open(capture_path + ".json", FileAccess.WRITE)
	metadata.store_string(JSON.stringify(record, "\t") + "\n")
	print("STYLE_CAPTURE: ", JSON.stringify(record))
	get_tree().quit()
