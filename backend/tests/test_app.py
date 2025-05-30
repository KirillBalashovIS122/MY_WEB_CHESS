import pytest
from fastapi import status

def test_start_game(test_client):
    response = test_client.post("/api/game/start", json={
        "mode": "pvp",
        "player1": "Player1",
        "player2": "Player2"
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "game_id" in data
    assert "player2" in data

def test_get_state(test_client, game_id):
    response = test_client.get(f"/api/game/state?game_id={game_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["board"] == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    assert data["turn"] == "белые"

def test_make_move(test_client, game_id):
    move_data = {
        "game_id": game_id,
        "from_square": "e2",
        "to_square": "e4"
    }
    response = test_client.post("/api/game/move", json=move_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "e4" in data["state"]["board"]

def test_get_legal_moves(test_client, game_id):
    response = test_client.get(f"/api/game/select?game_id={game_id}&square=e2")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "e4" in data["possible_moves"]

def test_surrender(test_client, game_id):
    surrender_data = {
        "game_id": game_id,
        "player": 1
    }
    response = test_client.post("/api/game/surrender", json=surrender_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["state"]["game_over"] is True
    assert data["state"]["winner"] == "Player2"

def test_get_ai_models(test_client):
    response = test_client.get("/api/ai/models")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "models" in data
    assert "stockfish" in data["models"]
