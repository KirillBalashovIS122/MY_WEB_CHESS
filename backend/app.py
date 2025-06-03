import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import chess
import asyncio
from typing import Dict, Optional, List
import uuid
from datetime import datetime
from chess_ai import get_best_move, available_ais
from chess_engine import create_board, is_game_over, get_legal_moves, make_move, get_game_result

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GameState(BaseModel):
    game_id: str
    board: str
    turn: str
    moves: List[str]
    game_over: bool
    winner: Optional[str] = None
    ai_thinking: bool = False
    mode: str
    player1: str
    player2: str
    captured_by_player1: List[str] = Field(default_factory=list)
    captured_by_player2: List[str] = Field(default_factory=list)

class MoveRequest(BaseModel):
    game_id: str
    from_square: str
    to_square: str
    promotion: Optional[str] = None

class GameConfig(BaseModel):
    mode: str
    player1: str
    player2: Optional[str] = None
    ai_white: Optional[str] = None
    ai_black: Optional[str] = None

class SurrenderRequest(BaseModel):
    game_id: str
    player: int

games: Dict[str, Dict] = {}
ai_tasks: Dict[str, asyncio.Task] = {}
game_scores: Dict[str, Dict] = {}
player_scores: Dict[str, Dict] = {}

PIECE_VALUES = {
    'p': 1, 'P': 1,
    'n': 3, 'N': 3,
    'b': 3, 'B': 3,
    'r': 5, 'R': 5,
    'q': 9, 'Q': 9,
}

@app.post("/api/game/start")
async def start_game(config: GameConfig):
    if len(config.player1) > 20 or (config.player2 and len(config.player2) > 20):
        raise HTTPException(status_code=400, detail="Имя игрока слишком длинное")
    
    if config.mode not in ["pvp", "pvai", "aivai"]:
        raise HTTPException(status_code=400, detail="Недопустимый режим игры")
    
    if config.mode == "pvai" and (not config.ai_black or config.ai_black not in available_ais):
        raise HTTPException(status_code=400, detail="Недопустимое имя ИИ для чёрных")
    
    if config.mode == "aivai" and (
        not config.ai_white or not config.ai_black or 
        config.ai_white not in available_ais or config.ai_black not in available_ais
    ):
        raise HTTPException(status_code=400, detail="Недопустимая комбинация ИИ")
    
    player2 = config.player2 or ("ИИ" if config.mode in ["pvai", "aivai"] else "Игрок 2")
    game_id = str(uuid.uuid4())
    
    if config.player1 not in player_scores:
        player_scores[config.player1] = {"wins": 0, "losses": 0, "draws": 0}
    if player2 not in player_scores:
        player_scores[player2] = {"wins": 0, "losses": 0, "draws": 0}
    
    games[game_id] = {
        "board": create_board(),
        "mode": config.mode,
        "player1": config.player1,
        "player2": player2,
        "moves": [],
        "game_over": False,
        "winner": None,
        "ai_white": config.ai_white if config.mode == "aivai" else None,
        "ai_black": config.ai_black if config.mode in ["pvai", "aivai"] else None,
        "started_at": datetime.now().isoformat(),
        "status": "ожидание",
        "captured_by_player1": [],
        "captured_by_player2": [],
        "scores_updated": False
    }
    
    session_key = f"{config.player1}_{player2}_{config.mode}"
    if not game_scores.get(session_key):
        game_scores[session_key] = {
            "player1": config.player1,
            "player2": player2,
            "scores": {
                config.player1: {"wins": 0, "losses": 0, "draws": 0},
                player2: {"wins": 0, "losses": 0, "draws": 0}
            }
        }
    
    games[game_id]["session_key"] = session_key
    
    if config.mode == "aivai":
        games[game_id]["status"] = "game"
        logger.debug(f"Starting AI vs AI game {game_id} with {config.ai_white} vs {config.ai_black}")
        ai_tasks[game_id] = asyncio.create_task(make_ai_move(game_id))
    
    logger.info(f"Игра {game_id} начата: {config.mode}, player1={config.player1}, player2={player2}")
    return {"game_id": game_id, "player2": player2}

