extends Camera3D

@export var rotation_speed = 0.1
@export var zoom_speed = 0.5
@export var min_zoom = 5.0
@export var max_zoom = 20.0

var is_rotating = false
var last_mouse_pos = Vector2.ZERO

func _unhandled_input(event):
    if event is InputEventMouseButton:
        if event.button_index == MOUSE_BUTTON_MIDDLE:
            is_rotating = event.pressed
            last_mouse_pos = event.position
        elif event.button_index == MOUSE_BUTTON_WHEEL_UP:
            zoom_camera(-zoom_speed)
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            zoom_camera(zoom_speed)
    
    elif event is InputEventMouseMotion and is_rotating:
        var delta = event.position - last_mouse_pos
        rotate_camera(delta)
        last_mouse_pos = event.position

func rotate_camera(delta: Vector2):
    # Rotate around the Y axis for horizontal movement
    rotate_y(-delta.x * rotation_speed * 0.01)
    
    # Rotate around the local X axis for vertical movement
    var new_rotation = rotation.x + (-delta.y * rotation_speed * 0.01)
    rotation.x = clamp(new_rotation, -PI/3, PI/3)  # Limit vertical rotation

func zoom_camera(zoom_amount: float):
    var new_position = position + position.normalized() * zoom_amount
    if new_position.length() > min_zoom and new_position.length() < max_zoom:
        position = new_position
