import pytest
from fastapi.testclient import TestClient
from ..backend.main import app
import json

client = TestClient(app)

def test_create_game():
    response = client.post(
        "/create_game",
        json={"player_id": "player1", "board_size": 15}
    )
    assert response.status_code == 200
    data = response.json()
    assert "game_id" in data
    assert "player_id" in data
    assert data["player_id"] == "player1"

def test_get_game_state():
    # First create a game
    create_response = client.post(
        "/create_game",
        json={"player_id": "player1", "board_size": 15}
    )
    game_id = create_response.json()["game_id"]
    
    # Then get its state
    response = client.get(f"/game/{game_id}")
    assert response.status_code == 200
    data = response.json()
    assert "board" in data
    assert "current_player" in data
    assert "game_state" in data
    
def test_get_nonexistent_game():
    response = client.get("/game/nonexistent")
    assert response.status_code == 200  # API returns 200 with error message
    assert "error" in response.json()
    assert response.json()["error"] == "Game not found"

@pytest.mark.asyncio
async def test_websocket_connection():
    game_response = client.post(
        "/create_game",
        json={"player_id": "player1", "board_size": 15}
    )
    game_id = game_response.json()["game_id"]
    
    with client.websocket_connect(f"/ws/{game_id}/player1") as websocket:
        # Test move
        websocket.send_json({
            "type": "move",
            "row": 7,
            "col": 7
        })
        
        data = websocket.receive_json()
        assert data["type"] == "game_update"
        assert "game_state" in data
        
        # Test chat
        websocket.send_json({
            "type": "chat",
            "message": "Hello!"
        })
        
        data = websocket.receive_json()
        assert data["type"] == "chat"
        assert data["message"] == "Hello!"
        assert data["player_id"] == "player1"

@pytest.mark.asyncio
async def test_invalid_moves():
    game_response = client.post(
        "/create_game",
        json={"player_id": "player1", "board_size": 15}
    )
    game_id = game_response.json()["game_id"]
    
    with client.websocket_connect(f"/ws/{game_id}/player1") as websocket:
        # Try to place at same position twice
        websocket.send_json({
            "type": "move",
            "row": 7,
            "col": 7
        })
        
        data = websocket.receive_json()
        assert data["type"] == "game_update"
        
        websocket.send_json({
            "type": "move",
            "row": 7,
            "col": 7
        })
        
        # Should not receive game_update for invalid move
        with pytest.raises(WebSocketDisconnect):
            websocket.receive_json()
