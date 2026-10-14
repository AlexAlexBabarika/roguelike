extends Node

const PLAYER = preload("res://player.gd")
const COURTYARD = preload("res://assets/courtyard.glb")
const WATER_HEIGHT := 0.075
const WORLD_SIZE := 11.0

var scene_view := SubViewport.new()
var mirror_view := SubViewport.new()
var world := Node3D.new()
var camera := Camera3D.new()
var mirror_camera := Camera3D.new()
var player: CharacterBody3D
var water_material := ShaderMaterial.new()
var wind_material := ShaderMaterial.new()
var rain_material := ShaderMaterial.new()
var glyph_material := ShaderMaterial.new()
var rain: MultiMeshInstance3D
var moon := DirectionalLight3D.new()
var world_environment := Environment.new()
var camera_yaw := 0.28
var camera_size := 19.0
var camera_target := Vector3.ZERO
var elapsed := 0.0
var last_step := Vector2.ZERO
var ripple_age := 10.0
var storm_enabled := true
var wind_enabled := true
var reflections_enabled := true
var ascii_enabled := true
var hud_visible := true
var hud := Control.new()
var status_label := Label.new()
var effect_buttons: Dictionary = {}
var frame_label := Label.new()
var rng := RandomNumberGenerator.new()


func _ready() -> void:
	rng.seed = 7301
	_setup_inputs()
	_setup_viewports()
	_setup_environment()
	_build_courtyard()
	_build_water()
	_build_grass()
	_build_rain()
	player = PLAYER.new()
	world.add_child(player)
	player.reset()
	player.camera = camera
	camera_target = Vector3(0, 0, 0.6)
	_update_cameras(1.0)
	_setup_display()
	_setup_hud()
	_update_status()
	get_viewport().size_changed.connect(_resize)
	_resize()
	print("STORM_READY: Blender courtyard, live planar reflections, rain, wind, glyphs")


func _setup_inputs() -> void:
	var keys := {
		"move_left": [KEY_A, KEY_LEFT],
		"move_right": [KEY_D, KEY_RIGHT],
		"move_up": [KEY_W, KEY_UP],
		"move_down": [KEY_S, KEY_DOWN],
		"sprint": [KEY_SHIFT],
		"rotate_left": [KEY_Q],
		"rotate_right": [KEY_E],
	}
	for action: String in keys:
		InputMap.add_action(action)
		for key: int in keys[action]:
			var event := InputEventKey.new()
			event.physical_keycode = key
			InputMap.action_add_event(action, event)


func _setup_viewports() -> void:
	scene_view.name = "SceneRender"
	scene_view.size = Vector2i(672, 420)
	scene_view.own_world_3d = true
	scene_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	scene_view.positional_shadow_atlas_size = 1024
	add_child(scene_view)
	scene_view.add_child(world)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = camera_size
	camera.near = 0.1
	camera.far = 80.0
	camera.current = true
	world.add_child(camera)
	mirror_view.name = "LiveReflection"
	mirror_view.size = Vector2i(336, 210)
	mirror_view.world_3d = scene_view.find_world_3d()
	mirror_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(mirror_view)
	mirror_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	mirror_camera.near = 0.1
	mirror_camera.far = 80.0
	mirror_camera.cull_mask = 1
	mirror_camera.current = true
	mirror_view.add_child(mirror_camera)


func _setup_environment() -> void:
	world_environment.background_mode = Environment.BG_COLOR
	world_environment.background_color = Color("020509")
	world_environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	world_environment.ambient_light_color = Color("738b9c")
	world_environment.ambient_light_energy = 0.24
	world_environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world_environment.fog_enabled = true
	world_environment.fog_light_color = Color("0c141d")
	world_environment.fog_density = 0.006
	var environment := WorldEnvironment.new()
	environment.environment = world_environment
	world.add_child(environment)
	moon.rotation_degrees = Vector3(-48, -32, 0)
	moon.light_color = Color("9fbfdd")
	moon.light_energy = 0.7
	moon.shadow_enabled = true
	moon.directional_shadow_max_distance = 35.0
	world.add_child(moon)
	for pos in [Vector3(-2.2, 1.6, -5.7), Vector3(4.9, 1.3, 2.0)]:
		_lantern(pos)


