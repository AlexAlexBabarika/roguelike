extends Node3D

const KIT = preload("res://assets/forest-clinic.glb")
const WATER = preload("res://shaders/mock_water.gdshader")
const RAIN = preload("res://shaders/mock_rain.gdshader")
const FOLIAGE = preload("res://shaders/mock_foliage.gdshader")
const GROUND = preload("res://shaders/mock_ground.gdshader")
const WATER_LEVEL := 0.065
const PRESETS := {
	"wide": [Vector3(-0.7, 2.5, -1.5), 20.5, 0.57, 0.62],
	"clinic": [Vector3(-0.5, 2.9, -3.1), 13.5, 0.48, 0.48],
	"traveler": [Vector3(-0.5, 1.25, 4.45), 5.0, 0.65, 0.34],
}

var camera := Camera3D.new()
var mirror_camera := Camera3D.new()
var mirror_view := SubViewport.new()
var water_material := ShaderMaterial.new()
var rain_material := ShaderMaterial.new()
var foliage_materials: Array[ShaderMaterial] = []
var rain := MultiMeshInstance3D.new()
var environment := Environment.new()
var hud := CanvasLayer.new()
var camera_target := Vector3.ZERO
var camera_size := 22.0
var yaw := 0.57
var elevation := 0.62
var elapsed := 6.0
var rain_enabled := true
var wind_enabled := true
var reflections_enabled := true
var frozen := false
var capture_path := ""
var capture_view := "wide"
var rng := RandomNumberGenerator.new()


func _ready() -> void:
	rng.seed = 40217
	_read_options()
	get_viewport().msaa_3d = Viewport.MSAA_4X
	_setup_world()
	_setup_kit()
	_setup_reflection()
	_setup_puddles()
	_setup_rain()
	_setup_hud()
	_set_view(capture_view)
	get_viewport().size_changed.connect(_resize)
	_resize()
	print("MOCK_READY: original clinic, layered forest, traveler; art mock, not gameplay")
	if not capture_path.is_empty():
		get_window().content_scale_aspect = Window.CONTENT_SCALE_ASPECT_IGNORE
		_capture.call_deferred()


func _read_options() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture="):
			capture_path = arg.trim_prefix("--capture=")
			frozen = true
		elif arg.begins_with("--view="):
			capture_view = arg.trim_prefix("--view=")
		elif arg == "--dry":
			rain_enabled = false
		elif arg == "--no-reflections":
			reflections_enabled = false
		elif arg == "--no-wind":
			wind_enabled = false


func _setup_world() -> void:
	var world_environment := WorldEnvironment.new()
	environment.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("344c58")
	sky_material.sky_horizon_color = Color("7d9188")
	sky_material.ground_bottom_color = Color("283d3d")
	sky_material.ground_horizon_color = Color("7d9188")
	sky.sky_material = sky_material
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("8ba8ad")
	environment.ambient_light_energy = 0.28
	environment.fog_enabled = true
	environment.fog_light_color = Color("344950")
	environment.fog_light_energy = 0.45
	environment.fog_density = 0.004
	world_environment.environment = environment
	add_child(world_environment)
	var moon := DirectionalLight3D.new()
	moon.name = "OvercastKey"
	moon.rotation_degrees = Vector3(-48, -38, 0)
	moon.light_color = Color("c2d7d5")
	moon.light_energy = 0.85
	moon.shadow_enabled = true
	moon.directional_shadow_max_distance = 45.0
	moon.shadow_bias = 0.12
	moon.shadow_normal_bias = 2.0
	add_child(moon)
	_lamp(Vector3(-3.7, 2.4, -0.8), 1.1, 3.8)
	_lamp(Vector3(-0.55, 2.1, -0.4), 1.5, 4.0)
	_lamp(Vector3(3.4, 2.4, -3.7), 0.9, 4.0)
	_lamp(Vector3(-5.28, 2.9, 0.9), 1.4, 4.4)
	var traveler_fill := OmniLight3D.new()
	traveler_fill.position = Vector3(-0.5, 4.0, 5.4)
	traveler_fill.light_color = Color("c7d5ca")
	traveler_fill.light_energy = 0.55
	traveler_fill.omni_range = 4.0
	add_child(traveler_fill)
	camera.name = "MockCamera"
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.near = 0.1
	camera.far = 110.0
	camera.current = true
	add_child(camera)


func _lamp(pos: Vector3, energy: float, reach: float) -> void:
	var lamp := OmniLight3D.new()
	lamp.position = pos
	lamp.light_color = Color("ffc17a")
	lamp.light_energy = energy
	lamp.omni_range = reach
	lamp.omni_attenuation = 1.6
	add_child(lamp)


