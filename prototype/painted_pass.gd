extends Node

const PAINTERLY = preload("res://shaders/study_painterly.gdshader")
const PROTECTION = preload("res://shaders/study_protection.gdshader")
const RAIN_PROTECTION = preload("res://shaders/study_rain_protection.gdshader")

var scene
var mask_view := SubViewport.new()
var mask_camera := Camera3D.new()
var paint_material := ShaderMaterial.new()
var white := ShaderMaterial.new()
var rain_mask := MultiMeshInstance3D.new()
var rain_mask_material := ShaderMaterial.new()
var paint_layer := CanvasLayer.new()


func _ready() -> void:
	white.shader = PROTECTION
	mask_view.name = "ProtectedSilhouettes"
	mask_view.own_world_3d = true
	mask_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	mask_view.msaa_3d = Viewport.MSAA_4X
	add_child(mask_view)
	var backdrop := Environment.new()
	backdrop.background_mode = Environment.BG_COLOR
	backdrop.background_color = Color.BLACK
	mask_camera.environment = backdrop
	mask_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	mask_camera.far = scene.camera.far
	mask_view.add_child(mask_camera)
	for part in scene.find_children("*", "MeshInstance3D", true, false):
		if part.name == "Traveler" or part.name.begins_with("NonGameplay"):
			_add_mask(part.mesh, part.global_transform)
		elif part.get_parent().name == "PreparedBlenderKit":
			for index in range(part.mesh.get_surface_count()):
				var base := part.mesh.surface_get_material(index) as StandardMaterial3D
				if (
					base != null
					and base.resource_name in ["Warm glass", "Ivory enamel", "Faded clinic cross"]
				):
					var panes := ArrayMesh.new()
					panes.add_surface_from_arrays(
						Mesh.PRIMITIVE_TRIANGLES, part.mesh.surface_get_arrays(index)
					)
					_add_mask(panes, part.global_transform)
	rain_mask.multimesh = scene.rain.multimesh
	rain_mask.custom_aabb = scene.rain.custom_aabb
	rain_mask_material.shader = RAIN_PROTECTION
	rain_mask.material_override = rain_mask_material
	mask_view.add_child(rain_mask)
	paint_layer.layer = 0
	add_child(paint_layer)
	var panel := ColorRect.new()
	panel.name = "PainterlyBackground"
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	paint_material.shader = PAINTERLY
	paint_material.set_shader_parameter("protection", mask_view.get_texture())
	panel.material = paint_material
	paint_layer.add_child(panel)
	_process(0.0)


func _add_mask(mesh: Mesh, transform: Transform3D) -> void:
	var silhouette := MeshInstance3D.new()
	silhouette.mesh = mesh
	silhouette.material_override = white
	silhouette.transform = transform
	mask_view.add_child(silhouette)


func _process(_delta: float) -> void:
	var window_size: Vector2i = scene.get_viewport().size
	var projection: Projection = scene.camera.get_camera_projection()
	var aspect := projection.y.y / projection.x.x
	# Window.size includes letterboxing; the mask must match the actual camera frustum.
	var height := mini(window_size.y, roundi(float(window_size.x) / aspect))
	var size := Vector2i(maxi(1, roundi(height * aspect)), maxi(1, height))
	if mask_view.size != size:
		mask_view.size = size
	mask_camera.global_transform = scene.camera.global_transform
	mask_camera.size = scene.camera.size
	mask_camera.near = scene.camera.near
	rain_mask.visible = scene.rain_enabled
	rain_mask_material.set_shader_parameter("clock", scene.elapsed)
	paint_material.set_shader_parameter("radius_pixels", 3.5 * float(size.y) / 720.0)