@app.get("/api/game/state", response_model=GameState)
async def get_state(game_id: str):
    game = games.get(game_id)
    if not game:
        logger.error(f"Game {game_id} not found")
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    board = game["board"]
    return GameState(
        game_id=game_id,
        board=board.fen(),
        turn="белые" if board.turn else "чёрные",
        moves=[move.uci() for move in board.move_stack],
        game_over=game["game_over"],
        winner=game["winner"],
        ai_thinking=game.get("ai_thinking", False),
        mode=game["mode"],
        player1=game["player1"],
        player2=game["player2"],
        captured_by_player1=game["captured_by_player1"],
        captured_by_player2=game["captured_by_player2"],
    )

@app.get("/api/game/select")
async def select_square(game_id: str, square: str):
    game = games.get(game_id)
    if not game:
        logger.error(f"Game {game_id} not found")
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    if game["game_over"]:
        logger.warning(f"Game {game_id} is already over")
        raise HTTPException(status_code=400, detail="Игра завершена")
    
    board = game["board"]
    legal_moves = get_legal_moves(board, square)
    valid_moves = [move.uci() for move in legal_moves]
    logger.debug(f"Legal moves for square {square} in game {game_id}: {valid_moves}")
    
    return {"game_id": game_id, "square": square, "legal_moves": valid_moves}

@app.post("/api/game/move")
async def make_move_endpoint(move: MoveRequest, background_tasks: BackgroundTasks):
    game = games.get(move.game_id)
    if not game:
        logger.error(f"Game {move.game_id} not found")
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    board = game["board"]
    if game["game_over"]:
        logger.warning(f"Game {move.game_id} is already over")
        raise HTTPException(status_code=400, detail="Игра завершена")
    
    if game["status"] == "ожидание":
        game["status"] = "game"
        logger.debug(f"Game {move.game_id} status changed to 'game'")
    
    uci_move = move.from_square + move.to_square
    if move.promotion:
        uci_move += move.promotion.lower()
    
    is_promotion = False
    piece = board.piece_at(chess.parse_square(move.from_square))
    if piece and piece.piece_type == chess.PAWN:
        to_rank = chess.square_rank(chess.parse_square(move.to_square))
        if to_rank == 0 or to_rank == 7:
            is_promotion = True
            if not move.promotion:
                logger.error(f"Promotion piece not specified for move {uci_move}")
                raise HTTPException(status_code=400, detail="Не указана фигура для превращения")
    
    success, captured_piece = make_move(board, uci_move)
    if not success:
        logger.error(f"Invalid move {uci_move} in game {move.game_id}")
        raise HTTPException(status_code=400, detail="Недопустимый ход")
    
    if captured_piece:
        piece_symbol = captured_piece.symbol()
        if board.turn == chess.WHITE:
            game["captured_by_player1"].append(piece_symbol)
        else:
            game["captured_by_player2"].append(piece_symbol)
        logger.debug(f"Captured piece {piece_symbol} in game {move.game_id}")
    
    game["moves"].append(uci_move)
    
    if is_game_over(board):
        game["game_over"] = True
        game["status"] = "завершена"
        result = get_game_result(board)
        game["winner"] = (
            game["player1"] if result == "1-0" 
            else game["player2"] if result == "0-1" 
            else "Ничья"
        )
        logger.info(f"Game {move.game_id} ended with result {result}, winner: {game['winner']}")
        
        session_key = game["session_key"]
        score = game_scores[session_key]["scores"]
        if not game.get("scores_updated", False):
            if game["winner"] == game["player1"]:
                player_scores[game["player1"]]["wins"] += 1
                player_scores[game["player2"]]["losses"] += 1
                score[game["player1"]]["wins"] += 1
                score[game["player2"]]["losses"] += 1
            elif game["winner"] == game["player2"]:
                player_scores[game["player2"]]["wins"] += 1
                player_scores[game["player1"]]["losses"] += 1
                score[game["player2"]]["wins"] += 1
                score[game["player1"]]["losses"] += 1
            else:
                player_scores[game["player1"]]["draws"] += 1
                player_scores[game["player2"]]["draws"] += 1
                score[game["player1"]]["draws"] += 1
                score[game["player2"]]["draws"] += 1
            game["scores_updated"] = True
            logger.debug(f"Scores updated for game {move.game_id}: {score}")
    
    if not game["game_over"]:
        if game["mode"] == "pvai" and not board.turn:
            logger.debug(f"Scheduling AI move for black in game {move.game_id}")
            background_tasks.add_task(make_ai_move, move.game_id)
        elif game["mode"] == "aivai":
            logger.debug(f"Scheduling AI move for {'white' if board.turn else 'black'} in game {move.game_id}")
            background_tasks.add_task(make_ai_move, move.game_id)
    
    return {"success": True, "state": await get_state(move.game_id)}

