extends SceneTree

var errors := 0


func _initialize() -> void:
	_run.call_deferred()
	create_timer(20.0).timeout.connect(func() -> void: quit(1))


func _check(condition: bool, description: String) -> void:
	if condition:
		print("PASS: ", description)
	else:
		push_error(description)
		errors += 1


func _key(mock: Node, code: Key) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	mock._unhandled_input(event)


func _run() -> void:
	var mock = load("res://mock_scene.tscn").instantiate()
	root.add_child(mock)
	await process_frame
	mock.frozen = true
	var kit: Node = mock.get_node("OriginalBlenderKit")
	for group in ["Ground", "Clinic", "Windows", "Porch", "Roof", "Forest", "Props", "Traveler"]:
		_check(kit.get_node_or_null(NodePath(group)) is MeshInstance3D, "Imported " + group)
	_check(mock.foliage_materials.size() >= 5, "Spruce surfaces use the wind material")
	_check(mock.mirror_view.world_3d == mock.get_world_3d(), "Reflection shares the live world")
	_check(mock.mirror_camera.cull_mask == 1, "Reflection excludes ground, water and rain")
	_check(kit.get_node("Ground").layers == 2, "Ground is excluded from reflections")
	for preset in [KEY_1, KEY_2, KEY_3]:
		_key(mock, preset)
		_check(
			absf(mock.camera.position.y + mock.mirror_camera.position.y - 0.13) < 0.001,
			"Reflection mirrors the water plane after camera preset %d" % preset
		)
		_check(mock.camera.size == mock.mirror_camera.size, "Camera scales agree")
	_key(mock, KEY_1)
	_check(is_equal_approx(mock.camera_size, 20.5), "Wide view can be restored")
	_key(mock, KEY_R)
	_check(not mock.rain.visible, "Rain toggle disables visible streaks")
	_key(mock, KEY_R)
	_check(mock.rain.visible, "Rain toggle restores visible streaks")
	_key(mock, KEY_F)
	_check(not mock.reflections_enabled, "Reflection toggle disables sampling")
	_check(
		mock.mirror_view.render_target_update_mode == SubViewport.UPDATE_DISABLED,
		"Reflection toggle stops the second render"
	)
	_key(mock, KEY_F)
	_check(mock.reflections_enabled, "Reflection toggle restores sampling")
	_key(mock, KEY_SPACE)
	_check(not mock.frozen, "Space resumes the clock")
	_key(mock, KEY_SPACE)
	_check(mock.frozen, "Space freezes the clock")
	_key(mock, KEY_H)
	_check(not mock.hud.visible, "HUD can be hidden")
	_key(mock, KEY_H)
	_check(mock.hud.visible, "HUD can be restored")
	var event := InputEventMouseButton.new()
	event.pressed = true
	event.button_index = MOUSE_BUTTON_WHEEL_UP
	mock._unhandled_input(event)
	_check(is_equal_approx(mock.camera_size, 19.5), "Mouse wheel zoom changes the camera")
	_check(mock.mirror_view.size.x > 0 and mock.mirror_view.size.y > 0, "Reflection has a size")
	print("MOCK_SMOKE: ", errors, " failures")
	quit(1 if errors else 0)
