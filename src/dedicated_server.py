"""
Dedicated Server Implementation for Gomoku
Handles multiple players and game rooms properly with improved stability.
"""

import socket
import threading
import json
import time
import select
import uuid
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ServerMessageType(Enum):
    """Server message types"""
    PLAYER_JOIN = "player_join"
    PLAYER_LEAVE = "player_leave"
    ROOM_CREATE = "room_create"
    ROOM_JOIN = "room_join"
    ROOM_LEAVE = "room_leave"
    ROOM_LIST = "room_list"
    GAME_MOVE = "game_move"
    GAME_START = "game_start"
    GAME_STATE = "game_state"
    CHAT = "chat"
    PING = "ping"
    PONG = "pong"


@dataclass
class Player:
    """Player data structure"""
    client_id: str
    name: str
    socket: socket.socket
    session_token: str = ""
    room_id: Optional[str] = None
    connected_time: float = 0.0
    last_ping: float = 0.0
    disconnected_time: Optional[float] = None
    
    def __post_init__(self):
        if self.connected_time == 0.0:
            self.connected_time = time.time()
        self.last_ping = time.time()
        if not self.session_token:
            self.session_token = secrets.token_urlsafe(32)


@dataclass
class GameRoom:
    """Game room data structure"""
    room_id: str
    name: str
    host_id: str
    players: List[str]
    max_players: int = 2
    created_time: float = 0.0
    game_state: Dict[str, Any] = None
    game_paused: bool = False
    pause_reason: str = ""
    timer_state: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_time == 0.0:
            self.created_time = time.time()
        if self.game_state is None:
            self.game_state = {
                "board": [[0 for _ in range(15)] for _ in range(15)], 
                "current_player": 1, 
                "moves": []
            }
        if self.timer_state is None:
            self.timer_state = {
                "turn_start_time": None,
                "elapsed_before_pause": 0,
                "move_time_limit": 60
            }
    
    def is_full(self) -> bool:
        return len(self.players) >= self.max_players
    
    def can_join(self) -> bool:
        return not self.is_full()


