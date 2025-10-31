extends Node3D

var black_material: Material
var white_material: Material

func _ready():
	# Load materials
	black_material = preload("res://materials/black_stone.tres")
	white_material = preload("res://materials/white_stone.tres")

func set_player(player: int):
	var mesh = $Mesh
	if not mesh:
		return
		
	match player:
		1:  # Black
			mesh.material_override = black_material
		2:  # White
			mesh.material_override = white_material
