extends "res://mock_scene.gd"

const SPRUCES = preload("res://assets/structured-spruces.glb")
const NEEDLES = preload("res://shaders/forest_needles.gdshader")
const BARK = preload("res://shaders/forest_bark.gdshader")
const BRANCHES = preload("res://assets/spruce-branches.png")
const SOIL = preload("res://shaders/forest_soil.gdshader")
const SLICE_VIEWS := {
	"wide": [Vector3(-0.6, 3.0, -1.5), 20.5, 0.57, 0.62],
	"tree": [Vector3(6.0, 4.0, 2.0), 10.8, 0.6, 0.32],
	"grove": [Vector3(5.0, 3.1, -0.2), 13.8, 0.8, 0.5],
}
const TREE_PLACEMENTS := [
	[Vector3(6.0, 0, 2.0), 0, 0.0, 1.0],
	[Vector3(6.2, 0, -3.2), 1, 1.9, 1.03],
	[Vector3(3.9, 0, -8.0), 2, 0.7, 0.95],
	[Vector3(-1.0, 0, -9.2), 0, 2.1, 1.08],
	[Vector3(-6.0, 0, -7.2), 1, 4.2, 1.08],
	[Vector3(-8.0, 0, -2.2), 2, 1.3, 0.96],
	[Vector3(-7.2, 0, 3.2), 1, 3.0, 0.92],
]

var tree_materials: Array[ShaderMaterial] = []
var trees: Array[Node3D] = []
var weather := false
var isolated := false
var silhouette := false
var shadows_enabled := true
var sun: DirectionalLight3D
var context: Node3D
var branch_texture: ImageTexture


func _ready() -> void:
	super._ready()
	get_viewport().msaa_3d = Viewport.MSAA_2X
	print("FOREST_READY: structured branch meshes; daylight by default; no screen filter")


func _process(delta: float) -> void:
	super._process(delta)
	for material in foliage_materials:
		material.set_shader_parameter("wind_enabled", wind_enabled)


func _read_options() -> void:
	super._read_options()
	rain_enabled = false
	reflections_enabled = false
	for arg in OS.get_cmdline_user_args():
		if arg == "--weather":
			weather = true
		elif arg == "--isolated":
			isolated = true
		elif arg == "--silhouette":
			silhouette = true
		elif arg == "--no-shadows":
			shadows_enabled = false


func _setup_world() -> void:
	super._setup_world()
	sun = get_node("OvercastKey")
	sun.rotation_degrees = Vector3(-43, -55, 0)
	sun.directional_shadow_max_distance = 40.0
	sun.shadow_bias = 0.12
	sun.shadow_normal_bias = 2.0
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL
	RenderingServer.directional_shadow_atlas_set_size(2048, true)
	_apply_conditions()


func _setup_kit() -> void:
	var branch_image := BRANCHES.get_image()
	branch_image.generate_mipmaps()
	branch_texture = ImageTexture.create_from_image(branch_image)
	context = Node3D.new()
	context.name = "ClinicContext"
	add_child(context)
	var kit := KIT.instantiate()
	context.add_child(kit)
	for part in kit.find_children("*", "MeshInstance3D", true, false):
		if part.name in ["Ground", "Forest", "Undergrowth"]:
			part.queue_free()
			continue
		for index in range(part.mesh.get_surface_count()):
			var base := part.mesh.surface_get_material(index) as StandardMaterial3D
			if base == null:
				continue
			var clean := base.duplicate() as StandardMaterial3D
			clean.vertex_color_use_as_albedo = false
			clean.roughness = maxf(clean.roughness, 0.85)
			clean.metallic_specular = 0.15
			if base.resource_name.replace("_", " ").begins_with("Blue slate"):
				clean.albedo_color = Color("47545b")
			part.set_surface_override_material(index, clean)
	var floor_mesh := PlaneMesh.new()
	floor_mesh.size = Vector2(160, 160)
	var floor_part := MeshInstance3D.new()
	floor_part.name = "EarthFloor"
	floor_part.mesh = floor_mesh
	floor_part.position.y = -0.08
	floor_part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var soil := ShaderMaterial.new()
	soil.shader = SOIL
	floor_part.material_override = soil
	add_child(floor_part)
	for index in range(TREE_PLACEMENTS.size()):
		var placement: Array = TREE_PLACEMENTS[index]
		var tree := SPRUCES.instantiate() as Node3D
		tree.name = "StructuredSpruce%d" % index
		tree.position = placement[0]
		tree.rotation.y = placement[2]
		tree.scale = Vector3.ONE * placement[3]
		for part in tree.find_children("*", "MeshInstance3D", true, false):
			if not part.name.begins_with("Spruce%d" % placement[1]):
				part.queue_free()
				continue
			var material := ShaderMaterial.new()
			material.shader = NEEDLES if part.name.ends_with("Needles") else BARK
			if part.name.ends_with("Needles"):
				material.set_shader_parameter("branches", branch_texture)
				foliage_materials.append(material)
			tree_materials.append(material)
			part.material_override = material
			part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		add_child(tree)
		trees.append(tree)
	_apply_isolation()
	_apply_silhouette()


