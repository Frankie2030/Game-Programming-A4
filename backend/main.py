from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
import asyncio
from pydantic import BaseModel
import uuid
from ..src.gomoku import GomokuGame, Player, GameState

app = FastAPI()

# Store active games and their connections
games: Dict[str, GomokuGame] = {}
connections: Dict[str, List[WebSocket]] = {}

class GameSession(BaseModel):
    game_id: str
    player_id: str
    board_size: int = 15

class Move(BaseModel):
    game_id: str
    player_id: str
    row: int
    col: int

@app.post("/create_game")
async def create_game(session: GameSession):
    game_id = str(uuid.uuid4())
    games[game_id] = GomokuGame(size=session.board_size)
    connections[game_id] = []
    return {"game_id": game_id, "player_id": session.player_id}

@app.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    await websocket.accept()
    
    if game_id not in games:
        await websocket.close(reason="Game not found")
        return

    connections[game_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            game = games[game_id]
            
            if data["type"] == "move":
                row, col = data["row"], data["col"]
                
                # Validate move
                if game.is_valid_move(row, col):
                    success = game.make_move(row, col)
                    if success:
                        # Broadcast the updated game state to all players
                        game_state = game.to_dict()
                        for conn in connections[game_id]:
                            await conn.send_json({
                                "type": "game_update",
                                "game_state": game_state
                            })
                        
                        # Check for game end
                        if game.game_state != GameState.ONGOING:
                            winner = None
                            if game.game_state == GameState.BLACK_WIN:
                                winner = "BLACK"
                            elif game.game_state == GameState.WHITE_WIN:
                                winner = "WHITE"
                            elif game.game_state == GameState.DRAW:
                                winner = "DRAW"
                            
                            for conn in connections[game_id]:
                                await conn.send_json({
                                    "type": "game_end",
                                    "winner": winner
                                })
                    
            elif data["type"] == "chat":
                # Handle chat messages
                for conn in connections[game_id]:
                    await conn.send_json({
                        "type": "chat",
                        "player_id": player_id,
                        "message": data["message"]
                    })
                    
    except WebSocketDisconnect:
        connections[game_id].remove(websocket)
        # Notify other players about disconnection
        for conn in connections[game_id]:
            await conn.send_json({
                "type": "player_disconnected",
                "player_id": player_id
            })
    finally:
        if not connections[game_id]:
            # Clean up the game if no players are connected
            del games[game_id]
            del connections[game_id]

@app.get("/game/{game_id}")
async def get_game_state(game_id: str):
    if game_id not in games:
        return {"error": "Game not found"}
    return games[game_id].to_dict()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
