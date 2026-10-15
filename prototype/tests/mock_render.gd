extends SceneTree


func _initialize() -> void:
	_run.call_deferred()
	create_timer(90.0).timeout.connect(func() -> void: quit(1))


func _frames(count: int) -> void:
	for frame in range(count):
		await process_frame
	await RenderingServer.frame_post_draw


func _difference(a: Image, b: Image) -> float:
	var difference := 0.0
	for y in range(0, a.get_height(), 4):
		for x in range(0, a.get_width(), 4):
			var on := a.get_pixel(x, y)
			var off := b.get_pixel(x, y)
			difference += absf(on.r - off.r) + absf(on.g - off.g) + absf(on.b - off.b)
	return difference


func _run() -> void:
	var mock = load("res://mock_scene.tscn").instantiate()
	root.add_child(mock)
	mock.frozen = true
	mock.hud.visible = false
	await _frames(20)
	var enabled := root.get_texture().get_image()
	if enabled.is_empty():
		push_error("Mock render is empty")
		quit(1)
		return
	var arguments := OS.get_cmdline_user_args()
	var output := arguments[0] if arguments.size() else "user://mock.png"
	var error := enabled.save_png(output)
	if error != OK:
		quit(error)
		return
	mock._set_reflections(false)
	await _frames(3)
	var disabled := root.get_texture().get_image()
	var reflection_difference := _difference(enabled, disabled)
	mock.rain.visible = false
	await _frames(3)
	var dry := root.get_texture().get_image()
	var rain_difference := _difference(disabled, dry)
	print("MOCK_PIXELS: reflection difference ", reflection_difference)
	print("MOCK_PIXELS: rain difference ", rain_difference)
	if reflection_difference < 5.0 or rain_difference < 0.5:
		push_error("Mock reflection or rain failed the actual-render pixel check")
		quit(1)
		return
	for preset in ["clinic", "traveler"]:
		mock._set_view(preset)
		await _frames(3)
	print("MOCK_RENDER: ", output, " / ", enabled.get_size(), " / passed")
	quit(0)