func _build_courtyard() -> void:
	var courtyard := COURTYARD.instantiate()
	world.add_child(courtyard)
	for node in courtyard.find_children("*", "MeshInstance3D"):
		if "Ground" in node.name:
			node.layers = 2
	_collider(Vector3(0, -0.16, 0), Vector3(24, 0.30, 22))
	for side in [-1.0, 1.0]:
		_collider(Vector3(side * 11.7, 1, 0), Vector3(0.4, 2, 23))
		_collider(Vector3(0, 1, side * 10.7), Vector3(24, 2, 0.4))
		_collider(Vector3(side * 2.38, 2.3, -6.8), Vector3(1.05, 4.6, 1.1))
		_collider(Vector3(side * 5.4, 1, -6.8), Vector3(5.3, 2, 1.0))
	for pos in [Vector3(-5.5, 0.5, -4.5), Vector3(5.6, 0.5, 4.8)]:
		_collider(pos, Vector3(2.1, 1, 0.65))


func _collider(pos: Vector3, size: Vector3) -> void:
	var body := StaticBody3D.new()
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	collision.shape = shape
	body.position = pos
	body.add_child(collision)
	world.add_child(body)


func _build_water() -> void:
	water_material.shader = preload("res://shaders/water.gdshader")
	water_material.set_shader_parameter("reflection_texture", mirror_view.get_texture())
	var water := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(8.0, 6.0)
	water.mesh = plane
	water.material_override = water_material
	water.position.y = WATER_HEIGHT
	water.layers = 4
	world.add_child(water)


func _build_grass() -> void:
	wind_material.shader = preload("res://shaders/wind.gdshader")
	var blade := ArrayMesh.new()
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array(
		[
			Vector3(-0.035, 0, 0),
			Vector3(0.035, 0, 0),
			Vector3(0.025, 0.40, 0),
			Vector3(-0.025, 0.40, 0),
			Vector3(0.08, 0.78, 0)
		]
	)
	arrays[Mesh.ARRAY_NORMAL] = PackedVector3Array(
		[Vector3.FORWARD, Vector3.FORWARD, Vector3.FORWARD, Vector3.FORWARD, Vector3.FORWARD]
	)
	arrays[Mesh.ARRAY_TEX_UV] = PackedVector2Array(
		[Vector2(0, 0), Vector2(1, 0), Vector2(1, 0.5), Vector2(0, 0.5), Vector2(0.5, 1)]
	)
	arrays[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3, 3, 2, 4])
	blade.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = blade
	multimesh.instance_count = 2400
	for i in range(multimesh.instance_count):
		var pos := Vector3(rng.randf_range(-10.7, 10.7), 0.04, rng.randf_range(-10.0, 10.0))
		while (abs(pos.x) < 4.9 and abs(pos.z) < 3.8) or (abs(pos.x) < 1.5 and abs(pos.z) < 8.5):
			pos.x = rng.randf_range(-10.7, 10.7)
			pos.z = rng.randf_range(-10.0, 10.0)
		var scale_factor := rng.randf_range(0.45, 1.15)
		var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * scale_factor)
		multimesh.set_instance_transform(i, Transform3D(basis, pos))
	var grass := MultiMeshInstance3D.new()
	grass.multimesh = multimesh
	grass.material_override = wind_material
	grass.custom_aabb = AABB(Vector3(-12, -1, -12), Vector3(24, 4, 24))
	grass.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	world.add_child(grass)


func _build_rain() -> void:
	rain_material.shader = preload("res://shaders/rain.gdshader")
	var stroke := CylinderMesh.new()
	stroke.top_radius = 0.014
	stroke.bottom_radius = 0.014
	stroke.height = 0.60
	stroke.radial_segments = 4
	stroke.cap_top = false
	stroke.cap_bottom = false
	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_custom_data = true
	multimesh.mesh = stroke
	multimesh.instance_count = 650
	for i in range(multimesh.instance_count):
		var pos := Vector3(rng.randf_range(-12, 12), 0, rng.randf_range(-12, 12))
		multimesh.set_instance_transform(i, Transform3D(Basis(Vector3.UP, 0.3), pos))
		multimesh.set_instance_custom_data(i, Color(rng.randf(), rng.randf(), 0, 1))
	rain = MultiMeshInstance3D.new()
	rain.multimesh = multimesh
	rain.material_override = rain_material
	rain.custom_aabb = AABB(Vector3(-16, -1, -16), Vector3(32, 17, 32))
	rain.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	world.add_child(rain)