func _setup_kit() -> void:
	var ground_extension := MeshInstance3D.new()
	ground_extension.mesh = PlaneMesh.new()
	ground_extension.mesh.size = Vector2(200, 200)
	ground_extension.position.y = -0.5
	ground_extension.layers = 2
	var ground_material := ShaderMaterial.new()
	ground_material.shader = GROUND
	ground_extension.material_override = ground_material
	add_child(ground_extension)
	var kit := KIT.instantiate()
	kit.name = "OriginalBlenderKit"
	add_child(kit)
	for node in kit.find_children("*", "MeshInstance3D", true, false):
		var part := node as MeshInstance3D
		if part.name == "Ground":
			part.layers = 2
		for index in range(part.mesh.get_surface_count()):
			var base := part.mesh.surface_get_material(index) as StandardMaterial3D
			if base == null:
				continue
			if part.name == "Ground":
				var material := ShaderMaterial.new()
				material.shader = GROUND
				material.set_shader_parameter("mud", base.resource_name.begins_with("Wet earth"))
				part.set_surface_override_material(index, material)
			elif base.resource_name.begins_with("Fir needles"):
				var material := ShaderMaterial.new()
				material.shader = FOLIAGE
				material.set_shader_parameter("pigment", base.albedo_color)
				material.set_shader_parameter("clock", elapsed)
				material.set_shader_parameter("wind_enabled", wind_enabled)
				part.set_surface_override_material(index, material)
				foliage_materials.append(material)


func _setup_reflection() -> void:
	mirror_view.name = "MockLiveReflection"
	mirror_view.world_3d = get_world_3d()
	mirror_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(mirror_view)
	mirror_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	mirror_camera.near = 0.1
	mirror_camera.far = 110.0
	mirror_camera.cull_mask = 1
	mirror_camera.current = true
	mirror_view.add_child(mirror_camera)
	water_material.shader = WATER
	water_material.set_shader_parameter("reflection_texture", mirror_view.get_texture())
	_set_reflections(reflections_enabled)
	water_material.set_shader_parameter("clock", elapsed)


func _setup_puddles() -> void:
	var positions := [
		Vector3(0.3, WATER_LEVEL, 6.9),
		Vector3(1.0, WATER_LEVEL, 2.45),
		Vector3(-3.6, WATER_LEVEL, 3.4),
		Vector3(3.8, WATER_LEVEL, 5.6),
	]
	var sizes := [Vector2(1.35, 2.0), Vector2(1.05, 1.0), Vector2(1.25, 0.65), Vector2(1.2, 0.9)]
	for index in range(positions.size()):
		var vertices := PackedVector3Array([Vector3.ZERO])
		var normals := PackedVector3Array([Vector3.UP])
		var triangles := PackedInt32Array()
		for point in range(40):
			var angle := float(point) * TAU / 40.0
			var radius := 1.0 + 0.1 * sin(angle * 5.0 + float(index))
			vertices.append(
				Vector3(
					cos(angle) * sizes[index].x * radius, 0, sin(angle) * sizes[index].y * radius
				)
			)
			normals.append(Vector3.UP)
			triangles.append_array(PackedInt32Array([0, (point + 1) % 40 + 1, point + 1]))
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = vertices
		arrays[Mesh.ARRAY_NORMAL] = normals
		arrays[Mesh.ARRAY_INDEX] = triangles
		var surface := ArrayMesh.new()
		surface.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
		var puddle := MeshInstance3D.new()
		puddle.name = "ReflectivePuddle%d" % index
		puddle.mesh = surface
		puddle.material_override = water_material
		puddle.position = positions[index]
		puddle.layers = 4
		puddle.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(puddle)


func _setup_rain() -> void:
	rain_material.shader = RAIN
	rain_material.set_shader_parameter("clock", elapsed)
	var stroke := QuadMesh.new()
	stroke.size = Vector2(0.014, 0.24)
	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_custom_data = true
	multimesh.mesh = stroke
	multimesh.instance_count = 850
	for index in range(multimesh.instance_count):
		var pos := Vector3(
			rng.randf_range(-13, 13), rng.randf_range(4, 15), rng.randf_range(-13, 12)
		)
		multimesh.set_instance_transform(index, Transform3D(Basis(Vector3.UP, 0.5), pos))
		multimesh.set_instance_custom_data(index, Color(rng.randf(), 0, 0, 1))
	rain.multimesh = multimesh
	rain.material_override = rain_material
	rain.layers = 4
	rain.custom_aabb = AABB(Vector3(-16, -10, -14), Vector3(32, 28, 28))
	rain.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	rain.visible = rain_enabled
	add_child(rain)


