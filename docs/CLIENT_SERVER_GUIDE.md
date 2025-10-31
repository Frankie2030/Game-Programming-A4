# Client-Server Architecture Guide

## System Overview
```
[Game Clients] ←→ [FastAPI Server + WebSocket] ←→ [Game Logic + AI]
     ↑                      ↑                          ↑
     |                      |                          |
     └──────────────────────┴──────────────[Redis for game state]
```

## Deployment Setup

### Server (Port 8000)
- FastAPI server handling both HTTP and WebSocket
- Game state management
- AI processing for single-player
- Player session management

### Client (Godot)
- Connects to server via WebSocket
- Local game rendering
- Input handling
- State synchronization

## Network Flow

### 1. Single Player Mode
```
[Client] → [Server]
   ↑          ↓
   └──← [AI Module]
```
- Client connects to server
- Server creates AI instance
- Client moves are processed locally and validated by server
- AI moves are computed server-side
- Both players' moves are synchronized back to client

### 2. Multiplayer Mode
```
[Client A] →→ [Server] →→ [Client B]
    ↑           ↓            ↑
    └─────State Sync────────┘
```
- Both clients connect to server
- Server matches players or uses room code
- Moves are validated and broadcast to both clients
- Game state is synchronized in real-time

## Deployment Instructions

1. Server Deployment:
```bash
# Build and start the server
docker-compose up --build -d

# Server will run on port 8000
# WebSocket endpoint: ws://server-ip:8000/ws
# HTTP endpoint: http://server-ip:8000
```

2. Client Configuration:
```
1. Open Godot project
2. Set server address in Network Settings:
   - Local: ws://localhost:8000/ws
   - Network: ws://server-ip:8000/ws
```

## Connection Flow

### Starting a Game

1. Single Player:
```
Client                    Server
  |                         |
  |--Start Single Player-->|
  |                        |--Create AI Instance
  |<--Game Session ID-----|
  |                        |
  |--Make Move----------->|
  |                        |--Validate Move
  |<--Move Confirmed------|
  |                        |--AI Computes Move
  |<--AI Move-------------|
```

2. Multiplayer:
```
Client A   Server    Client B
  |          |          |
  |--Host-->|          |
  |<--ID----|          |
  |          |<--Join--|
  |          |--OK---->|
  |<--Start--|--Start->|
  |          |          |
```

## Configuration Files

1. Server Environment (.env):
```
PORT=8000
HOST=0.0.0.0
AI_THINKING_TIME=2
MAX_GAMES=100
```

2. Client Settings (settings.cfg):
```
[Network]
server_url="ws://server-ip:8000/ws"
reconnect_attempts=3
update_rate=60
```

## Local Testing Setup

1. Start Server:
```bash
# In A4/backend directory
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Run Client:
```bash
# Open Godot project in A4/client
# Click "Play" in editor
# For multiple clients, use "Export" and run multiple instances
```

## Game Modes

### Single Player
1. Start game client
2. Select "Single Player"
3. Choose AI difficulty
4. Game connects to server automatically
5. Server handles AI moves

### Multiplayer
1. First player:
   - Start game client
   - Select "Host Game"
   - Get room code

2. Second player:
   - Start game client
   - Select "Join Game"
   - Enter room code

## Network Protocol

### WebSocket Messages

1. Game Start:
```json
{
  "type": "start_game",
  "mode": "single_player|multiplayer",
  "difficulty": "easy|medium|hard"  // for AI games
}
```

2. Move:
```json
{
  "type": "move",
  "position": {"x": 0, "y": 0},
  "player": "black|white"
}
```

3. Game State:
```json
{
  "type": "state_update",
  "board": [[0,0,0], ...],
  "current_player": "black|white",
  "last_move": {"x": 0, "y": 0}
}
```

## Error Handling

1. Connection Loss:
- Client attempts reconnection
- Game state preserved in Redis
- Resume from last valid state

2. Invalid Moves:
- Server validates all moves
- Rejected moves are returned with error
- Client state is rolled back

## Performance Considerations

1. Latency:
- WebSocket for real-time updates
- Move validation under 100ms
- State updates at 60Hz

2. Server Load:
- Single AI instance per game
- Game state cached in Redis
- Resource cleanup for ended games
