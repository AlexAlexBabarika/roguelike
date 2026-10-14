extends CharacterBody3D

const WALK_SPEED := 3.0
const RUN_SPEED := 5.0
const GRAVITY := 18.0

var camera: Camera3D
var visual := Node3D.new()
var legs: Array[Node3D] = []
var arms: Array[Node3D] = []
var gait := 0.0
var lamp: SpotLight3D
var glow := OmniLight3D.new()
var lantern_enabled := true


func _ready() -> void:
	name = "Player"
	add_child(visual)
	var shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.23
	capsule.height = 1.3
	shape.shape = capsule
	shape.position.y = 0.67
	add_child(shape)
	var coat := _material(Color("8da19e"))
	var dark := _material(Color("182530"))
	var ochre := _material(Color("aa7042"))
	var body := CylinderMesh.new()
	body.top_radius = 0.19
	body.bottom_radius = 0.27
	body.height = 0.62
	body.radial_segments = 8
	_part(body, coat, Vector3(0, 0.83, 0), visual)
	var head := SphereMesh.new()
	head.radius = 0.16
	head.height = 0.32
	head.radial_segments = 8
	head.rings = 4
	_part(head, dark, Vector3(0, 1.30, 0), visual)
	var pack := BoxMesh.new()
	pack.size = Vector3(0.33, 0.34, 0.16)
	_part(pack, ochre, Vector3(0, 0.87, 0.25), visual)
	for side in [-1.0, 1.0]:
		var leg := Node3D.new()
		leg.position = Vector3(side * 0.12, 0.49, 0)
		visual.add_child(leg)
		legs.append(leg)
		var boot := BoxMesh.new()
		boot.size = Vector3(0.14, 0.40, 0.18)
		_part(boot, dark, Vector3(0, -0.20, 0), leg)
		var arm := Node3D.new()
		arm.position = Vector3(side * 0.27, 1.03, 0)
		visual.add_child(arm)
		arms.append(arm)
		var sleeve := BoxMesh.new()
		sleeve.size = Vector3(0.12, 0.39, 0.14)
		_part(sleeve, coat, Vector3(0, -0.16, 0), arm)
	lamp = SpotLight3D.new()
	lamp.position = Vector3(0, 1.05, -0.30)
	lamp.rotation.x = -0.40
	lamp.light_color = Color("ffcc8e")
	lamp.light_energy = 3.0
	lamp.spot_range = 9.0
	lamp.spot_angle = 48.0
	visual.add_child(lamp)
	glow.position.y = 0.8
	glow.light_color = Color("f2c791")
	glow.light_energy = 0.6
	glow.omni_range = 2.0
	visual.add_child(glow)


func _physics_process(delta: float) -> void:
	var input := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	var direction := Vector3(input.x, 0, input.y)
	if is_instance_valid(camera):
		var right := camera.global_basis.x
		var back := camera.global_basis.z
		right.y = 0
		back.y = 0
		direction = right.normalized() * input.x + back.normalized() * input.y
	var speed := RUN_SPEED if Input.is_action_pressed("sprint") else WALK_SPEED
	velocity.x = move_toward(velocity.x, direction.x * speed, 16.0 * delta)
	velocity.z = move_toward(velocity.z, direction.z * speed, 16.0 * delta)
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	else:
		velocity.y = 0
	move_and_slide()
	var horizontal_speed := Vector2(velocity.x, velocity.z).length()
	if horizontal_speed > 0.1:
		visual.rotation.y = lerp_angle(
			visual.rotation.y, atan2(-velocity.x, -velocity.z), delta * 12.0
		)
		gait += delta * horizontal_speed * 3.2
	visual.position.y = abs(sin(gait)) * min(horizontal_speed, 1.0) * 0.045
	for i in range(2):
		var swing := sin(gait + float(i) * PI) * minf(horizontal_speed / 5.0, 0.8)
		legs[i].rotation.x = swing
		arms[i].rotation.x = -swing * 0.65


func reset() -> void:
	position = Vector3(0, 0.15, 5.5)
	velocity = Vector3.ZERO
	gait = 0


func toggle_lantern() -> void:
	lantern_enabled = not lantern_enabled
	lamp.visible = lantern_enabled
	glow.visible = lantern_enabled


func _part(mesh: Mesh, material: Material, pos: Vector3, parent: Node3D) -> void:
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	instance.material_override = material
	instance.position = pos
	parent.add_child(instance)


func _material(color: Color) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.8
	return material