func _setup_hud() -> void:
	add_child(hud)
	var overlay := Control.new()
	overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(overlay)
	var heading := Label.new()
	heading.position = Vector2(32, 24)
	heading.text = "THE LAST LIGHT\nForest / field clinic — model & lighting study"
	heading.add_theme_font_size_override("font_size", 20)
	heading.modulate = Color("e1e3d0")
	overlay.add_child(heading)
	var footer := Label.new()
	overlay.add_child(footer)
	footer.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	footer.position = Vector2(32, -58)
	footer.text = (
		"1–3 views  /  Q E orbit  /  wheel zoom  /  R rain  /  F reflections  /  Space pause  /  H hide\n"
		+ "Actual Godot render · original Blender geometry · static art mock, not gameplay"
	)
	footer.add_theme_font_size_override("font_size", 13)
	footer.modulate = Color("b6c4b7")


func _set_view(preset: String) -> void:
	if not PRESETS.has(preset):
		preset = "wide"
	camera_target = PRESETS[preset][0]
	camera_size = PRESETS[preset][1]
	yaw = PRESETS[preset][2]
	elevation = PRESETS[preset][3]
	_update_cameras()


func _resize() -> void:
	var pixels := get_viewport().get_texture().get_size()
	mirror_view.size = Vector2i(maxi(1, int(pixels.x / 2)), maxi(1, int(pixels.y / 2)))
	_update_cameras()


func _update_cameras() -> void:
	var offset := (
		Vector3(sin(yaw) * cos(elevation), sin(elevation), cos(yaw) * cos(elevation)) * 40.0
	)
	camera.position = camera_target + offset
	camera.size = camera_size
	camera.look_at(camera_target)
	mirror_camera.position = camera.position
	mirror_camera.position.y = 2.0 * WATER_LEVEL - camera.position.y
	var reflected_target := camera_target
	reflected_target.y = 2.0 * WATER_LEVEL - camera_target.y
	mirror_camera.size = camera_size
	mirror_camera.look_at(reflected_target, Vector3.DOWN)
	water_material.set_shader_parameter(
		"reflection_view", mirror_camera.global_transform.affine_inverse()
	)
	water_material.set_shader_parameter(
		"reflection_projection", mirror_camera.get_camera_projection()
	)


func _process(delta: float) -> void:
	if not frozen:
		elapsed += minf(delta, 0.1)
		var orbit := (
			float(Input.is_physical_key_pressed(KEY_E))
			- float(Input.is_physical_key_pressed(KEY_Q))
		)
		yaw += orbit * delta * 0.5
		_update_cameras()
	water_material.set_shader_parameter("clock", elapsed)
	rain_material.set_shader_parameter("clock", elapsed)
	for material in foliage_materials:
		material.set_shader_parameter("clock", elapsed)


func _set_reflections(enabled: bool) -> void:
	reflections_enabled = enabled
	water_material.set_shader_parameter("reflections_enabled", enabled)
	mirror_view.render_target_update_mode = (
		SubViewport.UPDATE_ALWAYS if enabled else SubViewport.UPDATE_DISABLED
	)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1:
				_set_view("wide")
			KEY_2:
				_set_view("clinic")
			KEY_3:
				_set_view("traveler")
			KEY_R:
				rain_enabled = not rain_enabled
				rain.visible = rain_enabled
			KEY_F:
				_set_reflections(not reflections_enabled)
			KEY_SPACE:
				frozen = not frozen
			KEY_H:
				hud.visible = not hud.visible
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			camera_size = maxf(4.0, camera_size - 1.0)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			camera_size = minf(30.0, camera_size + 1.0)
		_update_cameras()


func _capture() -> void:
	hud.visible = false
	for frame in range(20):
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	var error := image.save_png(capture_path)
	print(
		"MOCK_VIEW: ",
		(
			JSON
			. stringify(
				{
					"preset": capture_view,
					"projection": "orthographic",
					"size": camera_size,
					"target": [camera_target.x, camera_target.y, camera_target.z],
					"yaw_radians": yaw,
					"elevation_radians": elevation,
					"clock_seconds": elapsed,
					"rain": rain_enabled,
					"wind": wind_enabled,
					"reflections": reflections_enabled,
					"engine": Engine.get_version_info().string,
					"resolution": [image.get_width(), image.get_height()],
				}
			)
		)
	)
	print("MOCK_CAPTURE: ", capture_path, " / ", image.get_size(), " / error ", error)
	get_tree().quit(error)
