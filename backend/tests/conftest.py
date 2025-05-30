import pytest
import chess
from fastapi.testclient import TestClient
from backend.app import app, games, ai_tasks
from backend.chess_engine import create_board

@pytest.fixture(autouse=True)
def reset_state():
    """Сбрасывает состояние приложения перед каждым тестом"""
    games.clear()
    ai_tasks.clear()

@pytest.fixture
def test_client():
    """Фикстура для TestClient FastAPI"""
    return TestClient(app)

@pytest.fixture
def new_board():
    """Фикстура для новой шахматной доски"""
    return create_board()

@pytest.fixture
def game_id(test_client):
    """Фикстура создает новую игру и возвращает её ID"""
    response = test_client.post("/api/game/start", json={
        "mode": "pvp",
        "player1": "Player1",
        "player2": "Player2"
    })
    return response.json()["game_id"]