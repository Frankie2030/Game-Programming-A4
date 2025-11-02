"""
Lobby Manager for Gomoku Multiplayer
Handles game rooms, player names, and server browser functionality.
"""

import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class GameRoomStatus(Enum):
    """Game room status enumeration"""
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


@dataclass
class PlayerInfo:
    """Player information"""
    player_id: str
    name: str
    connected_time: float
    is_ready: bool = False


@dataclass
class GameRoom:
    """Game room information"""
    room_id: str
    room_name: str
    host_player: PlayerInfo
    guest_player: Optional[PlayerInfo] = None
    status: GameRoomStatus = GameRoomStatus.WAITING
    created_time: float = 0.0
    max_players: int = 2
    is_private: bool = False
    password: str = ""
    
    def __post_init__(self):
        if self.created_time == 0.0:
            self.created_time = time.time()
    
    def is_full(self) -> bool:
        """Check if room is full"""
        return self.guest_player is not None
    
    def get_player_count(self) -> int:
        """Get current player count"""
        count = 1  # Host is always present
        if self.guest_player:
            count += 1
        return count
    
    def can_join(self) -> bool:
        """Check if room can be joined"""
        return (self.status == GameRoomStatus.WAITING and 
                not self.is_full())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for network transmission"""
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "host_name": self.host_player.name,
            "player_count": self.get_player_count(),
            "max_players": self.max_players,
            "status": self.status.value,
            "is_private": self.is_private,
            "created_time": self.created_time
        }


class LobbyManager:
    """
    Manages game lobbies, rooms, and player connections.
    """
    
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.players: Dict[str, PlayerInfo] = {}
        self.client_to_player: Dict[str, str] = {}  # client_id -> player_id
        self.player_to_room: Dict[str, str] = {}    # player_id -> room_id
        self.next_room_id = 1
    
    def add_player(self, client_id: str, player_name: str) -> PlayerInfo:
        """Add a new player to the lobby"""
        player_id = f"player_{len(self.players) + 1}_{int(time.time())}"
        
        player = PlayerInfo(
            player_id=player_id,
            name=player_name,
            connected_time=time.time()
        )
        
        self.players[player_id] = player
        self.client_to_player[client_id] = player_id
        
        print(f"Player added: {player_name} ({player_id})")
        return player
    
    def remove_player(self, client_id: str) -> bool:
        """Remove a player from the lobby"""
        if client_id not in self.client_to_player:
            return False
        
        player_id = self.client_to_player[client_id]
        player = self.players.get(player_id)
        
        if not player:
            return False
        
        # Remove from room if in one
        if player_id in self.player_to_room:
            room_id = self.player_to_room[player_id]
            self.leave_room(player_id)
        
        # Clean up
        del self.players[player_id]
        del self.client_to_player[client_id]
        
        print(f"Player removed: {player.name} ({player_id})")
        return True
    
    def create_room(self, host_client_id: str, room_name: str, 
                   is_private: bool = False, password: str = "") -> Optional[GameRoom]:
        """Create a new game room"""
        if host_client_id not in self.client_to_player:
            return None
        
        player_id = self.client_to_player[host_client_id]
        player = self.players.get(player_id)
        
        if not player:
            return None
        
        # Check if player is already in a room
        if player_id in self.player_to_room:
            return None
        
        room_id = f"room_{self.next_room_id}"
        self.next_room_id += 1
        
        room = GameRoom(
            room_id=room_id,
            room_name=room_name,
            host_player=player,
            is_private=is_private,
            password=password
        )
        
        self.rooms[room_id] = room
        self.player_to_room[player_id] = room_id
        
        print(f"Room created: {room_name} ({room_id}) by {player.name}")
        return room
    
    def join_room(self, client_id: str, room_id: str, password: str = "") -> Optional[GameRoom]:
        """Join an existing room"""
        if client_id not in self.client_to_player:
            return None
        
        player_id = self.client_to_player[client_id]
        player = self.players.get(player_id)
        room = self.rooms.get(room_id)
        
        if not player or not room:
            return None
        
        # Check if player is already in a room
        if player_id in self.player_to_room:
            return None
        
        # Check if room can be joined
        if not room.can_join():
            return None
        
        # Check password for private rooms
        if room.is_private and room.password != password:
            return None
        
        # Join the room
        room.guest_player = player
        self.player_to_room[player_id] = room_id
        
        print(f"Player {player.name} joined room {room.room_name}")
        return room
    
    def leave_room(self, player_id: str) -> bool:
        """Leave current room"""
        if player_id not in self.player_to_room:
            return False
        
        room_id = self.player_to_room[player_id]
        room = self.rooms.get(room_id)
        
        if not room:
            return False
        
        player = self.players.get(player_id)
        
        # Remove player from room
        if room.host_player.player_id == player_id:
            # Host is leaving - close the room
            if room.guest_player:
                guest_id = room.guest_player.player_id
                if guest_id in self.player_to_room:
                    del self.player_to_room[guest_id]
            
            del self.rooms[room_id]
            print(f"Room {room.room_name} closed (host left)")
        else:
            # Guest is leaving
            room.guest_player = None
            room.status = GameRoomStatus.WAITING
            print(f"Player {player.name if player else 'Unknown'} left room {room.room_name}")
        
        del self.player_to_room[player_id]
        return True
    
    def get_public_rooms(self) -> List[Dict[str, Any]]:
        """Get list of public rooms that can be joined"""
        public_rooms = []
        
        for room in self.rooms.values():
            if not room.is_private and room.can_join():
                public_rooms.append(room.to_dict())
        
        # Sort by creation time (newest first)
        public_rooms.sort(key=lambda x: x["created_time"], reverse=True)
        return public_rooms
    
    def get_player_room(self, client_id: str) -> Optional[GameRoom]:
        """Get the room a player is currently in"""
        if client_id not in self.client_to_player:
            return None
        
        player_id = self.client_to_player[client_id]
        
        if player_id not in self.player_to_room:
            return None
        
        room_id = self.player_to_room[player_id]
        return self.rooms.get(room_id)
    
    def start_game(self, room_id: str) -> bool:
        """Start a game in the specified room"""
        room = self.rooms.get(room_id)
        
        if not room or not room.is_full():
            return False
        
        room.status = GameRoomStatus.PLAYING
        print(f"Game started in room {room.room_name}")
        return True
    
    def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed room information"""
        room = self.rooms.get(room_id)
        
        if not room:
            return None
        
        info = room.to_dict()
        info["guest_name"] = room.guest_player.name if room.guest_player else None
        return info
    
    def cleanup_inactive_rooms(self, timeout_seconds: int = 300):
        """Clean up rooms that have been inactive for too long"""
        current_time = time.time()
        rooms_to_remove = []
        
        for room_id, room in self.rooms.items():
            if (current_time - room.created_time > timeout_seconds and 
                room.status == GameRoomStatus.WAITING and 
                not room.is_full()):
                rooms_to_remove.append(room_id)
        
        for room_id in rooms_to_remove:
            room = self.rooms[room_id]
            print(f"Cleaning up inactive room: {room.room_name}")
            self.leave_room(room.host_player.player_id)
    
    def get_lobby_stats(self) -> Dict[str, Any]:
        """Get lobby statistics"""
        return {
            "total_players": len(self.players),
            "total_rooms": len(self.rooms),
            "active_games": len([r for r in self.rooms.values() if r.status == GameRoomStatus.PLAYING]),
            "waiting_rooms": len([r for r in self.rooms.values() if r.status == GameRoomStatus.WAITING])
        }

