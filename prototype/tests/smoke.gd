extends SceneTree

var errors := 0


func _initialize() -> void:
	call_deferred("_run")
	_watchdog()


func _watchdog() -> void:
	var timer := Timer.new()
	timer.wait_time = 20.0
	timer.one_shot = true
	timer.ignore_time_scale = true
	timer.autostart = true
	timer.timeout.connect(_timeout)
	root.add_child(timer)


func _timeout() -> void:
	push_error("Smoke check timed out")
	quit(1)


func _check(condition: bool, description: String) -> void:
	if not condition:
		push_error(description)
		errors += 1
	else:
		print("PASS: ", description)


func _run() -> void:
	var demo = load("res://main.tscn").instantiate()
	root.add_child(demo)
	await process_frame
	await process_frame
	if not is_instance_valid(demo.player):
		push_error("Player failed to initialize")
		quit(1)
		return
	_check(demo.world.get_child_count() > 20, "World contains imported geometry and effect nodes")
	_check(
		demo.scene_view.find_world_3d() == demo.mirror_view.find_world_3d(),
		"Reflection renders the actual shared 3D world"
	)
	_check(
		demo.mirror_camera.cull_mask == 1,
		"Reflection excludes ground and reflective water to prevent feedback"
	)
	_check(
		abs(demo.mirror_camera.position.y + demo.camera.position.y - 2 * demo.WATER_HEIGHT) < 0.001,
		"Reflection camera mirrors across the water plane"
	)
	for effect in ["ascii", "rain", "wind", "reflection"]:
		demo._toggle(effect)
	_check(
		(
			not demo.ascii_enabled
			and not demo.storm_enabled
			and not demo.wind_enabled
			and not demo.reflections_enabled
		),
		"All effect toggles disable independently"
	)
	_check(not demo.rain.visible, "Disabled rain stops drawing")
	_check(
		demo.wind_material.get_shader_parameter("wind_strength") == 0.0,
		"Disabled wind stops vertex displacement"
	)
	_check(
		demo.mirror_view.render_target_update_mode == SubViewport.UPDATE_DISABLED,
		"Disabled reflection stops the extra render"
	)
	for effect in ["ascii", "rain", "wind", "reflection"]:
		demo._toggle(effect)
	_check(
		(
			demo.ascii_enabled
			and demo.storm_enabled
			and demo.wind_enabled
			and demo.reflections_enabled
		),
		"All effects re-enable"
	)
	Engine.time_scale = 8.0
	for i in range(15):
		await physics_frame
	var start: Vector3 = demo.player.position
	Input.action_press("move_right")
	for i in range(20):
		await physics_frame
	Input.action_release("move_right")
	_check(
		demo.player.position.distance_to(start) > 0.3,
		"Camera-relative movement changes player position"
	)
	_check(demo.player.position.y > -0.05, "Player stays on collision floor")
	Input.action_press("sprint")
	Input.action_press("move_left")
	for i in range(15):
		await physics_frame
	_check(
		Vector2(demo.player.velocity.x, demo.player.velocity.z).length() > 3.5,
		"Sprint exceeds walking speed"
	)
	Input.action_release("move_left")
	Input.action_release("sprint")
	demo.player.position = Vector3(11.1, 0.1, 0)
	demo.camera_yaw = 0
	demo._update_cameras(1)
	Input.action_press("move_right")
	for i in range(30):
		await physics_frame
	Input.action_release("move_right")
	_check(demo.player.position.x < 11.5, "Boundary collision prevents escaping the courtyard")
	demo.player.reset()
	_check(
		demo.player.position.distance_to(Vector3(0, 0.15, 5.5)) < 0.01,
		"Reset restores player spawn"
	)
	demo.player.toggle_lantern()
	_check(
		not demo.player.lamp.visible and not demo.player.glow.visible,
		"Player lantern can be switched off"
	)
	print("STORM_SMOKE: ", errors, " failures")
	demo.queue_free()
	await process_frame
	quit(1 if errors else 0)
