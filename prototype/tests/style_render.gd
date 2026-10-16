extends SceneTree

var failures := 0


func _initialize() -> void:
	_run.call_deferred()


func _check(condition: bool, description: String) -> void:
	if not condition:
		failures += 1
		push_error("STYLE_TEST: " + description)


func _run() -> void:
	root.size = Vector2i(720, 405)
	var scene = load("res://style_study.tscn").instantiate()
	scene.arm = "G1"
	scene.atmosphere = true
	root.add_child(scene)
	scene.frozen = true
	scene.hud.visible = false
	for frame in range(20):
		await process_frame
	await RenderingServer.frame_post_draw
	_check(scene.has_node("PreparedBlenderKit"), "prepared kit loaded")
	_check(not scene.has_node("OriginalBlenderKit"), "baseline kit replaced only in study")
	_check(scene.has_node("NonGameplayWarningProbe"), "labelled warning probe")
	_check(scene.study_materials.size() > 10, "material treatment assigned")
	_check(
		is_equal_approx(scene.environment.ambient_light_energy, 0.28), "baseline ambient preserved"
	)
	_check(scene.rain.visible, "rain remains enabled")
	_check(scene.mirror_view.world_3d == scene.get_world_3d(), "reflection shares treatment")
	var protected := 0
	var textured := 0
	for material in scene.study_materials:
		if material.get_shader_parameter("actor"):
			protected += 1
		else:
			textured += 1
	_check(protected > 0 and textured > 0, "actor and environment classes remain separate")
	var image := root.get_texture().get_image()
	var low := 1.0
	var high := 0.0
	for y in range(0, image.get_height(), 8):
		for x in range(0, image.get_width(), 8):
			var pixel := image.get_pixel(x, y)
			low = minf(low, pixel.get_luminance())
			high = maxf(high, pixel.get_luminance())
	_check(high - low > 0.3, "nonempty rendered frame")
	print("STYLE_RENDER: ", scene.arm, " + H / ", failures, " failures")
	scene.queue_free()
	await process_frame
	quit(failures)
