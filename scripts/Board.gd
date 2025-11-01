extends Node3D

signal cell_clicked(x:int, y:int, z:int)
signal board_changed()

@export var size:int = 10
@export var line_color:Color = Color(0.15,0.15,0.15)
@export var cell_spacing:float = 1.2
@export var show_axes:bool = true

var grid:Array = [] # 3D array [z][y][x]; 0 empty, 1 black, 2 white
var stones:Array[Vector3] = []
var stone_colors:Array[int] = []

@onready var stone_pool:MultiMeshInstance3D = $StonePool

var _cursor := Vector3i(0,0,0)
var _cursor_mesh:MeshInstance3D
var _line_mesh:ImmediateMesh

func _ready():
    _build_board()
    _build_cursor()
    _rebuild_stones()

func _build_board():
    grid.resize(size)
    for z in size:
        grid[z] = []
        grid[z].resize(size)
        for y in size:
            grid[z][y] = PackedInt32Array()
            grid[z][y].resize(size)
    _line_mesh = ImmediateMesh.new()
    var mi := MeshInstance3D.new()
    mi.mesh = _line_mesh
    add_child(mi)
    _draw_lines()

func _draw_lines():
    _line_mesh.clear_surfaces()
    var mat := ORMMaterial3D.new()
    mat.albedo_color = line_color
    _line_mesh.surface_begin(Mesh.PRIMITIVE_LINES, mat)
    var s := float(size-1) * cell_spacing
    # draw outer cube
    for i in 0:12:
        pass # (cube edges optional; we draw inner grid instead)
    # inner grid per layer
    for z in size:
        var zoff := z * cell_spacing
        for i in range(size):
            var off := i * cell_spacing
            _line_mesh.surface_add_vertex(Vector3(0, off, zoff))
            _line_mesh.surface_add_vertex(Vector3((size-1)*cell_spacing, off, zoff))
            _line_mesh.surface_add_vertex(Vector3(off, 0, zoff))
            _line_mesh.surface_add_vertex(Vector3(off, (size-1)*cell_spacing, zoff))
    _line_mesh.surface_end()

func _build_cursor():
    _cursor_mesh = MeshInstance3D.new()
    var m := CylinderMesh.new()
    m.radius = 0.2
    m.height = 0.1
    _cursor_mesh.mesh = m
    var mat := StandardMaterial3D.new()
    mat.albedo_color = Color(0.2,0.7,1.0,0.6)
    mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    _cursor_mesh.material_override = mat
    add_child(_cursor_mesh)
    _update_cursor()

func _update_cursor():
    var pos := Vector3(_cursor.x, _cursor.y, _cursor.z) * cell_spacing
    _cursor_mesh.transform = Transform3D(Basis.IDENTITY, pos)

func _unhandled_input(event:InputEvent)->void:
    if event.is_action_pressed("ui_up"): _cursor.y = clampi(_cursor.y-1,0,size-1)
    elif event.is_action_pressed("ui_down"): _cursor.y = clampi(_cursor.y+1,0,size-1)
    elif event.is_action_pressed("ui_left"): _cursor.x = clampi(_cursor.x-1,0,size-1)
    elif event.is_action_pressed("ui_right"): _cursor.x = clampi(_cursor.x+1,0,size-1)
    elif event.is_action_pressed("ui_page_up"): _cursor.z = clampi(_cursor.z+1,0,size-1)
    elif event.is_action_pressed("ui_page_down"): _cursor.z = clampi(_cursor.z-1,0,size-1)
    elif event.is_action_pressed("ui_accept"):
        emit_signal("cell_clicked", _cursor.x, _cursor.y, _cursor.z)
    _update_cursor()

func clear_board():
    for z in size:
        for y in size:
            for x in size:
                grid[z][y][x] = 0
    stones.clear()
    stone_colors.clear()
    _rebuild_stones()
    emit_signal("board_changed")

func place_stone(x:int,y:int,z:int, player:int)->bool:
    if x<0 or y<0 or z<0 or x>=size or y>=size or z>=size: return false
    if grid[z][y][x] != 0: return false
    grid[z][y][x] = player
    stones.append(Vector3(x,y,z)*cell_spacing)
    stone_colors.append(player)
    _rebuild_stones()
    emit_signal("board_changed")
    return true

func _rebuild_stones():
    stone_pool.rebuild(stones.size())
    for i in stones.size():
        stone_pool.set_stone(i, stones[i], stone_colors[i]==1)

func check_win_from(x:int,y:int,z:int, player:int)->bool:
    var dirs = [
        Vector3i(1,0,0), Vector3i(0,1,0), Vector3i(0,0,1),
        Vector3i(1,1,0), Vector3i(1,-1,0), Vector3i(1,0,1), Vector3i(1,0,-1),
        Vector3i(0,1,1), Vector3i(0,1,-1), Vector3i(1,1,1), Vector3i(1,1,-1), Vector3i(1,-1,1), Vector3i(1,-1,-1)
    ]
    for d in dirs:
        var count := 1
        count += _count_dir(x,y,z, d, player)
        count += _count_dir(x,y,z, -d, player)
        if count >= 5:
            return true
    return false

func _count_dir(x:int,y:int,z:int, d:Vector3i, player:int)->int:
    var c := 0
    var nx := x + d.x
    var ny := y + d.y
    var nz := z + d.z
    while nx>=0 and ny>=0 and nz>=0 and nx<size and ny<size and nz<size and grid[nz][ny][nx]==player:
        c += 1
        nx += d.x; ny += d.y; nz += d.z
    return c