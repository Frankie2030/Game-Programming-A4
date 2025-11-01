extends Node

enum Mode { LOCAL, SINGLE_AI, CLIENT, SERVER }

@export var mode:Mode = Mode.LOCAL
@export var size:int = 10

@onready var board:Node = $World/Board
@onready var mode_label:Label = $UI/HBox/ModeLabel
@onready var turn_label:Label = $UI/HBox/TurnLabel
@onready var status_label:Label = $UI/HBox/StatusLabel

var turn:int = 1 # 1 black, 2 white
var winner:int = 0

var net_server:Node
var net_client:Node
var ai:Node

func _ready():
    Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
    board.size = size
    board.clear_board()
    board.cell_clicked.connect(_on_cell_clicked)
    ai = load("res://scripts/AI.gd").new()
    ai.board = board
    _update_ui()

func set_mode_local():
    mode = Mode.LOCAL
    mode_label.text = "Mode: Local"
    restart()

func set_mode_single_ai():
    mode = Mode.SINGLE_AI
    mode_label.text = "Mode: Single (AI as White)"
    restart()

func set_mode_server(port:int=7777):
    mode = Mode.SERVER
    mode_label.text = "Mode: Server"
    if net_server: net_server.queue_free()
    net_server = load("res://scripts/NetServer.gd").new()
    add_child(net_server)
    restart()

func set_mode_client(ip:String="127.0.0.1", port:int=7777):
    mode = Mode.CLIENT
    mode_label.text = "Mode: Client"
    if net_client: net_client.queue_free()
    net_client = load("res://scripts/NetClient.gd").new()
    add_child(net_client)
    net_client.board = board
    net_client.on_move = Callable(self, "_on_net_move")
    net_client.server_ip = ip
    net_client.port = port
    net_client.connect_now()
    status_label.text = "Connecting to %s:%d" % [ip, port]

func restart():
    winner = 0
    turn = 1
    board.size = size
    board.clear_board()
    _update_ui()

func _on_cell_clicked(x:int,y:int,z:int)->void:
    if winner != 0: return
    match mode:
        Mode.LOCAL:
            _apply_local_move(x,y,z)
        Mode.SINGLE_AI:
            if turn == 1:
                if _apply_local_move(x,y,z):
                    await get_tree().create_timer(0.1).timeout
                    var mv := ai.choose_move(2)
                    _apply_local_move(mv.x, mv.y, mv.z)
        Mode.CLIENT:
            if net_client and net_client.my_color == turn:
                net_client.try_move(x,y,z)
        Mode.SERVER:
            # server scene is headless; ignore clicks
            pass

func _apply_local_move(x:int,y:int,z:int)->bool:
    if not board.place_stone(x,y,z,turn): return false
    if board.check_win_from(x,y,z,turn):
        winner = turn
        status_label.text = (winner==1?"Black":"White") + " wins!"
    turn = (turn==1)?2:1
    _update_ui()
    return true

func _on_net_move(x:int,y:int,z:int,color:int,next_turn:int):
    board.place_stone(x,y,z,color)
    if board.check_win_from(x,y,z,color):
        winner = color
        status_label.text = (winner==1?"Black":"White") + " wins! (Online)"
    turn = next_turn
    _update_ui()

func _update_ui():
    turn_label.text = "Turn: " + (turn==1?"Black":"White")
    if winner==0:
        status_label.text = "Playing size %d" % size