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

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

class AIConfig(BaseModel):
    depth: int = 3
    model: Optional[str] = "custom_model.h5"  # Изменено: model теперь необязательный
    use_stockfish: bool = False
    skill_level: int = 20

class GameConfig(BaseModel):
    mode: str
    player1: str
    player2: Optional[str] = None
    ai_config: Optional[AIConfig] = None

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
    logger.debug(f"Received game start request with body: {config.dict()}")
    if len(config.player1) > 20 or (config.player2 and len(config.player2) > 20):
        raise HTTPException(status_code=400, detail="Player name too long")
    
    if config.mode not in ["pvp", "pvai", "aivai"]:
        raise HTTPException(status_code=400, detail="Invalid mode")
    
    player2 = config.player2 or ("AI" if config.mode in ["pvai", "aivai"] else "Player2")
    game_id = str(uuid.uuid4())
    
    default_ai_config = {
        "depth": 3,
        "model": config.ai_config.model if config.ai_config else "custom_model.h5",
        "use_stockfish": config.ai_config.use_stockfish if config.ai_config else False,
        "skill_level": 20
    }
    
    games[game_id] = {
        "board": chess.Board(),
        "mode": config.mode,
        "player1": config.player1,
        "player2": player2,
        "moves": [],
        "game_over": False,
        "winner": None,
        "ai_config": default_ai_config,
        "ai_thinking": False,
        "started_at": datetime.now().isoformat(),
        "status": "waiting"
    }
    
    if config.mode == "aivai":
        games[game_id]["status"] = "playing"
        logger.info(f"Scheduling AI move for AIVAI game {game_id}")
        asyncio.create_task(make_ai_move(game_id))
    
    logger.info(f"Game {game_id} started: {config.mode}, player1: {config.player1}, player2: {player2}")
    return {"game_id": game_id, "player2": player2}

@app.get("/api/game/state", response_model=GameState)
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
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = game["board"]
    try:
        square = chess.parse_square(square)
        possible_moves = [
            move.uci() for move in board.legal_moves
            if move.from_square == square
        ]
        logger.debug(f"Selected square {square} in game {game_id}, possible moves: {possible_moves}")
        return {"possible_moves": possible_moves}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid square")

@app.post("/api/game/move")
async def make_move(move: MoveRequest, background_tasks: BackgroundTasks):
    game = games.get(move.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    board = game["board"]
    if game["game_over"]:
        raise HTTPException(status_code=400, detail="Game is already over")
    
    try:
        if game["status"] == "waiting":
            game["status"] = "playing"
        
        uci_move = f"{move.from_square}{move.to_square}"
        move_obj = chess.Move.from_uci(uci_move)
        
        if (move_obj.to_square // 8 == 7 and board.piece_at(move_obj.from_square).piece_type == chess.PAWN and board.turn) or \
           (move_obj.to_square // 8 == 0 and board.piece_at(move_obj.from_square).piece_type == chess.PAWN and not board.turn):
            if not move.promotion:
                raise HTTPException(status_code=400, detail="Promotion required")
            uci_move += move.promotion.lower()
            move_obj = chess.Move.from_uci(uci_move)
        
        if move_obj not in board.legal_moves:
            raise HTTPException(status_code=400, detail="Illegal move")
        
        board.push(move_obj)
        game["moves"].append(move_obj.uci())
        logger.info(f"Move {move_obj.uci()} made in game {move.game_id}")
        
        if board.is_game_over():
            game["game_over"] = True
            game["status"] = "finished"
            result = board.result()
            game["winner"] = (
                game["player1"] if result == "1-0" 
                else game["player2"] if result == "0-1" 
                else "Draw"
            )
            logger.info(f"Game {move.game_id} ended: {game['winner']}")
        
        if game["mode"] in ["pvai", "aivai"] and not game["game_over"]:
            if (game["mode"] == "pvai" and not board.turn) or game["mode"] == "aivai":
                logger.info(f"Scheduling AI move for game {move.game_id}")
                background_tasks.add_task(make_ai_move, move.game_id)
        
        return {"success": True, "state": await get_state(move.game_id)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid move: {str(e)}")
    except AttributeError:
        raise HTTPException(status_code=400, detail="No piece at starting square")

@app.post("/api/game/surrender")
async def surrender_game(surrender: SurrenderRequest):
    game = games.get(surrender.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game["game_over"]:
        raise HTTPException(status_code=400, detail="Game is already over")
    
    game["game_over"] = True
    game["status"] = "finished"
    game["winner"] = game["player2"] if surrender.player == 1 else game["player1"]
    logger.info(f"Game {surrender.game_id} surrendered: winner {game['winner']}")
    
    return {"success": True, "state": await get_state(surrender.game_id)}

@app.post("/api/ai/configure")
async def configure_ai(game_id: str, config: AIConfig):
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game["mode"] not in ["pvai", "aivai"]:
        raise HTTPException(status_code=400, detail="AI configuration only available in pvai or aivai modes")
    
    game["ai_config"] = config.dict()
    logger.info(f"AI config updated for game {game_id}: {config}")
    return {"status": "AI configuration updated"}

@app.get("/api/ai/models", response_model=dict)
async def get_ai_models():
    models = []
    model_dir = "models"
    if os.path.exists(model_dir):
        models = [f for f in os.listdir(model_dir) if f.endswith(".h5")]
    logger.debug(f"Available models: {models}")
    return {"models": models}

@app.get("/api/games/active", response_model=List[GameInfo])
async def get_active_games():
    active = []
    for game_id, game in games.items():
        if game["status"] != "finished":
            active.append({
                "game_id": game_id,
                "mode": game["mode"],
                "player1": game["player1"],
                "player2": game["player2"],
                "started_at": game["started_at"],
                "moves_count": len(game["moves"]),
                "status": game["status"]
            })
    logger.debug(f"Active games: {len(active)}")
    return active

async def make_ai_move(game_id: str):
    game = games.get(game_id)
    if not game or game["game_over"]:
        logger.info(f"AI move skipped: game {game_id} not found or already over")
        return
    
    logger.info(f"Starting AI move for game {game_id}, mode: {game['mode']}, turn: {'white' if game['board'].turn else 'black'}")
    
    game["ai_thinking"] = True
    
    try:
        board = game["board"]
        config = game["ai_config"]
        
        from chess_ai import get_best_move
        
        logger.debug(f"AI config: {config}")
        ai_move = await get_best_move(
            board,
            use_model=not config["use_stockfish"]
        )
        
        if ai_move and ai_move in board.legal_moves:
            logger.info(f"AI move selected: {ai_move.uci()}")
            board.push(ai_move)
            game["moves"].append(ai_move.uci())
            
            if board.is_game_over():
                game["game_over"] = True
                game["status"] = "finished"
                result = board.result()
                game["winner"] = (
                    game["player1"] if result == "1-0" 
                    else game["player2"] if result == "0-1" 
                    else "Draw"
                )
                logger.info(f"Game {game_id} ended: {game['winner']}")
            
            if game["mode"] == "aivai" and not game["game_over"]:
                logger.info(f"Scheduling next AI move for AIVAI mode")
                await asyncio.sleep(1)
                asyncio.create_task(make_ai_move(game_id))
        else:
            logger.warning(f"No valid AI move returned for game {game_id}")
    except Exception as e:
        logger.error(f"AI move failed in game {game_id}: {str(e)}")
    finally:
        game["ai_thinking"] = False

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Chess Web App API")
    os.makedirs("models", exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Chess Web App API")
    for task in ai_tasks.values():
        task.cancel()
