extends Node

@export var server_ip:String = "127.0.0.1"
@export var port:int = 7777

var peer := ENetMultiplayerPeer.new()
var my_color:int = 1
var board:Node
var on_move:Callable # set by GameManager to update UI

const RPC_JOIN = "srv_register"
const RPC_START = "cli_game_start"
const RPC_MOVE = "srv_move"
const RPC_UPDATE = "cli_move_update"
const RPC_CHAT = "srv_chat"
const RPC_CHAT_BROADCAST = "cli_chat"

func connect_now():
    peer.create_client(server_ip, port)
    multiplayer.multiplayer_peer = peer
    rpc_id(1, RPC_JOIN, OS.get_unique_id())

@rpc(authority)
func cli_game_start(size:int, color:int):
    my_color = color
    if board:
        board.size = size
        board.clear_board()

@rpc(authority)
func cli_move_update(x:int,y:int,z:int,color:int,next_turn:int):
    if board:
        board.place_stone(x,y,z,color)
    if on_move:
        on_move.call(x,y,z,color,next_turn)

func try_move(x:int,y:int,z:int):
    rpc_id(1, RPC_MOVE, x,y,z)

func send_chat(msg:String):
    rpc_id(1, RPC_CHAT, msg)