@app.post("/api/game/surrender")
async def surrender_game(surrender: SurrenderRequest):
    game = games.get(surrender.game_id)
    if not game:
        logger.error(f"Game {surrender.game_id} not found")
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    if game["game_over"]:
        logger.warning(f"Game {surrender.game_id} is already over")
        raise HTTPException(status_code=400, detail="Игра уже завершена")
    
    game["game_over"] = True
    game["status"] = "завершена"
    
    winner = game["player2"] if surrender.player == 1 else game["player1"]
    game["winner"] = winner
    logger.info(f"Game {surrender.game_id} ended by surrender, winner: {winner}")
    
    session_key = game["session_key"]
    score = game_scores[session_key]["scores"]
    if not game.get("scores_updated", False):
        if winner == game["player1"]:
            player_scores[game["player1"]]["wins"] += 1
            player_scores[game["player2"]]["losses"] += 1
            score[game["player1"]]["wins"] += 1
            score[game["player2"]]["losses"] += 1
        else:
            player_scores[game["player2"]]["wins"] += 1
            player_scores[game["player1"]]["losses"] += 1
            score[game["player2"]]["wins"] += 1
            score[game["player1"]]["losses"] += 1
        game["scores_updated"] = True
        logger.debug(f"Scores updated for game {surrender.game_id}: {score}")
    
    return {"success": True, "state": await get_state(surrender.game_id)}

@app.post("/api/game/stop")
async def stop_game(game_id: str):
    game = games.get(game_id)
    if not game:
        logger.error(f"Game {game_id} not found")
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    if game["mode"] != "aivai":
        logger.warning(f"Game {game_id} is not in AI vs AI mode")
        raise HTTPException(status_code=400, detail="Только для режима ИИ против ИИ")
    
    task = ai_tasks.get(game_id)
    if task:
        task.cancel()
        del ai_tasks[game_id]
        logger.debug(f"AI task for game {game_id} canceled")
    
    del games[game_id]
    logger.info(f"Game {game_id} stopped")
    return {"success": True}

@app.get("/api/game/score")
async def get_game_score(game_id: str):
    game = games.get(game_id)
    if not game:
        logger.error(f"Game {game_id} not found")
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    session_key = game["session_key"]
    score = game_scores.get(session_key)
    if not score:
        logger.error(f"Score not found for session {session_key}")
        raise HTTPException(status_code=404, detail="Счёт не найден")
    
    logger.debug(f"Returning score for game {game_id}: {score}")
    return {
        "player1": score["player1"],
        "player2": score["player2"],
        "scores": score["scores"],
        "score": f"{score['scores'][score['player1']]['wins']} - {score['scores'][score['player2']]['wins']}"
    }

