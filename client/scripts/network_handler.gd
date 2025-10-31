extends Node

signal connection_established
signal connection_failed
signal connection_closed
signal state_updated(state)
signal move_validated(success, move_data)

# Network configuration
const UPDATE_RATE = 1.0/60.0  # 60Hz update rate
const INTERPOLATION_OFFSET = 100  # ms
const MAX_BUFFER_SIZE = 120  # 2 seconds at 60Hz
const PREDICTION_THRESHOLD = 100  # ms

# Connection state
var _client = WebSocketPeer.new()
var _server_url = ""
var _game_id = ""
var _player_id = ""
var _sequence_number = 0

# Game state management
var _state_buffer = []
var _input_sequence = 0
var _last_processed_input = 0
var _pending_inputs = []
var _last_update_time = 0.0

# Interpolation/Prediction
var _interpolation_buffer = []
var _predicted_states = []

signal connection_established
signal connection_failed
signal connection_closed
signal state_updated(state)
signal move_validated(success, move_data)

func _ready():
    # Configure WebSocket
    _client.supported_protocols = ["gomoku-binary"]
    _client.inbound_buffer_size = 1024 * 64  # 64KB

func connect_to_server(url: String, game_id: String, player_id: String):
    _server_url = url
    _game_id = game_id
    _player_id = player_id
    
    var error = _client.connect_to_url(_server_url)
    if error != OK:
        emit_signal("connection_failed")
        return

func _process(delta):
    _client.poll()
    
    match _client.get_ready_state():
        WebSocketPeer.STATE_OPEN:
            while _client.get_available_packet_count():
                var packet = _client.get_packet()
                _handle_server_message(packet)
            
            # Process game state
            _process_game_state(delta)
        
        WebSocketPeer.STATE_CLOSED:
            emit_signal("connection_closed")

func _handle_server_message(packet: PackedByteArray):
    # Decode message (using JSON for example, could be optimized with binary protocol)
    var message = JSON.parse_string(packet.get_string_from_utf8())
    
    match message.type:
        "state_update":
            _handle_state_update(message)
        "move_validation":
            _handle_move_validation(message)

func _handle_state_update(update):
    # Add to interpolation buffer
    _interpolation_buffer.append({
        "timestamp": Time.get_ticks_msec(),
        "state": update.state
    })
    
    # Keep buffer size in check
    while _interpolation_buffer.size() > MAX_BUFFER_SIZE:
        _interpolation_buffer.pop_front()
    
    # Validate predictions
    _reconcile_predictions(update)

func _handle_move_validation(validation):
    var move_id = validation.move_id
    
    # Remove confirmed inputs
    _pending_inputs = _pending_inputs.filter(func(input): return input.id > move_id)
    
    emit_signal("move_validated", validation.success, validation.move_data)

func _process_game_state(delta):
    var current_time = Time.get_ticks_msec()
    
    # Process interpolation
    if _interpolation_buffer.size() >= 2:
        var render_timestamp = current_time - INTERPOLATION_OFFSET
        var states = _find_states_for_timestamp(render_timestamp)
        
        if states.size() == 2:
            var interpolated_state = _interpolate_states(states[0], states[1], render_timestamp)
            emit_signal("state_updated", interpolated_state)

func _find_states_for_timestamp(timestamp: int) -> Array:
    var result = []
    
    for i in range(_interpolation_buffer.size() - 1):
        var state1 = _interpolation_buffer[i]
        var state2 = _interpolation_buffer[i + 1]
        
        if state1.timestamp <= timestamp and state2.timestamp >= timestamp:
            result = [state1, state2]
            break
    
    return result

func _interpolate_states(state1: Dictionary, state2: Dictionary, timestamp: int) -> Dictionary:
    var alpha = float(timestamp - state1.timestamp) / (state2.timestamp - state1.timestamp)
    
    # Interpolate relevant state properties
    # This needs to be customized based on your game state structure
    var interpolated = {}
    
    # Example: Interpolate piece positions
    for piece_id in state1.state.pieces.keys():
        if piece_id in state2.state.pieces:
            var pos1 = state1.state.pieces[piece_id].position
            var pos2 = state2.state.pieces[piece_id].position
            interpolated[piece_id] = {
                "position": lerp(pos1, pos2, alpha)
            }
    
    return interpolated

func send_move(move_data: Dictionary):
    var input = {
        "id": _input_sequence,
        "type": "move",
        "game_id": _game_id,
        "player_id": _player_id,
        "data": move_data,
        "timestamp": Time.get_ticks_msec()
    }
    
    # Add to pending inputs
    _pending_inputs.append(input)
    _input_sequence += 1
    
    # Send to server
    _client.send_text(JSON.stringify(input))
    
    # Predict result immediately
    _predict_move_result(input)

func _predict_move_result(input: Dictionary):
    # Add prediction logic here
    # This should match the server's expected behavior
    var predicted_state = _create_predicted_state(input)
    _predicted_states.append({
        "input_sequence": input.id,
        "state": predicted_state
    })

func _reconcile_predictions(server_state):
    # Remove old predictions
    _predicted_states = _predicted_states.filter(
        func(pred): return pred.input_sequence > server_state.last_processed_input
    )
    
    # Re-apply remaining predictions
    var current_state = server_state.state
    for prediction in _predicted_states:
        current_state = _apply_prediction(current_state, prediction)
    
    return current_state

func _apply_prediction(base_state: Dictionary, prediction: Dictionary) -> Dictionary:
    # Apply prediction logic here
    # This should match the server's state update logic
    var new_state = base_state.duplicate(true)
    # Apply the predicted changes
    return new_state
