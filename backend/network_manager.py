from typing import Dict, Set, Optional
import asyncio
import json
import msgpack
import redis.asyncio as redis
from fastapi import WebSocket
from dataclasses import dataclass
import time

@dataclass
class GameSession:
    game_id: str
    players: Dict[str, WebSocket]
    spectators: Set[WebSocket]
    last_state: dict
    sequence_number: int = 0
    last_update_time: float = 0

class NetworkManager:
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.sessions: Dict[str, GameSession] = {}
        self.message_queue: Dict[str, list] = {}
        self.UPDATE_RATE = 1/60  # 60Hz update rate
        
    async def start(self):
        """Start the network manager and its background tasks"""
        asyncio.create_task(self._update_loop())
        asyncio.create_task(self._cleanup_loop())

    async def _update_loop(self):
        """Main update loop for sending game states"""
        while True:
            start_time = time.time()
            
            # Process all game sessions
            for game_id, session in self.sessions.items():
                await self._process_game_updates(session)
            
            # Maintain consistent update rate
            elapsed = time.time() - start_time
            if elapsed < self.UPDATE_RATE:
                await asyncio.sleep(self.UPDATE_RATE - elapsed)

    async def _process_game_updates(self, session: GameSession):
        """Process updates for a single game session"""
        current_time = time.time()
        
        # Only send updates if there are changes or every 1 second for keepalive
        if (self.message_queue.get(session.game_id) or 
            current_time - session.last_update_time > 1.0):
            
            # Prepare the update package
            updates = self.message_queue.get(session.game_id, [])
            state_update = {
                'seq': session.sequence_number,
                'timestamp': current_time,
                'updates': updates
            }
            
            # Compress and send to all players
            packed_data = msgpack.packb(state_update)
            for player in session.players.values():
                try:
                    await player.send_bytes(packed_data)
                except Exception:
                    # Handle disconnection in another task
                    continue
            
            # Clear processed updates
            if updates:
                self.message_queue[session.game_id] = []
            
            session.sequence_number += 1
            session.last_update_time = current_time

    async def _cleanup_loop(self):
        """Cleanup disconnected sessions and players"""
        while True:
            await asyncio.sleep(60)  # Run cleanup every minute
            for game_id in list(self.sessions.keys()):
                session = self.sessions[game_id]
                # Remove disconnected players
                session.players = {
                    pid: ws for pid, ws in session.players.items()
                    if not ws.client_state.disconnected
                }
                # Remove empty sessions
                if not session.players:
                    del self.sessions[game_id]
                    await self.redis.delete(f"game:{game_id}")

    async def register_player(self, game_id: str, player_id: str, websocket: WebSocket):
        """Register a new player to a game session"""
        if game_id not in self.sessions:
            # Create new session
            self.sessions[game_id] = GameSession(
                game_id=game_id,
                players={},
                spectators=set(),
                last_state={}
            )
            
        session = self.sessions[game_id]
        session.players[player_id] = websocket
        
        # Send initial state
        state = await self.redis.get(f"game:{game_id}")
        if state:
            await websocket.send_text(state)

    async def queue_update(self, game_id: str, update: dict):
        """Queue an update to be sent to clients"""
        if game_id not in self.message_queue:
            self.message_queue[game_id] = []
        self.message_queue[game_id].append(update)
        
        # Store state in Redis
        await self.redis.set(f"game:{game_id}", json.dumps(update))

    async def handle_client_message(self, game_id: str, player_id: str, message: dict):
        """Handle incoming client messages"""
        session = self.sessions.get(game_id)
        if not session:
            return
        
        # Validate and process the message
        if message.get('type') == 'move':
            # Validate move
            if self._validate_move(game_id, player_id, message):
                # Broadcast validated move
                await self.queue_update(game_id, {
                    'type': 'move',
                    'player': player_id,
                    'position': message['position'],
                    'timestamp': time.time()
                })

    def _validate_move(self, game_id: str, player_id: str, move: dict) -> bool:
        """Validate a player's move"""
        session = self.sessions.get(game_id)
        if not session:
            return False
            
        # Add move validation logic here
        return True  # Placeholder
