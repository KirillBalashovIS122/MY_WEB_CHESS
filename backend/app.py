import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess
import asyncio
from typing import List, Optional, Dict
import os
import uuid
from datetime import datetime
from ais import available_ais
from chess_ai import get_best_move, load_custom_light_model
from chess_engine import create_board, is_game_over, get_legal_moves, make_move, get_game_result

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://frontend:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

class MoveRequest(BaseModel):
    game_id: str
    from_square: str
    to_square: str
    promotion: Optional[str] = None

class GameConfig(BaseModel):
    mode: str
    player1: str
    player2: Optional[str] = None
    ai_name: Optional[str] = None

class SurrenderRequest(BaseModel):
    game_id: str
    player: int

class GameInfo(BaseModel):
    game_id: str
    mode: str
    player1: str
    player2: str
    started_at: str
    moves_count: int
    status: str

games: Dict[str, Dict] = {}
ai_tasks: Dict[str, asyncio.Task] = {}

@app.post("/api/game/start")
async def start_game(config: GameConfig):
    logger.debug(f"Получен запрос на начало игры: {config.dict()}")
    if len(config.player1) > 20 or (config.player2 and len(config.player2) > 20):
        raise HTTPException(status_code=400, detail="Имя игрока слишком длинное")
    
    if config.mode not in ["pvp", "pvai", "aivai"]:
        raise HTTPException(status_code=400, detail="Недопустимый режим")
    
    if config.mode in ["pvai", "aivai"] and (not config.ai_name or config.ai_name not in available_ais):
        raise HTTPException(status_code=400, detail="Недопустимое имя ИИ")
    
    player2 = config.player2 or ("ИИ" if config.mode in ["pvai", "aivai"] else "Игрок 2")
    game_id = str(uuid.uuid4())
    
    games[game_id] = {
        "board": create_board(),
        "mode": config.mode,
        "player1": config.player1,
        "player2": player2,
        "moves": [],
        "game_over": False,
        "winner": None,
        "ai_name": config.ai_name if config.mode in ["pvai", "aivai"] else None,
        "ai_thinking": False,
        "started_at": datetime.now().isoformat(),
        "status": "ожидание"
    }
    
    if config.mode == "aivai":
        games[game_id]["status"] = "игра"
        logger.info(f"Запланирован ход ИИ для игры AIvAI {game_id}")
        ai_tasks[game_id] = asyncio.create_task(make_ai_move(game_id))
    
    logger.info(f"Игра {game_id} начата: {config.mode}, игрок 1: {config.player1}, игрок 2: {player2}")
    return {"game_id": game_id, "player2": player2}

@app.get("/api/game/state", response_model=GameState)
async def get_state(game_id: str):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    board = game["board"]
    logger.debug(f"Returning board state for game {game_id}: {board.fen()}")
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
        player2=game["player2"]
    )

@app.get("/api/game/select")
async def select_piece(game_id: str, square: str):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    board = game["board"]
    possible_moves = get_legal_moves(board, square)
    logger.debug(f"Выбрана клетка {square} в игре {game_id}, возможные ходы: {possible_moves}")
    return {"possible_moves": possible_moves}

