extends SceneTree

var failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()
	create_timer(120.0).timeout.connect(func() -> void: quit(1))


func _check(condition: bool, label: String) -> void:
	print("FOREST_TEST: ", label, " / ", "pass" if condition else "FAIL")
	if not condition:
		failures.append(label)


func _frames() -> void:
	for frame in range(4):
		await process_frame
	await RenderingServer.frame_post_draw


func _difference(a: Image, b: Image) -> float:
	var sum := 0.0
	for y in range(0, a.get_height(), 3):
		for x in range(0, a.get_width(), 3):
			var pa := a.get_pixel(x, y)
			var pb := b.get_pixel(x, y)
			sum += absf(pa.r - pb.r) + absf(pa.g - pb.g) + absf(pa.b - pb.b)
	return sum


func _run() -> void:
	var scene = load("res://forest_slice.tscn").instantiate()
	root.add_child(scene)
	scene.frozen = true
	scene.wind_enabled = false
	scene.hud.visible = false
	scene._set_view("grove")
	await _frames()
	_check(
		not scene.environment.fog_enabled and not scene.rain.visible, "daylight without fog/rain"
	)
	_check(scene.sun.shadow_enabled, "daylight casts shadows")
	_check(scene.branch_texture.get_image().has_mipmaps(), "foliage has real texture mipmaps")
	_check(scene.trees.size() == 7, "seven deterministic tree placements")
	for material in scene.foliage_materials:
		_check(not material.get_shader_parameter("wind_enabled"), "wind-off reaches foliage shader")
	for tree in scene.trees:
		_check(tree.get_child_count() == 2, "only selected variant wood/needle meshes retained")
	var lit := root.get_texture().get_image()
	_check(not lit.is_empty(), "nonempty viewport image")
	scene.shadows_enabled = false
	scene._apply_conditions()
	await _frames()
	var no_shadow := root.get_texture().get_image()
	var shadow_delta := _difference(lit, no_shadow)
	_check(shadow_delta > 15.0, "cast shadows visibly affect pixels")
	scene.sun.light_energy = 0.0
	await _frames()
	var unlit := root.get_texture().get_image()
	var lighting_delta := _difference(no_shadow, unlit)
	_check(lighting_delta > 50.0, "sunlight visibly affects pixels")
	scene.sun.light_energy = 1.45
	scene.isolated = true
	scene._apply_isolation()
	scene._set_view("tree")
	scene.get_node("EarthFloor").visible = false
	scene.environment.background_mode = Environment.BG_COLOR
	scene.environment.background_color = Color("383f43")
	await _frames()
	var tree_lit := root.get_texture().get_image()
	scene.sun.light_energy = 0.0
	await _frames()
	var tree_unlit := root.get_texture().get_image()
	_check(_difference(tree_lit, tree_unlit) > 10.0, "isolated tree responds to light")
	var transforms: Array[Transform3D] = []
	for tree in scene.trees:
		transforms.append(tree.transform)
	for step in range(3):
		scene.yaw += 0.7
		scene._update_cameras()
		await _frames()
	for index in range(scene.trees.size()):
		_check(
			scene.trees[index].transform == transforms[index],
			"camera orbit does not billboard trees"
		)
	scene.silhouette = true
	scene._apply_silhouette()
	_check(
		not scene.context.visible and not scene.get_node("EarthFloor").visible,
		"silhouette isolates shape"
	)
	scene.silhouette = false
	scene.isolated = false
	scene.weather = true
	scene._apply_silhouette()
	_check(scene.environment.fog_enabled and scene.rain.visible, "weather optional, not baseline")
	scene.weather = false
	scene._apply_conditions()
	_check(not scene.environment.fog_enabled and not scene.rain.visible, "daylight restored")
	print("FOREST_DELTAS: shadows=", shadow_delta, " lighting=", lighting_delta)
	print("FOREST_TEST_RESULT: ", "passed" if failures.is_empty() else str(failures))
	quit(0 if failures.is_empty() else 1)
