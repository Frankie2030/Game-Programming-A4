extends MultiMeshInstance3D

@export var stone_radius:float = 0.35
@export var black_color:Color = Color(0.05,0.05,0.05)
@export var white_color:Color = Color(0.95,0.95,0.95)

var _mesh_black:SphereMesh
var _mesh_white:SphereMesh

func _ready():
    _mesh_black = SphereMesh.new()
    _mesh_black.radius = stone_radius
    _mesh_white = SphereMesh.new()
    _mesh_white.radius = stone_radius
    multimesh = MultiMesh.new()
    multimesh.transform_format = MultiMesh.TRANSFORM_3D
    multimesh.color_format = MultiMesh.COLOR_8BIT
    multimesh.custom_data_format = MultiMesh.CUSTOM_DATA_NONE

func rebuild(count:int):
    multimesh.instance_count = count

func set_stone(i:int, position:Vector3, is_black:bool):
    var t := Transform3D(Basis.IDENTITY, position)
    multimesh.set_instance_transform(i, t)
    multimesh.set_instance_color(i, is_black ? black_color : white_color)
    mesh = is_black ? _mesh_black : _mesh_white