func _setup_puddles() -> void:
	pass


func _setup_rain() -> void:
	super._setup_rain()
	rain.visible = weather and not isolated and not silhouette


func _setup_hud() -> void:
	super._setup_hud()
	var overlay := hud.get_child(0)
	var heading := overlay.get_child(0) as Label
	heading.text = "THE LAST LIGHT\nStructured spruce / daylight forest slice"
	var footer := overlay.get_child(1) as Label
	footer.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	footer.offset_left = 32
	footer.offset_right = -24
	footer.offset_top = -86
	footer.offset_bottom = -12
	footer.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	footer.text = (
		"1 grove context · 2 single tree · 3 grove detail · Q/E orbit · wheel zoom\n"
		+ "I isolate · S silhouette · L shadows · T weather · Space pause · H HUD\n"
		+ "Actual Godot render · procedural branches / fixed cutouts · no painterly filter"
	)
	footer.add_theme_color_override("font_outline_color", Color("152025"))
	footer.add_theme_constant_override("outline_size", 3)


func _set_view(preset: String) -> void:
	if not SLICE_VIEWS.has(preset):
		preset = "wide"
	camera_target = SLICE_VIEWS[preset][0]
	camera_size = SLICE_VIEWS[preset][1]
	yaw = SLICE_VIEWS[preset][2]
	elevation = SLICE_VIEWS[preset][3]
	_update_cameras()


func _apply_conditions() -> void:
	var atmospheric := weather and not isolated and not silhouette
	environment.fog_enabled = atmospheric
	environment.fog_density = 0.009 if atmospheric else 0.0
	environment.ambient_light_color = Color("a3b4c0")
	environment.ambient_light_energy = 0.48 if not atmospheric else 0.38
	sun.light_energy = 1.45 if not atmospheric else 0.85
	sun.light_color = Color("fff0cd") if not atmospheric else Color("c9d7df")
	sun.shadow_enabled = shadows_enabled
	rain_enabled = atmospheric
	if is_instance_valid(rain):
		rain.visible = atmospheric


func _apply_isolation() -> void:
	context.visible = not isolated and not silhouette
	for index in range(trees.size()):
		trees[index].visible = not (isolated or silhouette) or index == 0
	_apply_conditions()


func _apply_silhouette() -> void:
	for material in tree_materials:
		material.set_shader_parameter("silhouette", silhouette)
	_apply_isolation()
	environment.background_mode = Environment.BG_COLOR if silhouette else Environment.BG_SKY
	environment.background_color = Color("e7e4d9")
	get_node("EarthFloor").visible = not silhouette


func _capture() -> void:
	frozen = true
	hud.visible = false
	for frame in range(6):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	var error := image.save_png(capture_path)
	if error != OK:
		push_error("Forest capture failed: " + capture_path)
		get_tree().quit(error)
		return
	var record := _capture_record(image)
	var sidecar := FileAccess.open(capture_path.get_basename() + ".json", FileAccess.WRITE)
	if sidecar == null:
		push_error("Forest capture metadata could not be written")
		get_tree().quit(1)
		return
	sidecar.store_string(JSON.stringify(record, "\t") + "\n")
	print("FOREST_CAPTURE: ", JSON.stringify(record), " / error ", error)
	get_tree().quit(error)


func _capture_record(image: Image) -> Dictionary:
	return {
		"scene": "res://forest_slice.tscn",
		"engine": Engine.get_version_info().string,
		"renderer": RenderingServer.get_current_rendering_method(),
		"device": RenderingServer.get_video_adapter_name(),
		"resolution": [image.get_width(), image.get_height()],
		"projection": "orthographic",
		"preset": capture_view,
		"target": [camera_target.x, camera_target.y, camera_target.z],
		"size": camera_size,
		"yaw_radians": yaw,
		"elevation_radians": elevation,
		"clock_seconds": elapsed,
		"wind": wind_enabled,
		"rain": rain.visible,
		"fog": environment.fog_enabled,
		"reflections": false,
		"screen_filter": false,
		"shadows": sun.shadow_enabled,
		"silhouette": silhouette,
		"isolated": isolated,
		"msaa": "2x",
		"shadow_atlas": 2048,
		"asset_sha256": FileAccess.get_sha256("res://assets/structured-spruces.glb"),
		"atlas_sha256": FileAccess.get_sha256("res://assets/spruce-branches.png"),
		"capture_sha256": FileAccess.get_sha256(capture_path),
	}


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1:
				_set_view("wide")
			KEY_2:
				_set_view("tree")
			KEY_3:
				_set_view("grove")
			KEY_I:
				isolated = not isolated
				_apply_isolation()
			KEY_S:
				silhouette = not silhouette
				_apply_silhouette()
			KEY_L:
				shadows_enabled = not shadows_enabled
				_apply_conditions()
			KEY_T:
				weather = not weather
				_apply_conditions()
			KEY_SPACE:
				frozen = not frozen
			KEY_H:
				hud.visible = not hud.visible
	elif event is InputEventMouseButton:
		super._unhandled_input(event)
