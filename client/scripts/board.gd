extends Node3D

@export var board_size = 15
@export var cell_size = 1.0
@export var board_thickness = 0.1

@onready var board_mesh = $BoardMesh
@onready var grid_lines = $GridLines
@onready var highlight = $Highlight

var material_board = StandardMaterial3D.new()
var material_lines = StandardMaterial3D.new()
var material_highlight = StandardMaterial3D.new()

func _ready():
    # Set up materials
    material_board.albedo_color = Color(0.7, 0.5, 0.3)  # Wooden color
    material_board.roughness = 0.8
    
    material_lines.albedo_color = Color.BLACK
    material_lines.roughness = 0.5
    
    material_highlight.albedo_color = Color(1, 1, 0, 0.3)  # Semi-transparent yellow
    material_highlight.transparency = StandardMaterial3D.TRANSPARENCY_ALPHA
    
    create_board()
    create_grid()
    create_highlight()

func create_board():
    var mesh = BoxMesh.new()
    mesh.size = Vector3(board_size * cell_size, board_thickness, board_size * cell_size)
    board_mesh.mesh = mesh
    board_mesh.material_override = material_board

func create_grid():
    var immediate_mesh = ImmediateMesh.new()
    grid_lines.mesh = immediate_mesh
    grid_lines.material_override = material_lines
    
    # Draw horizontal lines
    for i in range(board_size):
        var start = Vector3(-board_size * cell_size / 2, board_thickness/2 + 0.001, (i - board_size/2) * cell_size)
        var end = Vector3(board_size * cell_size / 2, board_thickness/2 + 0.001, (i - board_size/2) * cell_size)
        immediate_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
        immediate_mesh.surface_add_vertex(start)
        immediate_mesh.surface_add_vertex(end)
        immediate_mesh.surface_end()
    
    # Draw vertical lines
    for i in range(board_size):
        var start = Vector3((i - board_size/2) * cell_size, board_thickness/2 + 0.001, -board_size * cell_size / 2)
        var end = Vector3((i - board_size/2) * cell_size, board_thickness/2 + 0.001, board_size * cell_size / 2)
        immediate_mesh.surface_begin(Mesh.PRIMITIVE_LINES)
        immediate_mesh.surface_add_vertex(start)
        immediate_mesh.surface_add_vertex(end)
        immediate_mesh.surface_end()

func create_highlight():
    var mesh = PlaneMesh.new()
    mesh.size = Vector2(cell_size * 0.9, cell_size * 0.9)
    highlight.mesh = mesh
    highlight.material_override = material_highlight
    highlight.visible = false

func highlight_cell(pos: Vector3):
    var grid_pos = world_to_grid(pos)
    if grid_pos:
        highlight.visible = true
        highlight.position = Vector3(
            grid_pos.x * cell_size,
            board_thickness/2 + 0.002,
            grid_pos.y * cell_size
        )
    else:
        highlight.visible = false

func world_to_grid(pos: Vector3) -> Vector2:
    var x = int(round((pos.x + board_size * cell_size / 2) / cell_size))
    var z = int(round((pos.z + board_size * cell_size / 2) / cell_size))
    
    if x >= 0 and x < board_size and z >= 0 and z < board_size:
        return Vector2(x - board_size/2, z - board_size/2)
    return Vector2(-1, -1)

func grid_to_world(grid_pos: Vector2) -> Vector3:
    return Vector3(
        grid_pos.x * cell_size,
        board_thickness/2,
        grid_pos.y * cell_size
    )
