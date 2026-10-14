extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var demo = load("res://main.tscn").instantiate()
	root.add_child(demo)
	var args := OS.get_cmdline_user_args()
	if "--raw" in args:
		demo._toggle("ascii")
	if "--no-rain" in args:
		demo._toggle("rain")
	if "--verify" in args:
		demo._toggle("ascii")
		demo._toggle("rain")
		demo._toggle("wind")
	for i in range(45):
		await process_frame
	await RenderingServer.frame_post_draw
	if "--verify" in args:
		demo.set_process(false)
		var reflection: Image = demo.mirror_view.get_texture().get_image()
		var reflected := _average(reflection)
		var enabled: Image = demo.scene_view.get_texture().get_image()
		demo._toggle("reflection")
		for i in range(3):
			await process_frame
		await RenderingServer.frame_post_draw
		var disabled: Image = demo.scene_view.get_texture().get_image()
		var difference := 0.0
		for y in range(0, enabled.get_height(), 4):
			for x in range(0, enabled.get_width(), 4):
				var on := enabled.get_pixel(x, y)
				var off := disabled.get_pixel(x, y)
				difference += absf(on.r - off.r) + absf(on.g - off.g) + absf(on.b - off.b)
		print(
			"STORM_PIXELS: reflection brightness ", reflected, " / toggle difference ", difference
		)
		if reflected < 0.025 or difference < 30.0:
			push_error("Live reflection failed the actual-render pixel check")
			quit(1)
			return
		demo._toggle("reflection")
		for i in range(3):
			await process_frame
		await RenderingServer.frame_post_draw
	var output := (
		OS.get_cmdline_user_args()[0] if OS.get_cmdline_user_args().size() else "user://storm.png"
	)
	var image := root.get_texture().get_image()
	if "--reflection" in args:
		image = demo.mirror_view.get_texture().get_image()
	var error := image.save_png(output)
	print("STORM_RENDER: ", output, " / ", image.get_size(), " / error ", error)
	quit(error)


func _average(image: Image) -> float:
	var total := 0.0
	var count := 0
	for y in range(0, image.get_height(), 4):
		for x in range(0, image.get_width(), 4):
			var color := image.get_pixel(x, y)
			total += (color.r + color.g + color.b) / 3.0
			count += 1
	return total / float(count)