class DedicatedGomokuServer:
    """
    Dedicated server for Gomoku multiplayer games.
    Uses non-blocking sockets and proper message queuing.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 12345):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.send_lock = threading.Lock()
        
        # Data structures
        self.players: Dict[str, Player] = {}  # client_id -> Player
        self.rooms: Dict[str, GameRoom] = {}  # room_id -> GameRoom
        self.client_sockets: Dict[socket.socket, str] = {}  # socket -> client_id
        
        # Threading
        self.accept_thread = None
        self.message_thread = None
        self.cleanup_thread = None
        
        # Message queues
        self.message_queue = []
        self.queue_lock = threading.Lock()
        
        # Statistics
        self.next_client_id = 1
        self.next_room_id = 1
        self.total_connections = 0
    
    def start(self) -> bool:
        """Start the dedicated server"""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.server_socket.settimeout(1.0)  # Non-blocking with timeout
            
            self.running = True
            
            # Start threads
            self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.message_thread = threading.Thread(target=self._process_messages, daemon=True)
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            
            self.accept_thread.start()
            self.message_thread.start()
            self.cleanup_thread.start()
            
            print(f"🚀 Dedicated Gomoku Server started on {self.host}:{self.port}")
            print(f"📊 Max connections: 50, Timeout: 30s")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop the server gracefully"""
        print("🛑 Stopping server...")
        self.running = False
        
        # Close all client connections
        for player in list(self.players.values()):
            try:
                player.socket.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("✅ Server stopped")
    
    def _accept_connections(self):
        """Accept new client connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_socket.settimeout(30.0)  # 30 second timeout per client
                
                # Generate unique client ID
                client_id = f"client_{self.next_client_id}_{int(time.time())}"
                self.next_client_id += 1
                self.total_connections += 1
                
                # Create player object (name will be set when they join lobby)
                player = Player(
                    client_id=client_id,
                    name=f"Player_{self.next_client_id}",
                    socket=client_socket
                )
                
                # Store player
                self.players[client_id] = player
                self.client_sockets[client_socket] = client_id
                
                print(f"👤 New connection: {client_id} from {address}")
                
                # Start handling this client
                threading.Thread(
                    target=self._handle_client,
                    args=(client_id, client_socket),
                    daemon=True
                ).start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"⚠️  Accept error: {e}")
    
    def _handle_client(self, client_id: str, client_socket: socket.socket):
        """Handle messages from a specific client"""
        buffer = b""
        
        while self.running and client_id in self.players:
            try:
                # Use select for non-blocking read
                ready = select.select([client_socket], [], [], 1.0)
                if not ready[0]:
                    continue
                
                # Receive data
                data = client_socket.recv(4096)
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line:
                        try:
                            message = json.loads(line.decode('utf-8'))
                            self._queue_message(client_id, message)
                        except json.JSONDecodeError:
                            print(f"⚠️  Invalid JSON from {client_id}")
                
            except socket.timeout:
                # Check if client is still alive
                if time.time() - self.players[client_id].last_ping > 60:
                    print(f"⏰ Client {client_id} timed out")
                    break
            except Exception as e:
                print(f"⚠️  Client {client_id} error: {e}")
                break
        
        # Client disconnected
        self._remove_client(client_id)
    
    def _queue_message(self, client_id: str, message: Dict[str, Any]):
        """Queue a message for processing"""
        with self.queue_lock:
            self.message_queue.append((client_id, message))
    
    def _process_messages(self):
        """Process queued messages"""
        while self.running:
            messages_to_process = []
            
            # Get messages from queue
            with self.queue_lock:
                messages_to_process = self.message_queue.copy()
                self.message_queue.clear()
            
            # Process each message
            for client_id, message in messages_to_process:
                try:
                    self._handle_message(client_id, message)
                except Exception as e:
                    print(f"⚠️  Message processing error: {e}")
            
            time.sleep(0.01)  # Small delay to prevent busy waiting
    
    def _handle_message(self, client_id: str, message: Dict[str, Any]):
        """Handle a specific message"""
        if client_id not in self.players:
            return
        
        msg_type = message.get("type")
        data = message.get("data", {})
        
        # Update last ping time
        self.players[client_id].last_ping = time.time()
        
        if msg_type == "ping":
            self._send_to_client(client_id, {"type": "pong", "data": {}})
        
        elif msg_type == "lobby_join":
            player_name = data.get("player_name", f"Player_{client_id}")
            session_token = data.get("session_token", None)

            # ===== GRACEFUL TERMINATION: No reconnection logic =====
            # With graceful termination, disconnects immediately end the game
            # So we don't need reconnection handling here
            
            # Normal lobby join (new player)
            self.players[client_id].name = player_name
            print(f"🎮 {player_name} ({client_id}) joined lobby")

            self._send_to_client(client_id, {
                "type": "lobby_joined",
                "data": {
                    "client_id": client_id, 
                    "name": player_name,
                    "session_token": self.players[client_id].session_token
                }
            })
            self._send_room_list(client_id)
        
        elif msg_type == "room_create":
            room_name = data.get("room_name", f"Room {self.next_room_id}")
            room_id = f"room_{self.next_room_id}"
            self.next_room_id += 1
            
            # Create room
            room = GameRoom(
                room_id=room_id,
                name=room_name,
                host_id=client_id,
                players=[client_id]
            )
            
            self.rooms[room_id] = room
            self.players[client_id].room_id = room_id
            
            print(f"🏠 Room created: {room_name} ({room_id}) by {self.players[client_id].name}")
            
            # Notify creator with room info
            player_name = self.players[client_id].name
            self._send_to_client(client_id, {
                "type": "room_info",
                "data": {
                    "success": True,
                    "room_info": {
                        "room_id": room_id,
                        "name": room_name,
                        "host_name": player_name,
                        "players": 1,
                        "max_players": 2
                    }
                }
            })
            
            # Broadcast updated room list
            self._broadcast_room_list()
        
        elif msg_type == "room_join":
            room_id = data.get("room_id")
            if room_id in self.rooms and self.rooms[room_id].can_join():
                room = self.rooms[room_id]
                room.players.append(client_id)
                self.players[client_id].room_id = room_id
                
                player_name = self.players[client_id].name
                print(f"🚪 {player_name} joined room {room.name}")
                
                # Notify joiner with room info
                host_name = self.players[room.host_id].name if room.host_id in self.players else "Unknown"
                self._send_to_client(client_id, {
                    "type": "room_info",
                    "data": {
                        "success": True,
                        "room_info": {
                            "room_id": room_id,
                            "name": room.name,
                            "host_name": host_name,
                            "players": len(room.players),
                            "max_players": room.max_players
                        }
                    }
                })
                
                # Notify all players in room with updated room info
                for other_client_id in room.players:
                    if other_client_id != client_id:
                        # Send updated room info to existing players
                        self._send_to_client(other_client_id, {
                            "type": "room_info",
                            "data": {
                                "success": True,
                                "room_info": {
                                    "room_id": room_id,
                                    "name": room.name,
                                    "host_name": host_name,
                                    "players": len(room.players),
                                    "max_players": room.max_players
                                }
                            }
                        })
                
                # Start game if room is full
                if room.is_full():
                    self._start_game(room_id)
                
                # Broadcast updated room list
                self._broadcast_room_list()
        
        elif msg_type == "room_leave":
            self._leave_room(client_id)
        
        elif msg_type == "game_move":
            self._handle_game_move(client_id, data)
        
        elif msg_type == "room_list":
            self._send_room_list(client_id)
        
        elif msg_type == "new_game_request":
            self._handle_new_game_request(client_id, data)
        
        elif msg_type == "new_game_response":
            self._handle_new_game_response(client_id, data)
            
        # --- NEW ADDITION ---
        elif msg_type in ["player_pause", "player_resume"]:
            player = self.players.get(client_id)
            if not player or not player.room_id:
                return
            room_id = player.room_id
            if room_id not in self.rooms:
                return

            # Relay pause/resume to all other players in the room
            forward_message = {
                "type": msg_type,
                "data": data
            }
            self._broadcast_to_room(room_id, forward_message, exclude_client=client_id)
            print(f"🔄 Forwarded {msg_type} from {player.name} to room {room_id}")
        # --- HANDLE PLAYER RESIGN ---
        elif msg_type == "player_resign":
            resigned_player = data.get("player", "Unknown")
            player = self.players.get(client_id)
            if not player or not player.room_id:
                return
            room_id = player.room_id
            if room_id not in self.rooms:
                return
            room = self.rooms[room_id]
            print(f"🏳️ {resigned_player} resigned in room {room_id}")

            # Notify all
            for other_id in room.players:
                if other_id == client_id:
                    self._send_to_client(other_id, {
                        "type": "resign_ack",
                        "data": {"message": f"You ({resigned_player}) resigned."}
                    })
                else:
                    self._send_to_client(other_id, {
                        "type": "player_resign",
                        "data": {"player": resigned_player}
                    })
    
    def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        if client_id not in self.players:
            return False
        try:
            player = self.players[client_id]
            if not player.socket:
                return False
            message_json = json.dumps(message) + "\n"
            with self.send_lock:
                player.socket.send(message_json.encode('utf-8'))
            return True
        except Exception as e:
            print(f"⚠️ Send error to {client_id}: {e}")
            self._remove_client(client_id)
            return False
        
    def _find_disconnected_player_by_name(self, player_name: str) -> Optional[Player]:
        """Find a temporarily disconnected player by name"""
        for p in self.players.values():
            if p.name == player_name and p.socket is None and hasattr(p, "disconnected_time"):
                # Optional: expire old disconnected sessions after 2 minutes
                if time.time() - getattr(p, "disconnected_time", 0) < 120:
                    return p
        return None

    def _broadcast_to_room(self, room_id: str, message: Dict[str, Any], exclude_client: str = None):
        """Broadcast message to all players in a room"""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        msg_type = message.get("type", "unknown")
        sent_count = 0
        for client_id in room.players:
            if client_id != exclude_client:
                player = self.players.get(client_id)
                if player and player.socket:
                    self._send_to_client(client_id, message)
                    sent_count += 1
                else:
                    print(f"⚠️ Cannot broadcast {msg_type} to {player.name if player else client_id} - no socket")
        
        if msg_type == "game_move":
            print(f"📡 Broadcasted {msg_type} to {sent_count}/{len(room.players)} players in room {room.name}")
    
    def _send_room_list(self, client_id: str):
        """Send current room list to client"""
        rooms_data = []
        for room in self.rooms.values():
            if room.can_join():
                host_name = self.players[room.host_id].name if room.host_id in self.players else "Unknown"
                rooms_data.append({
                    "room_id": room.room_id,
                    "name": room.name,
                    "host_name": host_name,
                    "players": len(room.players),
                    "max_players": room.max_players
                })
        
        self._send_to_client(client_id, {
            "type": "room_list",
            "data": {"rooms": rooms_data}
        })
    
    def _broadcast_room_list(self):
        """Broadcast room list to all lobby players"""
        # Create a copy of the dictionary to avoid iteration issues during disconnection
        players_copy = dict(self.players)
        for client_id, player in players_copy.items():
            if client_id in self.players and player.room_id is None:  # Only send to players in lobby and still connected
                self._send_room_list(client_id)
    
    def _start_game(self, room_id: str):
        """Start game in a room"""
        if room_id not in self.rooms:
            return
        
        room = self.rooms[room_id]
        print(f"🎯 Starting game in room {room.name}")
        
        # Assign player roles (first player is Black, second is White)
        if len(room.players) >= 2:
            black_player_id = room.players[0]  # First player (usually room creator)
            white_player_id = room.players[1]  # Second player (joiner)
            
            black_player_name = self.players[black_player_id].name if black_player_id in self.players else "Unknown"
            white_player_name = self.players[white_player_id].name if white_player_id in self.players else "Unknown"
            
            # Send personalized game start message to each player
            # Black player (goes first)
            self._send_to_client(black_player_id, {
                "type": "game_started",
                "data": {
                    "room_id": room_id,
                    "your_role": "black",
                    "your_name": black_player_name,
                    "opponent_name": white_player_name,
                    "players": {
                        "black": black_player_name,
                        "white": white_player_name
                    },
                    "your_turn": True  # Black goes first
                }
            })
            
            # White player (goes second)
            self._send_to_client(white_player_id, {
                "type": "game_started",
                "data": {
                    "room_id": room_id,
                    "your_role": "white",
                    "your_name": white_player_name,
                    "opponent_name": black_player_name,
                    "players": {
                        "black": black_player_name,
                        "white": white_player_name
                    },
                    "your_turn": False  # White waits for Black's first move
                }
            })
            
            print(f"🎮 Game roles assigned: {black_player_name} (Black) vs {white_player_name} (White)")
    
    def _handle_game_move(self, client_id: str, data: Dict[str, Any]):
        # Must have a live player + socket
        if client_id not in self.players or not self.players[client_id].socket:
            print(f"⚠️ Ignoring move from disconnected player {client_id}")
            return

        player = self.players.get(client_id)
        if not player or not player.room_id:
            return

        room_id = player.room_id
        room = self.rooms.get(room_id)
        if not room:
            return

        row = data.get("row")
        col = data.get("col")
        player_id = data.get("player_id")

        # Ensure board and move lists exist
        if "board" not in room.game_state or not room.game_state["board"]:
            room.game_state["board"] = [[0 for _ in range(15)] for _ in range(15)]
        if "moves" not in room.game_state:
            room.game_state["moves"] = []

        # Optional board sync from client
        if data.get("board"):
            room.game_state["board"] = data["board"]
        
        # Update server's board state with the new move
        room.game_state["board"][row][col] = player_id
        
        # Debug: Count stones on board
        stone_count = sum(cell != 0 for row_data in room.game_state["board"] for cell in row_data)
        print(f"📍 Move at ({row}, {col}) by {player.name} (ID: {player_id}). Board now has {stone_count} stones")

        # Save move
        room.game_state["moves"].append({"player": player.name, "row": row, "col": col})
        room.game_state["current_player"] = 3 - room.game_state.get("current_player", 1)

        # Reset timer for the next turn
        room.timer_state = {
            "turn_start_time": time.time(),
            "elapsed_before_pause": 0,
            "move_time_limit": room.timer_state.get("move_time_limit", 30) if room.timer_state else 30
        }

        # Send timer sync to the player who made the move
        self._send_to_client(client_id, {
            "type": "timer_sync",
            "data": {
                "timer_state": room.timer_state
            }
        })

        # Broadcast move to OTHER players (excluding sender) with synchronized timer
        self._broadcast_to_room(room_id, {
            "type": "game_move",
            "data": {
                "player": player.name,
                "row": row,
                "col": col,
                "player_id": player_id,
                "timer_state": room.timer_state  # Send synchronized timer
            }
        }, exclude_client=client_id)  # Exclude sender - they already have the move!

    def _handle_new_game_request(self, client_id: str, data: Dict[str, Any]):
        """Handle new game request"""
        player = self.players.get(client_id)
        if not player or not player.room_id:
            return
        
        room_id = player.room_id
        room = self.rooms.get(room_id)
        if not room:
            return
        
        print(f"🔄 {player.name} requested new game in room {room.name}")
        
        # Forward request to other players in room
        for other_client_id in room.players:
            if other_client_id != client_id:
                self._send_to_client(other_client_id, {
                    "type": "new_game_request",
                    "data": {
                        "room_id": room_id,
                        "requester": player.name
                    }
                })
    
    def _handle_new_game_response(self, client_id: str, data: Dict[str, Any]):
        """Handle new game response"""
        player = self.players.get(client_id)
        if not player or not player.room_id:
            return
        
        room_id = player.room_id
        room = self.rooms.get(room_id)
        if not room:
            return
        
        accepted = data.get("accepted", False)
        print(f"🔄 {player.name} {'accepted' if accepted else 'declined'} new game in room {room.name}")
        
        if accepted:
            # Reset room game state
            room.game_state = {
                "board": [[0 for _ in range(15)] for _ in range(15)],
                "current_player": 1,
                "moves": []
            }   
            # Notify all players that new game is starting
            self._start_game(room_id)
        else:
            # Notify requester that new game was declined
            for other_client_id in room.players:
                if other_client_id != client_id:
                    self._send_to_client(other_client_id, {
                        "type": "new_game_response",
                        "data": {
                            "room_id": room_id,
                            "accepted": False,
                            "message": f"{player.name} declined the new game"
                        }
                    })
    
    def _leave_room(self, client_id: str):
        """Remove player from their current room"""
        player = self.players.get(client_id)
        if not player or not player.room_id:
            return
        
        room_id = player.room_id
        room = self.rooms.get(room_id)
        if not room:
            return
        
        # Remove player from room
        if client_id in room.players:
            room.players.remove(client_id)
        
        player.room_id = None
        
        player_name = player.name
        print(f"🚪 {player_name} left room {room.name}")
        
        # Notify other players
        self._broadcast_to_room(room_id, {
            "type": "player_left_room",
            "data": {"player_name": player_name}
        })
        
        # Handle room management when players leave
        if not room.players:
            # Room is empty, remove it
            print(f"🗑️  Removing empty room {room.name}")
            del self.rooms[room_id]
        elif client_id == room.host_id and len(room.players) > 0:
            # Host left but there are other players - transfer host to first remaining player
            new_host_id = room.players[0]
            room.host_id = new_host_id
            new_host_name = self.players[new_host_id].name if new_host_id in self.players else "Unknown"
            
            print(f"👑 Host transferred in room {room.name}: {new_host_name} is now the host")
            
            # Notify all players in room about host change
            for remaining_client_id in room.players:
                if remaining_client_id in self.players:
                    self._send_to_client(remaining_client_id, {
                        "type": "room_info",
                        "data": {
                            "success": True,
                            "room_info": {
                                "room_id": room_id,
                                "name": room.name,
                                "host_name": new_host_name,
                                "players": len(room.players),
                                "max_players": room.max_players
                            },
                            "message": f"You are now the host!" if remaining_client_id == new_host_id else f"{new_host_name} is now the host"
                        }
                    })
        
        # Send updated room list
        self._send_room_list(client_id)
        self._broadcast_room_list()
    
    def _remove_client(self, client_id: str, *, force: bool = False):
        """Remove or temporarily disconnect a client"""
        if client_id not in self.players:
            return

        player = self.players[client_id]
        if not force and getattr(player, "socket", None) is None:
            return  # Already marked as disconnected

        # Close socket and mark as disconnected
        if player.socket:
            try:
                if player.socket in self.client_sockets:
                    self.client_sockets.pop(player.socket, None)
                player.socket.close()
            except:
                pass

        player.socket = None
        player.last_ping = time.time()
        player.disconnected_time = time.time()

        # ===== GRACEFUL TERMINATION: Immediate forfeit on disconnect =====
        # When a player disconnects, immediately end the game and declare the other player as winner
        room_id = player.room_id
        if room_id and room_id in self.rooms:
            room = self.rooms[room_id]
            if client_id in room.players:
                room.players.remove(client_id)
            
            # Check if room is now empty
            if not room.players:
                print(f"🗑️ Removing empty room {room.name}")
                del self.rooms[room_id]
            else:
                # Notify remaining players that game ended due to disconnect (immediate forfeit)
                # Find the winner (the player who didn't disconnect)
                winner_id = None
                winner_name = "Unknown"
                for pid in room.players:
                    if pid != client_id and pid in self.players:
                        winner_id = pid
                        winner_name = self.players[pid].name
                        break
                
                self._broadcast_to_room(room_id, {
                    "type": "game_ended_disconnect",
                    "data": {
                        "reason": "opponent_disconnected",
                        "disconnected_player": player.name,
                        "winner": winner_name,
                        "message": f"{player.name} has disconnected. {winner_name} wins by forfeit!",
                        "forfeit": True,
                        "no_rematch": True  # Don't show rematch button
                    }
                })
                
                # Always update room info after a player leaves (player count changed)
                # Transfer host if the disconnected player was the host
                if client_id == room.host_id:
                    new_host_id = room.players[0]
                    room.host_id = new_host_id
                    new_host_name = self.players.get(new_host_id, Player(new_host_id, "Unknown", None)).name
                    host_message = "You are now the host!"
                else:
                    # Host didn't change, but we still need to send updated player count
                    new_host_id = room.host_id
                    new_host_name = self.players.get(new_host_id, Player(new_host_id, "Unknown", None)).name
                    host_message = f"Opponent disconnected. You are the host."
                
                # Send updated room info to all remaining players
                for rid in room.players:
                    if rid in self.players:
                        self._send_to_client(rid, {
                            "type": "room_info",
                            "data": {
                                "success": True,
                                "room_info": {
                                    "room_id": room.room_id,
                                    "name": room.name,
                                    "host_name": new_host_name,
                                    "players": len(room.players),
                                    "max_players": room.max_players
                                },
                                "message": host_message if rid == new_host_id else f"{new_host_name} is the host"
                            }
                        })
            
            player.room_id = None

        # Remove from players dictionary
        del self.players[client_id]
        print(f"👋 {player.name} ({client_id}) permanently disconnected")
    
    def _cleanup_loop(self):
        """Periodic cleanup of disconnected players and timed-out sessions"""
        while self.running:
            current_time = time.time()
            clients_to_remove = []

            for client_id, player in list(self.players.items()):
                # With graceful termination, we don't need reconnection window
                # Just handle connected players with ping timeout (90 seconds)
                if player.socket and current_time - player.last_ping > 90:
                    print(f"⏰ Ping timeout: Disconnecting {player.name}")
                    clients_to_remove.append(client_id)

            # Remove timed-out clients
            for cid in clients_to_remove:
                self._remove_client(cid, force=True)

            time.sleep(30)  # Check every 30 seconds
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            "active_players": len(self.players),
            "active_rooms": len(self.rooms),
            "total_connections": self.total_connections,
            "uptime": time.time() - (self.total_connections and self.players and min(p.connected_time for p in self.players.values()) or time.time())
        }
    
    def print_stats(self):
        """Print current server statistics"""
        stats = self.get_stats()
        print(f"📊 Server Stats: {stats['active_players']} players, {stats['active_rooms']} rooms, {stats['total_connections']} total connections")


def main():
    """Run the dedicated server"""
    server = DedicatedGomokuServer()
    
    try:
        if server.start():
            print("✅ Server running. Press Ctrl+C to stop.")
            
            # Main loop
            while server.running:
                time.sleep(5)
                server.print_stats()
                
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested...")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
