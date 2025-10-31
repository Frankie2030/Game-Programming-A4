extends Node3D

# Network client for Webfunc _process(_delta):
	if _client.get_ready_state() == STATE_CONNECTING || \
	   _client.get_ready_state() == STATE_OPEN:
		_client.poll()et communication
var _client = WebSocketPeer.new()
var game_id: String = ""
var player_id: String = ""

# WebSocket connection states
const STATE_CONNECTING = WebSocketPeer.STATE_CONNECTING
const STATE_OPEN = WebSocketPeer.STATE_OPEN

# Game state
var current_player = 1  # 1 for black, 2 for white
var board = []
var board_size = 15
var game_active = false

# 3D scene references
@onready var board_mesh = $Board
@onready var camera = $Camera3D
@onready var ui = $UI

# Preload the stone scene
var stone_scene = preload("res://scenes/stone.tscn")

func _ready():
	# Initialize empty board
	board.resize(board_size)
	for i in range(board_size):
		board[i] = []
		board[i].resize(board_size)
		for j in range(board_size):
			board[i][j] = 0
	
	# Setup WebSocket client
	_client.connect("connection_established", self._on_connection_established)
	_client.connect("connection_error", self._on_connection_error)
	_client.connect("data_received", self._on_data)
	_client.connect("connection_closed", self._on_connection_closed)

func _process(_delta):
	if _client.get_ready_state() == WebSocketPeer.STATE_CONNECTING || \
	   _client.get_ready_state() == WebSocketPeer.STATE_OPEN:
		_client.poll()

func connect_to_server(url: String):
	var err = _client.connect_to_url(url)
	if err != OK:
		print("Unable to connect to server")
		return

func _on_connection_established(_protocol):
	print("Connected to server!")
	ui.show_message("Connected to server")

func _on_connection_error():
	print("Failed to connect to server")
	ui.show_message("Connection failed")

func _on_connection_closed(_was_clean):
	print("Disconnected from server")
	ui.show_message("Disconnected from server")

func _on_data():
	var data = JSON.parse_string(_client.get_peer(1).get_packet().get_string_from_utf8())
	
	match data["type"]:
		"game_update":
			update_game_state(data["game_state"])
		"game_end":
			handle_game_end(data["winner"])
		"chat":
			ui.add_chat_message(data["player_id"], data["message"])
		"player_disconnected":
			ui.show_message("Player " + data["player_id"] + " disconnected")

func update_game_state(state):
	current_player = state["current_player"]
	
	# Update board and visual representation
	for i in range(board_size):
		for j in range(board_size):
			if board[i][j] != state["board"][i][j]:
				board[i][j] = state["board"][i][j]
				if board[i][j] != 0:
					place_stone(i, j, board[i][j])

func place_stone(row: int, col: int, player: int):
	var stone = stone_scene.instantiate()
	stone.translation = Vector3(row - board_size/2, 0, col - board_size/2)
	stone.set_material(player)  # 1 for black, 2 for white
	$Stones.add_child(stone)

func handle_game_end(winner):
	game_active = false
	match winner:
		"BLACK":
			ui.show_message("Black wins!")
		"WHITE":
			ui.show_message("White wins!")
		"DRAW":
			ui.show_message("Game ended in a draw!")

func _on_board_clicked(position: Vector3):
	if !game_active:
		return
		
	# Convert 3D position to board coordinates
	var row = int(position.x + board_size/2)
	var col = int(position.z + board_size/2)
	
	if row >= 0 && row < board_size && col >= 0 && col < board_size:
		_client.get_peer(1).put_packet(JSON.stringify({
			"type": "move",
			"row": row,
			"col": col
		}).to_utf8_buffer())

func send_chat(message: String):
	_client.get_peer(1).put_packet(JSON.stringify({
		"type": "chat",
		"message": message
	}).to_utf8_buffer())
