import logging
import chess
import chess.engine
import numpy as np
import tensorflow as tf
from tensorflow import keras
from typing import Optional
import os.path

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

custom_light_model = None

available_ais = {
    "stockfish": {
        "type": "uci",
        "path": "/usr/games/stockfish",
        "depth": 3,
        "skill_level": 20
    },
    "numfish": {
        "type": "uci",
        "command": ["python3", "/app/backend/engines/numbfish/numbfish.py"],
        "depth": 3,
        "skill_level": 20
    },
    "custom_light": {
        "type": "keras",
        "path": "custom_light"
    }
}

class ChessAIModel:
    """Класс для работы с моделями ИИ."""
    def __init__(self, model):
        self.model = model
    
    @tf.function(reduce_retracing=True)
    def predict(self, input_data):
        return self.model(input_data, training=False)

def load_custom_light_model():
    """Загружает модель Keras для легкого ИИ."""
    global custom_light_model
    if custom_light_model is None:
        model_path = os.path.join('/app/backend/models', 'light_model.keras')
        if not os.path.exists(model_path):
            logger.error("Custom light model file not found")
            return None
        try:
            model = keras.models.load_model(model_path)
            custom_light_model = ChessAIModel(model)
            logger.info("Custom light model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading custom light model: {e}")
            return None
    return custom_light_model

def board_to_input(board: chess.Board, ai_name: str) -> np.ndarray:
    """Преобразует шахматную доску в входные данные для нейросети."""
    tensor = np.zeros((1, 8, 8, 14), dtype=np.float32)
    piece_map = {
        chess.PAWN: {chess.WHITE: 0, chess.BLACK: 6},
        chess.KNIGHT: {chess.WHITE: 1, chess.BLACK: 7},
        chess.BISHOP: {chess.WHITE: 2, chess.BLACK: 8},
        chess.ROOK: {chess.WHITE: 3, chess.BLACK: 9},
        chess.QUEEN: {chess.WHITE: 4, chess.BLACK: 10},
        chess.KING: {chess.WHITE: 5, chess.BLACK: 11}
    }
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            row = 7 - (square // 8)
            col = square % 8
            layer = piece_map[piece.piece_type][piece.color]
            tensor[0, row, col, layer] = 1
    tensor[0, :, :, 12] = int(board.turn)
    tensor[0, :, :, 13] = board.ply() / 2
    return tensor

def predictions_to_move(predictions, board: chess.Board, ai_name: str) -> Optional[chess.Move]:
    """Преобразует предсказания нейросети в шахматный ход."""
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None
    if ai_name == "custom_light":
        if isinstance(predictions, (list, tuple)) and len(predictions) == 2:
            from_probs, to_probs = predictions
            from_probs = np.array(from_probs).reshape(1, 64)
            to_probs = np.array(to_probs).reshape(1, 64)
            move_scores = {}
            for move in legal_moves:
                score = from_probs[0][move.from_square] * to_probs[0][move.to_square] + 1e-8
                if score > 0:
                    move_scores[move] = score
            if not move_scores:
                return None
            return max(move_scores.items(), key=lambda x: x[1])[0]
    return None

async def get_best_move(board: chess.Board, ai_name: str, depth: int = 3, skill_level: int = 20) -> Optional[chess.Move]:
    """Возвращает лучший ход для указанного ИИ."""
    ai_info = available_ais.get(ai_name)
    if not ai_info:
        logger.warning(f"AI configuration not found for {ai_name}")
        return None
    
    try:
        if ai_info["type"] == "uci":
            return await get_best_move_uci(board, ai_info, depth, skill_level)
        elif ai_info["type"] == "keras":
            return get_best_move_keras(board, ai_info)
    except Exception as e:
        logger.error(f"Error getting best move for {ai_name}: {e}")
        return None

async def get_best_move_uci(board: chess.Board, ai_info: dict, depth: int, skill_level: int) -> Optional[chess.Move]:
    """Возвращает лучший ход для UCI-движка."""
    command = ai_info.get("command") or ai_info.get("path")
    if not command:
        return None
    
    try:
        transport, engine = await chess.engine.popen_uci(command)
        if ai_info.get("path", "").endswith("stockfish"):
            await engine.configure({"Skill Level": skill_level})
        result = await engine.play(
            board,
            chess.engine.Limit(depth=depth),
            info=chess.engine.INFO_ALL
        )
        move = result.move
        await engine.quit()
        if move and move in board.legal_moves:
            return move
        return None
    except Exception as e:
        logger.error(f"Error in UCI engine: {e}")
        return None
    finally:
        try:
            if 'engine' in locals():
                await engine.quit()
        except Exception:
            pass

def get_best_move_keras(board: chess.Board, ai_info: dict) -> Optional[chess.Move]:
    """Возвращает лучший ход для модели Keras."""
    try:
        model = load_custom_light_model()
        if not model:
            logger.error("Custom light model not loaded")
            return None
        input_data = board_to_input(board, ai_info["path"])
        predictions = model.predict(input_data)
        return predictions_to_move(predictions, board, "custom_light")
    except Exception as e:
        logger.error(f"Error in Keras model: {e}")
        return None
