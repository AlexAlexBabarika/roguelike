extends SceneTree

var failures := 0


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, description: String) -> void:
	if not condition:
		failures += 1
		push_error("PAINTED_TEST: " + description)


func _run() -> void:
	root.size = Vector2i(720, 405)
	if "--ignore-aspect" in OS.get_cmdline_user_args():
		root.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_IGNORE
	var scene = load("res://style_study.tscn").instantiate()
	scene.arm = "I1"
	scene.frozen = true
	root.add_child(scene)
	scene.hud.visible = false
	for frame in range(20):
		await process_frame
	await RenderingServer.frame_post_draw
	_check(scene.paint_pass != null, "selective painterly pass exists")
	var main_projection: Projection = scene.camera.get_camera_projection()
	var mask_projection: Projection = scene.paint_pass.mask_camera.get_camera_projection()
	_check(
		is_equal_approx(main_projection.x.x, mask_projection.x.x),
		"mask follows letterboxed camera frustum"
	)
	_check(
		scene.get_node("PaintedSpruceCrowns").multimesh.instance_count == 1254, "57 cards per tree"
	)
	var roofs := 0
	for material in scene.study_materials:
		if material.get_shader_parameter("roof"):
			roofs += 1
	_check(roofs > 0, "roof material classifier reaches clinic slate")
	var painted := root.get_texture().get_image()
	var mask: Image = scene.paint_pass.mask_view.get_texture().get_image()
	mask.resize(painted.get_width(), painted.get_height(), Image.INTERPOLATE_NEAREST)
	var event := InputEventKey.new()
	event.physical_keycode = KEY_P
	event.pressed = true
	scene._unhandled_input(event)
	_check(not scene.filter_enabled, "P disables only the screen filter")
	for frame in range(3):
		await process_frame
	await RenderingServer.frame_post_draw
	var plain := root.get_texture().get_image()
	painted.save_png("res://../artifacts/painted-on.png")
	plain.save_png("res://../artifacts/painted-off.png")
	mask.save_png("res://../artifacts/painted-mask.png")
	var protected_delta := 0.0
	var background_delta := 0.0
	var protected_pixels := 0
	var background_pixels := 0
	for y in range(0, painted.get_height(), 3):
		for x in range(0, painted.get_width(), 3):
			var a := painted.get_pixel(x, y)
			var b := plain.get_pixel(x, y)
			var difference := (absf(a.r - b.r) + absf(a.g - b.g) + absf(a.b - b.b)) / 3.0
			if mask.get_pixel(x, y).r > 0.95:
				protected_delta += difference
				protected_pixels += 1
			elif mask.get_pixel(x, y).r < 0.01:
				background_delta += difference
				background_pixels += 1
	_check(protected_pixels > 50, "actual geometry produces a nonempty sharp mask")
	_check(background_pixels > 1000, "background remains outside the protection mask")
	protected_delta /= maxf(1, protected_pixels)
	background_delta /= maxf(1, background_pixels)
	_check(protected_delta < 0.005, "protected shapes retain their unfiltered pixels")
	_check(background_delta > 0.002, "filter visibly changes the environment")
	print("PAINTED_DELTAS: protected=", protected_delta, " background=", background_delta)
	scene._unhandled_input(event)
	_check(scene.filter_enabled, "P restores the painterly filter")
	_check(scene.rain.visible and scene.reflections_enabled, "weather and reflections preserved")
	print("PAINTED_RENDER: ", failures, " failures")
	scene.queue_free()
	await process_frame
	quit(failures)