@app.post("/api/game/move")
async def make_move_endpoint(move: MoveRequest, background_tasks: BackgroundTasks):
    game = games.get(move.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    board = game["board"]
    if game["game_over"]:
        raise HTTPException(status_code=400, detail="Игра уже завершена")
    
    try:
        if game["status"] == "ожидание":
            game["status"] = "игра"
        
        uci_move = f"{move.from_square}{move.to_square}"
        if move.promotion:
            uci_move += move.promotion.lower()
        
        if not make_move(board, uci_move):
            raise HTTPException(status_code=400, detail="Недопустимый ход")
        
        game["moves"].append(uci_move)
        logger.info(f"Ход {uci_move} сделан в игре {move.game_id}, новое состояние: {board.fen()}")
        
        if is_game_over(board):
            game["game_over"] = True
            game["status"] = "завершена"
            result = get_game_result(board)
            game["winner"] = (
                game["player1"] if result == "1-0" 
                else game["player2"] if result == "0-1" 
                else "Ничья"
            )
            logger.info(f"Игра {move.game_id} завершена: победитель {game['winner']}")
        
        if game["mode"] in ["pvai", "aivai"] and not game["game_over"]:
            if (game["mode"] == "pvai" and not board.turn) or game["mode"] == "aivai":
                logger.info(f"Запланирован ход ИИ для игры {move.game_id}")
                background_tasks.add_task(make_ai_move, move.game_id)
        
        return {"success": True, "state": await get_state(move.game_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Недопустимый ход: {str(e)}")

@app.post("/api/game/surrender")
async def surrender_game(surrender: SurrenderRequest):
    game = games.get(surrender.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    
    if game["game_over"]:
        raise HTTPException(status_code=400, detail="Игра уже завершена")
    
    game["game_over"] = True
    game["status"] = "завершена"
    game["winner"] = game["player2"] if surrender.player == 1 else game["player1"]
    logger.info(f"Игра {surrender.game_id} завершена сдачей: победитель {game['winner']}")
    
    return {"success": True, "state": await get_state(surrender.game_id)}

@app.get("/api/ai/models", response_model=dict)
async def get_ai_models():
    models = list(available_ais.keys())
    logger.debug(f"Доступные модели: {models}")
    return {"models": models}

@app.get("/api/games/active", response_model=List[GameInfo])
async def get_active_games():
    active = []
    for game_id, game in games.items():
        if game["status"] != "завершена":
            active.append({
                "game_id": game_id,
                "mode": game["mode"],
                "player1": game["player1"],
                "player2": game["player2"],
                "started_at": game["started_at"],
                "moves_count": len(game["moves"]),
                "status": game["status"]
            })
    logger.debug(f"Активные игры: {len(active)}")
    return active

async def make_ai_move(game_id: str):
    game = games.get(game_id)
    if not game or game["game_over"]:
        logger.info(f"Ход ИИ пропущен: игра {game_id} не найдена или завершена")
        return
    
    logger.info(f"Начало хода ИИ для игры {game_id}, режим: {game['mode']}, ход: {'белые' if game['board'].turn else 'чёрные'}")
    
    game["ai_thinking"] = True
    
    try:
        board = game["board"]
        ai_name = game["ai_name"]
        
        ai_move = await get_best_move(
            board,
            ai_name,
            depth=3 if ai_name == "stockfish" else 1,
            skill_level=1 if ai_name == "stockfish" else 1
        )
        
        if ai_move and ai_move in board.legal_moves:
            logger.info(f"Выбран ход ИИ: {ai_move.uci()}")
            board.push(ai_move)
            game["moves"].append(ai_move.uci())
            logger.debug(f"Состояние доски после хода ИИ: {board.fen()}")
            
            if is_game_over(board):
                game["game_over"] = True
                game["status"] = "завершена"
                result = get_game_result(board)
                game["winner"] = (
                    game["player1"] if result == "1-0" 
                    else game["player2"] if result == "0-1" 
                    else "Ничья"
                )
                logger.info(f"Игра {game_id} завершена: победитель {game['winner']}")
            
            if game["mode"] == "aivai" and not game["game_over"]:
                logger.info(f"Запланирован следующий ход ИИ для режима AIvAI")
                await asyncio.sleep(1)
                ai_tasks[game_id] = asyncio.create_task(make_ai_move(game_id))
        else:
            logger.warning(f"ИИ не вернул допустимый ход для игры {game_id}")
    except Exception as e:
        logger.error(f"Ошибка хода ИИ в игре {game_id}: {str(e)}")
    finally:
        game["ai_thinking"] = False

@app.on_event("startup")
async def startup_event():
    logger.info("Запуск API шахматного приложения")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Files in directory: {os.listdir()}")
    if os.path.exists("engines/numbfish"):
        logger.info(f"Files in engines: {os.listdir('engines/numbfish')}")
    os.makedirs("models", exist_ok=True)
    load_custom_light_model()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Остановка приложения")
    for task in ai_tasks.values():
        task.cancel()

@app.get("/test-engines")
async def test_engines():
    import time
    board = chess.Board()
    results = {}
    for ai_name in available_ais:
        start = time.time()
        move = await get_best_move(board.copy(), ai_name)
        results[ai_name] = {
            "move": move.uci() if move else None,
            "time": time.time() - start
        }
    return results
