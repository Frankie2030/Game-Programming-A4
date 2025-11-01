class_name Move
extends RefCounted

var x:int
var y:int
var z:int
var player:int

func _init(_x:int, _y:int, _z:int, _player:int):
    x = _x; y = _y; z = _z; player = _player