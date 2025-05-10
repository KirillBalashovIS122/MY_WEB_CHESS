from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chess
import asyncio
from typing import List, Optional

app = FastAPI()

# Хранилище игр (в памяти для простоты)
games = {}

# Модель для ответа на запрос состояния игры
class GameState(BaseModel):
    game_id: str
    board: str  # FEN-строка
    turn: str  # "white" или "black"
    moves: List[str]  # Список ходов в UCI-нотации
    game_over: bool
    winner: Optional[str] = None

# Модель для запроса хода
class MoveRequest(BaseModel):
    game_id: str
    from_square: str  # Например, "e2"
    to_square: str    # Например, "e4"

@app.post("/game/start")
async def start_game(mode: str, player1: str = "Player1", player2: str = None):
    if mode not in ["pvp", "pvai", "aivai"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    player2 = "AI" if mode in ["pvai", "aivai"] else (player2 or "Player2")
    game_id = str(len(games) + 1)
    games[game_id] = {
        "board": chess.Board(),
        "mode": mode,
        "player1": player1,
        "player2": player2,
        "moves": [],
        "game_over": False,
        "winner": None
    }
    return {"game_id": game_id}

@app.get("/game/state", response_model=GameState)
async def get_state(game_id: str):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = game["board"]
    return GameState(
        game_id=game_id,
        board=board.fen(),
        turn="white" if board.turn else "black",
        moves=[move.uci() for move in board.move_stack],
        game_over=game["game_over"],
        winner=game["winner"]
    )

@app.get("/game/select")
async def select_piece(game_id: str, square: str):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = game["board"]
    try:
        square = chess.parse_square(square)  # Например, "e2" -> 12
        possible_moves = [
            board.san(move) for move in board.legal_moves
            if move.from_square == square
        ]
        return {"possible_moves": possible_moves}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid square")

@app.post("/game/move")
async def make_move(move: MoveRequest):
    game = games.get(move.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = game["board"]
    try:
        move_obj = chess.Move.from_uci(f"{move.from_square}{move.to_square}")
        if move_obj not in board.legal_moves:
            raise HTTPException(status_code=400, detail="Illegal move")
        
        board.push(move_obj)
        game["moves"].append(move_obj.uci())
        
        # Проверка окончания игры
        if board.is_game_over():
            game["game_over"] = True
            game["winner"] = "white" if board.result() == "1-0" else "black" if board.result() == "0-1" else None
        
        # Если режим PvAI или AIvAI, и ход ИИ
        if game["mode"] in ["pvai", "aivai"] and not game["game_over"]:
            if (game["mode"] == "pvai" and not board.turn) or game["mode"] == "aivai":
                await asyncio.sleep(5 if game["mode"] == "aivai" else 0)  # Задержка для AIvAI
                from chess_ai import get_best_move
                move = await get_best_move(board)
                if move:
                    board.push(move)
                    game["moves"].append(move.uci())
        
        return {"success": True, "state": await get_state(move.game_id)}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid move format")
