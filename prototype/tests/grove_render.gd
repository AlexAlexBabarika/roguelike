extends SceneTree

var failures: Array[String] = []


func _initialize() -> void:
	_run.call_deferred()
	create_timer(150.0).timeout.connect(func() -> void: quit(1))


func _check(condition: bool, label: String) -> void:
	print("GROVE_TEST: ", label, " / ", "pass" if condition else "FAIL")
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
	var scene = load("res://clinic_grove.tscn").instantiate()
	root.add_child(scene)
	scene.frozen = true
	scene.wind_enabled = false
	scene.hud.visible = false
	await _frames()
	_check(not scene.environment.fog_enabled and not scene.rain.visible, "default is dry daylight")
	_check(scene.trees.size() == 19, "nineteen deterministic artist-authored tree placements")
	_check(scene.cover.get_child_count() > 70, "rock and fern dressing retained")
	var floor_part := scene.get_node("EarthFloor") as MeshInstance3D
	var arrays := floor_part.mesh.surface_get_arrays(0)
	var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
	_check(normals[0].dot(Vector3.UP) > 0.95, "ground winding and normals face the camera")
	for channel in ["color", "normal"]:
		var terrain := scene.ground_material.get_shader_parameter("terrain_" + channel) as Texture2D
		_check(terrain.get_image().has_mipmaps(), "baked terrain " + channel + " has mipmaps")
	_check(scene._path_distance(-0.55, 0.8) < 0.01, "worn path meets clinic entrance")
	_check(scene._path_distance(4.0, 5.0) > 3.0, "understory stays outside the path")
	for material in scene.foliage_materials:
		_check(not material.get_shader_parameter("wind_enabled"), "wind-off reaches source foliage")
		var texture := material.get_shader_parameter("color_map") as Texture2D
		_check(texture.get_image().has_mipmaps(), "foliage atlas has mipmaps")
	scene.elapsed = 7.5
	scene._process(0.0)
	_check(
		scene.foliage_materials[0].get_shader_parameter("clock") == 7.5,
		"wind clock reaches foliage"
	)
	var lit := root.get_texture().get_image()
	scene.shadows_enabled = false
	scene._apply_conditions()
	await _frames()
	var no_shadow := root.get_texture().get_image()
	_check(_difference(lit, no_shadow) > 20.0, "shadows affect actual rendered pixels")
	scene.sun.light_energy = 0.0
	await _frames()
	_check(
		_difference(no_shadow, root.get_texture().get_image()) > 50.0,
		"surfaces respond to sunlight"
	)
	scene._apply_conditions()
	await _frames()
	var detailed := root.get_texture().get_image()
	scene.ground_material.set_shader_parameter("detail_strength", 0.0)
	await _frames()
	_check(
		_difference(detailed, root.get_texture().get_image()) > 100.0,
		"baked terrain affects actual rendered pixels"
	)
	scene.ground_material.set_shader_parameter("detail_strength", 1.0)
	await _frames()
	floor_part.visible = false
	await _frames()
	_check(
		_difference(no_shadow, root.get_texture().get_image()) > 200.0,
		"textured terrain is visible"
	)
	floor_part.visible = true
	var transform: Transform3D = scene.trees[0].transform
	scene.yaw += 1.1
	scene._update_cameras()
	await _frames()
	_check(scene.trees[0].transform == transform, "tree does not billboard when camera orbits")
	scene.silhouette = true
	scene._apply_silhouette()
	_check(
		not scene.context.visible and not floor_part.visible,
		"silhouette hides clinic and ground cover"
	)
	_check(
		scene.trees[0].visible and not scene.trees[1].visible, "silhouette selects only hero tree"
	)
	scene.silhouette = false
	scene.weather = true
	scene._apply_silhouette()
	_check(scene.rain.visible and scene.environment.fog_enabled, "optional weather toggles on")
	scene.weather = false
	scene._apply_conditions()
	_check(not scene.rain.visible and not scene.environment.fog_enabled, "daylight restores")
	print("GROVE_TEST_RESULT: ", "passed" if failures.is_empty() else str(failures))
	quit(0 if failures.is_empty() else 1)