func _lantern(pos: Vector3) -> void:
	var post := MeshInstance3D.new()
	var shaft := CylinderMesh.new()
	shaft.top_radius = 0.045
	shaft.bottom_radius = 0.07
	shaft.height = pos.y
	shaft.radial_segments = 6
	post.mesh = shaft
	post.position = Vector3(pos.x, pos.y / 2, pos.z)
	var iron := StandardMaterial3D.new()
	iron.albedo_color = Color("252a30")
	post.material_override = iron
	world.add_child(post)
	var lens := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(0.18, 0.3, 0.18)
	lens.mesh = box
	lens.position = pos
	var emission := StandardMaterial3D.new()
	emission.albedo_color = Color("e3af62")
	emission.emission_enabled = true
	emission.emission = Color("ffcc78")
	emission.emission_energy_multiplier = 2.5
	lens.material_override = emission
	world.add_child(lens)
	var light := OmniLight3D.new()
	light.position = pos
	light.light_color = Color("ffbd75")
	light.light_energy = 4.0
	light.omni_range = 6.0
	light.shadow_enabled = false
	world.add_child(light)


func _setup_display() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var display := ColorRect.new()
	display.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	display.mouse_filter = Control.MOUSE_FILTER_IGNORE
	glyph_material.shader = preload("res://shaders/glyphs.gdshader")
	glyph_material.set_shader_parameter("scene_texture", scene_view.get_texture())
	glyph_material.set_shader_parameter("glyph_atlas", preload("res://assets/glyph-atlas.png"))
	display.material = glyph_material
	layer.add_child(display)


func _setup_hud() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 2
	add_child(layer)
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(hud)
	var title := Label.new()
	title.text = "STORM / GLYPH COURTYARD"
	title.position = Vector2(32, 24)
	title.add_theme_font_size_override("font_size", 23)
	title.add_theme_color_override("font_color", Color("e1e3d7"))
	hud.add_child(title)
	var subtitle := Label.new()
	subtitle.text = "HEADLESS BLENDER GEOMETRY  /  GODOT LIVE RENDER"
	subtitle.position = Vector2(34, 56)
	subtitle.add_theme_font_size_override("font_size", 12)
	subtitle.add_theme_color_override("font_color", Color("9bacb2"))
	hud.add_child(subtitle)
	var controls := HBoxContainer.new()
	controls.position = Vector2(32, 88)
	controls.add_theme_constant_override("separation", 8)
	hud.add_child(controls)
	for entry in [
		["GLYPHS [1]", "ascii"],
		["RAIN [2]", "rain"],
		["WIND [3]", "wind"],
		["REFLECTION [4]", "reflection"]
	]:
		var button := Button.new()
		button.text = entry[0]
		button.toggle_mode = true
		button.button_pressed = true
		button.focus_mode = Control.FOCUS_NONE
		button.add_theme_font_size_override("font_size", 12)
		button.pressed.connect(_toggle.bind(entry[1]))
		controls.add_child(button)
		effect_buttons[entry[1]] = button
	var footer := PanelContainer.new()
	footer.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	footer.offset_top = -74
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.035, 0.06, 0.09, 0.90)
	style.content_margin_left = 32
	style.content_margin_top = 10
	style.content_margin_right = 32
	style.content_margin_bottom = 10
	footer.add_theme_stylebox_override("panel", style)
	hud.add_child(footer)
	var lines := VBoxContainer.new()
	footer.add_child(lines)
	var help := Label.new()
	help.text = (
		"WASD / ARROWS  move     SHIFT  run     Q / E  orbit     WHEEL  zoom"
		+ "     L  lantern     R  reset     H  hide UI"
	)
	help.add_theme_font_size_override("font_size", 14)
	lines.add_child(help)
	status_label.add_theme_font_size_override("font_size", 12)
	status_label.add_theme_color_override("font_color", Color("a2bbc4"))
	lines.add_child(status_label)
	frame_label.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	frame_label.offset_left = -100
	frame_label.offset_top = 30
	frame_label.offset_right = -24
	frame_label.add_theme_font_size_override("font_size", 12)
	hud.add_child(frame_label)


