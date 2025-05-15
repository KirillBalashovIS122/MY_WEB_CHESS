from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess
import asyncio
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

games = {}

class GameState(BaseModel):
    game_id: str
    board: str
    turn: str
    moves: List[str]
    game_over: bool
    winner: Optional[str] = None

class MoveRequest(BaseModel):
    game_id: str
    from_square: str
    to_square: str
    promotion: Optional[str] = None

class SurrenderRequest(BaseModel):
    game_id: str
    player: int

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
    print(f"Game started: ID={game_id}, Mode={mode}, Player1={player1}, Player2={player2}")
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
        square = chess.parse_square(square)
        possible_moves = [
            move.uci() for move in board.legal_moves
            if move.from_square == square
        ]
        print(f"Selected square {square}: Possible moves={possible_moves}")
        return {"possible_moves": possible_moves}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid square")

@app.post("/game/move")
async def make_move(move: MoveRequest):
    game = games.get(move.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = game["board"]
    if game["game_over"]:
        raise HTTPException(status_code=400, detail="Game is already over")
    
    try:
        uci_move = f"{move.from_square}{move.to_square}"
        move_obj = chess.Move.from_uci(uci_move)
        
        if (move_obj.to_square // 8 == 7 and board.piece_at(move_obj.from_square).piece_type == chess.PAWN and board.turn) or \
           (move_obj.to_square // 8 == 0 and board.piece_at(move_obj.from_square).piece_type == chess.PAWN and not board.turn):
            if not move.promotion:
                move.promotion = 'q'
            uci_move += move.promotion.lower()
            move_obj = chess.Move.from_uci(uci_move)
        
        if move_obj not in board.legal_moves:
            raise HTTPException(status_code=400, detail="Illegal move")
        
        print(f"Applying move: {uci_move}")
        board.push(move_obj)
        game["moves"].append(move_obj.uci())
        
        if board.is_game_over():
            game["game_over"] = True
            result = board.result()
            if result == "1-0":
                game["winner"] = game["player1"]
            elif result == "0-1":
                game["winner"] = game["player2"]
            else:
                game["winner"] = "Draw"
            print(f"Game over: Result={result}, Winner={game['winner']}")
        
        if game["mode"] in ["pvai", "aivai"] and not game["game_over"]:
            if (game["mode"] == "pvai" and not board.turn) or game["mode"] == "aivai":
                await asyncio.sleep(1 if game["mode"] == "aivai" else 0)
                from chess_ai import get_best_move
                ai_move = await get_best_move(board)
                if ai_move:
                    board.push(ai_move)
                    game["moves"].append(ai_move.uci())
                    print(f"AI move: {ai_move.uci()}")
                    if board.is_game_over():
                        game["game_over"] = True
                        result = board.result()
                        if result == "1-0":
                            game["winner"] = game["player1"]
                        elif result == "0-1":
                            game["winner"] = game["player2"]
                        else:
                            game["winner"] = "Draw"
                        print(f"Game over: Result={result}, Winner={game['winner']}")
        
        return {"success": True, "state": await get_state(move.game_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid move format: {str(e)}")

@app.post("/game/surrender")
async def surrender_game(surrender: SurrenderRequest):
    game = games.get(surrender.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game["game_over"]:
        raise HTTPException(status_code=400, detail="Game is already over")
    
    game["game_over"] = True
    if surrender.player == 1:
        game["winner"] = game["player2"]
    elif surrender.player == 2:
        game["winner"] = game["player1"]
    else:
        raise HTTPException(status_code=400, detail="Invalid player number")
    
    print(f"Game surrendered: ID={surrender.game_id}, Loser=Player{surrender.player}, Winner={game['winner']}")
    return {"success": True, "state": await get_state(surrender.game_id)}