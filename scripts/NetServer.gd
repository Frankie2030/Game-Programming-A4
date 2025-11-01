extends Node

@export var port:int = 7777
@export var max_clients:int = 8

var peer := ENetMultiplayerPeer.new()
var players := {} # peer_id -> {color:int}
var game_state := {
    "size": 10,
    "turn": 1, # 1 black, 2 white
    "grid": [] # filled after start
}

const RPC_JOIN = "srv_register"
const RPC_START = "cli_game_start"
const RPC_MOVE = "srv_move"
const RPC_UPDATE = "cli_move_update"
const RPC_CHAT = "srv_chat"
const RPC_CHAT_BROADCAST = "cli_chat"

func _ready():
    peer.create_server(port, max_clients)
    multiplayer.multiplayer_peer = peer
    multiplayer.peer_connected.connect(_on_peer_connected)
    multiplayer.peer_disconnected.connect(_on_peer_disconnected)
    _reset_state()
    print("Server listening on ", port)

func _reset_state():
    game_state.size = 10
    game_state.turn = 1
    game_state.grid = []
    game_state.grid.resize(game_state.size)
    for z in game_state.size:
        game_state.grid[z] = []
        game_state.grid[z].resize(game_state.size)
        for y in game_state.size:
            game_state.grid[z][y] = PackedInt32Array()
            game_state.grid[z][y].resize(game_state.size)

func _on_peer_connected(id:int):
    players[id] = {"color": (players.size()%2)+1}
    rpc_id(id, RPC_START, game_state.size, players[id].color)

func _on_peer_disconnected(id:int):
    players.erase(id)

@rpc(any_peer)
func srv_register(name:String):
    # optional metadata
    pass

@rpc(any_peer)
func srv_move(x:int,y:int,z:int):
    var pid := multiplayer.get_remote_sender_id()
    var color := players.get(pid,{"color":0}).color
    if color == 0: return
    if game_state.turn != color: return
    if x<0 or y<0 or z<0 or x>=game_state.size or y>=game_state.size or z>=game_state.size: return
    if game_state.grid[z][y][x] != 0: return
    game_state.grid[z][y][x] = color
    game_state.turn = (color==1)?2:1
    rpc(RPC_UPDATE, x,y,z,color, game_state.turn)

@rpc(any_peer)
func srv_chat(msg:String):
    var pid := multiplayer.get_remote_sender_id()
    rpc(RPC_CHAT_BROADCAST, pid, msg)