func _resize() -> void:
	var window_size := get_viewport().get_visible_rect().size
	var aspect := window_size.x / maxf(window_size.y, 1.0)
	scene_view.size = Vector2i(int(420 * aspect), 420)
	mirror_view.size = Vector2i(int(210 * aspect), 210)
	glyph_material.set_shader_parameter(
		"grid_size", Vector2(floor(window_size.x / 7.0), floor(window_size.y / 10.0))
	)


func _process(delta: float) -> void:
	elapsed += delta
	ripple_age += delta
	var orbit := Input.get_axis("rotate_left", "rotate_right")
	camera_yaw += orbit * delta * 0.9
	_update_cameras(delta)
	water_material.set_shader_parameter(
		"reflection_view", mirror_camera.global_transform.affine_inverse()
	)
	water_material.set_shader_parameter(
		"reflection_projection", mirror_camera.get_camera_projection()
	)
	water_material.set_shader_parameter("ripple_age", ripple_age)
	if abs(player.position.x) < 4 and abs(player.position.z) < 3:
		var step := Vector2(player.position.x, player.position.z)
		if step.distance_to(last_step) > 0.45:
			last_step = step
			ripple_age = 0
			water_material.set_shader_parameter("ripple_origin", step)
	var flash := 0.0
	if storm_enabled:
		var phase := fmod(elapsed, 13.0)
		if phase > 10.0 and phase < 10.15:
			flash = 3.5
		elif phase > 10.35 and phase < 10.44:
			flash = 2.0
	moon.light_energy = 0.7 + flash
	frame_label.text = "%d FPS" % Engine.get_frames_per_second()


func _update_cameras(delta: float) -> void:
	var wanted := player.position * 0.40
	wanted.y = 0
	camera_target = camera_target.lerp(wanted, 1.0 - exp(-delta * 3.0))
	var offset := Vector3(sin(camera_yaw) * 15.0, 12.5, cos(camera_yaw) * 15.0)
	camera.position = camera_target + offset
	camera.size = camera_size
	camera.look_at(camera_target + Vector3(0, 2.2, 0))
	mirror_camera.size = camera_size
	mirror_camera.position = Vector3(
		camera.position.x, 2 * WATER_HEIGHT - camera.position.y, camera.position.z
	)
	var target := camera_target + Vector3(0, 2.2, 0)
	target.y = 2 * WATER_HEIGHT - target.y
	mirror_camera.look_at(target, Vector3.DOWN)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1:
				_toggle("ascii")
			KEY_2:
				_toggle("rain")
			KEY_3:
				_toggle("wind")
			KEY_4:
				_toggle("reflection")
			KEY_L:
				player.toggle_lantern()
			KEY_R:
				player.reset()
			KEY_H:
				hud_visible = not hud_visible
				hud.visible = hud_visible
			KEY_ESCAPE:
				hud_visible = true
				hud.visible = true
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			camera_size = maxf(camera_size - 1.0, 11.0)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			camera_size = minf(camera_size + 1.0, 26.0)


func _toggle(effect: String) -> void:
	match effect:
		"ascii":
			ascii_enabled = not ascii_enabled
			glyph_material.set_shader_parameter("ascii_enabled", ascii_enabled)
		"rain":
			storm_enabled = not storm_enabled
			rain.visible = storm_enabled
			water_material.set_shader_parameter("rain_amount", 1.0 if storm_enabled else 0.0)
		"wind":
			wind_enabled = not wind_enabled
			wind_material.set_shader_parameter("wind_strength", 1.0 if wind_enabled else 0.0)
			rain_material.set_shader_parameter("wind_strength", 1.0 if wind_enabled else 0.0)
		"reflection":
			reflections_enabled = not reflections_enabled
			water_material.set_shader_parameter("reflections_enabled", reflections_enabled)
			mirror_view.render_target_update_mode = (
				SubViewport.UPDATE_ALWAYS if reflections_enabled else SubViewport.UPDATE_DISABLED
			)
	_update_status()


func _update_status() -> void:
	var values := {
		"ascii": ascii_enabled,
		"rain": storm_enabled,
		"wind": wind_enabled,
		"reflection": reflections_enabled
	}
	for effect: String in effect_buttons:
		effect_buttons[effect].set_pressed_no_signal(values[effect])
	status_label.text = (
		"Live planar reflection / ripple distortion / vertex wind / geometric rain."
		+ " Not real-time ray tracing."
	)