async def make_ai_move(game_id: str):
    game = games.get(game_id)
    if not game:
        logger.error(f"Game {game_id} not found in make_ai_move")
        return
    
    if game["game_over"]:
        logger.warning(f"Game {game_id} already over in make_ai_move")
        return
    
    game["ai_thinking"] = True
    logger.info(f"AI thinking for game {game_id}, turn: {'white' if game['board'].turn else 'black'}")
    
    try:
        board = game["board"]
        
        if game["mode"] == "pvai" and not board.turn:
            ai_name = game["ai_black"]
        elif game["mode"] == "aivai":
            ai_name = game["ai_white"] if board.turn else game["ai_black"]
        else:
            logger.warning(f"Invalid mode for AI move in game {game_id}")
            return
        
        logger.info(f"Requesting move from AI {ai_name} for game {game_id}, FEN: {board.fen()}")
        ai_move = await get_best_move(board, ai_name)
        
        if not ai_move or ai_move not in board.legal_moves:
            logger.error(f"AI {ai_name} failed to produce a valid move for game {game_id}, FEN: {board.fen()}")
            game["game_over"] = True
            game["status"] = "завершена"
            game["winner"] = "Ошибка ИИ"
            return
        
        captured_piece = board.piece_at(ai_move.to_square)
        if captured_piece:
            piece_symbol = captured_piece.symbol()
            if board.turn == chess.WHITE:
                game["captured_by_player1"].append(piece_symbol)
            else:
                game["captured_by_player2"].append(piece_symbol)
            logger.debug(f"Captured piece {piece_symbol} by AI {ai_name} in game {game_id}")
        
        board.push(ai_move)
        game["moves"].append(ai_move.uci())
        logger.info(f"AI {ai_name} made move {ai_move.uci()} in game {game_id}, new FEN: {board.fen()}")
        
        if is_game_over(board):
            game["game_over"] = True
            game["status"] = "завершена"
            result = get_game_result(board)
            game["winner"] = (
                game["player1"] if result == "1-0" 
                else game["player2"] if result == "0-1" 
                else "Ничья"
            )
            logger.info(f"Game {game_id} ended with result {result}, winner: {game['winner']}")
            
            session_key = game["session_key"]
            score = game_scores[session_key]["scores"]
            if not game.get("scores_updated", False):
                if game["winner"] == game["player1"]:
                    player_scores[game["player1"]]["wins"] += 1
                    player_scores[game["player2"]]["losses"] += 1
                    score[game["player1"]]["wins"] += 1
                    score[game["player2"]]["losses"] += 1
                elif game["winner"] == game["player2"]:
                    player_scores[game["player2"]]["wins"] += 1
                    player_scores[game["player1"]]["losses"] += 1
                    score[game["player2"]]["wins"] += 1
                    score[game["player1"]]["losses"] += 1
                else:
                    player_scores[game["player1"]]["draws"] += 1
                    player_scores[game["player2"]]["draws"] += 1
                    score[game["player1"]]["draws"] += 1
                    score[game["player2"]]["draws"] += 1
                game["scores_updated"] = True
                logger.debug(f"Scores updated for game {game_id}: {score}")
            
        if game["mode"] == "aivai" and not game["game_over"]:
            await asyncio.sleep(2)
            logger.debug(f"Scheduling next AI move for game {game_id}")
            ai_tasks[game_id] = asyncio.create_task(make_ai_move(game_id))
    except Exception as e:
        logger.error(f"Error in AI move for game {game_id}: {str(e)}")
        game["game_over"] = True
        game["status"] = "завершена"
        game["winner"] = "Ошибка ИИ"
    finally:
        game["ai_thinking"] = False

@app.on_event("shutdown")
async def shutdown_event():
    for game_id, task in ai_tasks.items():
        task.cancel()
        logger.debug(f"AI task for game {game_id} canceled during shutdown")
    ai_tasks.clear()