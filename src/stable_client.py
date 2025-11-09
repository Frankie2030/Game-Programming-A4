"""
Stable Client Implementation for Gomoku
Works with the dedicated server using line-based JSON protocol.
"""

import socket
import threading
import json
import time
from typing import Dict, Any, Optional, Callable


class StableGomokuClient:
    """
    Stable client for connecting to Gomoku dedicated server.
    Uses line-based JSON protocol for reliability.
    """
    
    def __init__(self):
        self.socket = None
        self.connected = False
        self.running = False
        
        # Connection info for reconnection
        self.last_host = ""
        self.last_port = 0
        
        # Player info
        self.client_id = None
        self.player_name = ""
        self.current_room_id = None
        self.session_token = None
        
        # Message handlers
        self.message_handlers = {}
        self.connection_callbacks = {}
        
        # Threading
        self.receive_thread = None
        self.ping_thread = None
        self.reconnect_thread = None
        
        # Buffer for incoming data
        self.receive_buffer = b""
        
        # Reconnection state
        self.is_reconnecting = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 12  # 12 attempts * 5 seconds = 60 seconds
    
    def set_message_handler(self, message_type: str, handler: Callable):
        """Set handler for specific message type"""
        self.message_handlers[message_type] = handler
    
    def set_connection_callback(self, event: str, callback: Callable):
        """Set callback for connection events"""
        self.connection_callbacks[event] = callback
    
    def connect(self, host: str = "localhost", port: int = 12345) -> bool:
        """Connect to the dedicated server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10.0)
            self.socket.connect((host, port))
            
            # Store connection info for reconnection
            self.last_host = host
            self.last_port = port
            
            self.connected = True
            self.running = True
            self.is_reconnecting = False
            self.reconnect_attempts = 0
            
            # Start threads
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.ping_thread = threading.Thread(target=self._ping_loop, daemon=True)
            
            self.receive_thread.start()
            self.ping_thread.start()
            
            print(f"✅ Connected to server {host}:{port}")
            
            # Notify connection
            if "connect" in self.connection_callbacks:
                self.connection_callbacks["connect"]()
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            if "error" in self.connection_callbacks:
                self.connection_callbacks["error"](str(e))
            return False
    
    def disconnect(self):
        """Disconnect from server"""
        # Only stop the client if not reconnecting
        if not self.is_reconnecting:
            self.running = False
        
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print("👋 Disconnected from server")
        
        # Only notify disconnect if not in reconnection process
        if not self.is_reconnecting and "disconnect" in self.connection_callbacks:
            self.connection_callbacks["disconnect"]()
    
    def send_message(self, message_type: str, data: Dict[str, Any] = None) -> bool:
        """Send message to server"""
        if not self.connected or not self.socket:
            return False
        
        try:
            message = {
                "type": message_type,
                "data": data or {},
                "timestamp": time.time()
            }
            
            message_json = json.dumps(message) + "\n"
            self.socket.send(message_json.encode('utf-8'))
            return True
            
        except Exception as e:
            print(f"⚠️  Send error: {e}")
            self.disconnect()
            return False
    
    def join_lobby(self, player_name: str) -> bool:
        """Join the lobby with player name"""
        self.player_name = player_name
        return self.send_message("lobby_join", {
            "player_name": player_name,
            "session_token": self.session_token
        })
    
    def create_room(self, room_name: str) -> bool:
        """Create a new room"""
        return self.send_message("room_create", {"room_name": room_name})
    
    def join_room(self, room_id: str) -> bool:
        """Join an existing room"""
        return self.send_message("room_join", {"room_id": room_id})
    
    def leave_room(self) -> bool:
        """Leave current room"""
        return self.send_message("room_leave", {})
    
    def get_rooms(self) -> bool:
        """Request room list"""
        return self.send_message("room_list", {})
    
    def send_game_move(self, row: int, col: int, player_id: int) -> bool:
        """Send game move"""
        return self.send_message("game_move", {
            "row": row,
            "col": col,
            "player_id": player_id
        })
    
    def _receive_loop(self):
        """Main receive loop"""
        while self.running and self.connected:
            try:
                # Receive data
                data = self.socket.recv(4096)
                if not data:
                    break
                
                self.receive_buffer += data
                
                # Process complete messages (line-based)
                while b'\n' in self.receive_buffer:
                    line, self.receive_buffer = self.receive_buffer.split(b'\n', 1)
                    if line:
                        try:
                            message = json.loads(line.decode('utf-8'))
                            self._handle_message(message)
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON decode error: {e}")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.connected:
                    print(f"⚠️  Receive error: {e}")
                break
        
        # Connection lost - attempt reconnection if we were in a game
        print(f"🔧 DEBUG: Receive loop exited - connected={self.connected}, is_reconnecting={self.is_reconnecting}, current_room_id={self.current_room_id}")
        if self.connected and not self.is_reconnecting:
            # Only attempt reconnection if we were in a room/game
            if self.current_room_id:
                print("🔌 Connection lost during game - attempting to reconnect...")
                self._attempt_reconnection()
            else:
                print("🔌 Connection lost (not in game)")
                self.disconnect()
        else:
            print(f"🔧 DEBUG: Skipping reconnection logic - connected={self.connected}, is_reconnecting={self.is_reconnecting}")
    
    def _handle_message(self, message: Dict[str, Any]):
        """Handle received message"""
        try:
            msg_type = message.get("type")
            data = message.get("data", {})
            
            # Handle built-in messages
            if msg_type == "pong":
                return
            elif msg_type == "lobby_joined":
                self.client_id = data.get("client_id")
                self.session_token = data.get("session_token")  # Store session token
                print(f"🎮 Joined lobby as {self.player_name} ({self.client_id})")
                print(f"🔑 Session token: {self.session_token[:16]}...")
            elif msg_type == "room_created":
                self.current_room_id = data.get("room_id")
                print(f"🏠 Created room: {data.get('room_name')} ({self.current_room_id})")
            elif msg_type == "room_joined":
                self.current_room_id = data.get("room_id")
                print(f"🚪 Joined room: {data.get('room_name')} ({self.current_room_id})")
            elif msg_type == "room_closed":
                self.current_room_id = None
                print(f"🚪 Room closed: {data.get('reason', 'Unknown reason')}")
            elif msg_type == "reconnect_success":
                print(f"✅ Reconnection successful! Restored to room {data.get('room_name')}")
                self.current_room_id = data.get("room_id")
                self.is_reconnecting = False
            elif msg_type == "reconnect_failed":
                print(f"❌ Reconnection failed: {data.get('message', 'Unknown reason')}")
                self.is_reconnecting = False
                self.current_room_id = None
            
            # Call registered handler
            if msg_type in self.message_handlers:
                self.message_handlers[msg_type](data)
                
        except Exception as e:
            print(f"⚠️  Message handling error: {e}")
    
    def _attempt_reconnection(self):
        """Attempt to reconnect to the server"""
        if self.is_reconnecting:
            print("🔧 DEBUG: Already reconnecting, skipping...")
            return
        
        print(f"🔧 DEBUG: Starting reconnection - running={self.running}, connected={self.connected}")
        self.is_reconnecting = True
        self.connected = False
        
        # Notify UI about connection loss
        if "connection_lost" in self.connection_callbacks:
            self.connection_callbacks["connection_lost"]()
        
        # Close old socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # Start reconnection thread
        self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self.reconnect_thread.start()
    
    def _reconnect_loop(self):
        """Reconnection loop with retry logic"""
        print(f"🔄 Starting reconnection attempts (max {self.max_reconnect_attempts})...")
        print(f"🔧 DEBUG: Reconnect loop - running={self.running}, is_reconnecting={self.is_reconnecting}")
        
        for attempt in range(1, self.max_reconnect_attempts + 1):
            if not self.is_reconnecting:
                print(f"🔧 DEBUG: Reconnection cancelled (is_reconnecting={self.is_reconnecting})")
                break
            
            if not self.running:
                print(f"🔧 DEBUG: Client stopped (running={self.running}), aborting reconnection")
                break
            
            print(f"🔄 Reconnection attempt {attempt}/{self.max_reconnect_attempts}...")
            
            # Notify UI about attempt
            if "reconnecting" in self.connection_callbacks:
                self.connection_callbacks["reconnecting"](attempt, self.max_reconnect_attempts)
            
            # Try to reconnect
            if self.connect(self.last_host, self.last_port):
                # Connection successful, now rejoin with session token
                time.sleep(0.5)  # Brief delay to let connection stabilize
                
                if self.join_lobby(self.player_name):
                    print(f"✅ Successfully reconnected as {self.player_name}")
                    
                    # Notify UI about successful reconnection
                    if "reconnect_success" in self.connection_callbacks:
                        self.connection_callbacks["reconnect_success"]()
                    
                    return
            
            # Wait before next attempt (unless it's the last one)
            if attempt < self.max_reconnect_attempts:
                time.sleep(5)
        
        # All attempts failed
        print(f"❌ Failed to reconnect after {self.max_reconnect_attempts} attempts")
        self.is_reconnecting = False
        
        # Notify UI about failure
        if "reconnect_failed" in self.connection_callbacks:
            self.connection_callbacks["reconnect_failed"]()
        
        # Final disconnect
        if "disconnect" in self.connection_callbacks:
            self.connection_callbacks["disconnect"]()
    
    def _ping_loop(self):
        """Send periodic pings"""
        while self.running and self.connected:
            time.sleep(30)  # Ping every 30 seconds
            if self.connected:
                self.send_message("ping")
    
    def is_in_room(self) -> bool:
        """Check if currently in a room"""
        return self.current_room_id is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status"""
        return {
            "connected": self.connected,
            "player_name": self.player_name,
            "client_id": self.client_id,
            "current_room": self.current_room_id
        }


# Test client functionality
def test_client():
    """Test the stable client"""
    client = StableGomokuClient()
    
    # Set up handlers
    def on_room_list(data):
        rooms = data.get("rooms", [])
        print(f"📋 Available rooms: {len(rooms)}")
        for room in rooms:
            print(f"   - {room['name']} (Host: {room['host_name']}, Players: {room['players']}/{room['max_players']})")
    
    def on_game_started(data):
        print(f"🎯 Game started! Players: {data.get('players', [])}")
    
    def on_game_move(data):
        print(f"🎲 Move: {data.get('player')} played at ({data.get('row')}, {data.get('col')})")
    
    client.set_message_handler("room_list", on_room_list)
    client.set_message_handler("game_started", on_game_started)
    client.set_message_handler("game_move", on_game_move)
    
    # Connect and test
    if client.connect():
        client.join_lobby("TestPlayer")
        time.sleep(1)
        
        client.get_rooms()
        time.sleep(1)
        
        client.create_room("Test Room")
        time.sleep(2)
        
        client.disconnect()
    
    return True


if __name__ == "__main__":
    test_client()
