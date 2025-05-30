import logging
import chess
import chess.engine
import numpy as np
import tensorflow as tf
from tensorflow import keras
from typing import Optional
import random
import os.path

logger = logging.getLogger(__name__)

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
    def __init__(self, model):
        self.model = model
    
    @tf.function(reduce_retracing=True)
    def predict(self, input_data):
        return self.model(input_data, training=False)

def load_custom_light_model():
    global custom_light_model
    if custom_light_model is None:
        model_path = os.path.join('/app/backend/models', 'light_model.keras')
        logger.info(f"Loading model from: {model_path}")
        if not os.path.exists(model_path):
            logger.error(f"Model file not found at: {model_path}")
            return None
        try:
            model = keras.models.load_model(model_path)
            custom_light_model = ChessAIModel(model)
            logger.info("Model loaded successfully")
            test_model()
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
    return custom_light_model

def test_model():
    model = load_custom_light_model()
    if model:
        test_input = np.random.rand(1, 8, 8, 14).astype(np.float32)
        prediction = model.predict(test_input)
        logger.info(f"Model test prediction: {prediction}")

def board_to_input(board: chess.Board, ai_name: str) -> np.ndarray:
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
    logger.debug(f"Input tensor for {ai_name}: shape={tensor.shape}")
    logger.debug(f"Example tensor values: {tensor[0, :, :, 0]} (white pawns)")
    return tensor

def predictions_to_move(predictions, board: chess.Board, ai_name: str) -> Optional[chess.Move]:
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        logger.warning("No legal moves available")
        return None
    if ai_name == "custom_light":
        if isinstance(predictions, (list, tuple)) and len(predictions) == 2:
            from_probs, to_probs = predictions
            from_probs = np.array(from_probs).reshape(1, 64)
            to_probs = np.array(to_probs).reshape(1, 64)
            logger.debug(f"from_probs: {from_probs[0]}, to_probs: {to_probs[0]}")
            move_scores = {}
            for move in legal_moves:
                score = from_probs[0][move.from_square] * to_probs[0][move.to_square] + 1e-8
                if score > 0:
                    move_scores[move] = score
            if not move_scores:
                logger.warning("All probabilities zero, selecting random move")
                return random.choice(legal_moves)
            best_move = max(move_scores.items(), key=lambda x: x[1])[0]
            logger.debug(f"Best move: {best_move.uci()} (score: {move_scores[best_move]:.4f})")
            return best_move
        else:
            logger.error(f"Invalid predictions format: {type(predictions)}")
            return random.choice(legal_moves)
    return None

async def get_best_move(board: chess.Board, ai_name: str, depth: int = 3, skill_level: int = 20) -> Optional[chess.Move]:
    logger.debug(f"Requesting best move for AI: {ai_name}")
    ai_info = available_ais.get(ai_name)
    if not ai_info:
        logger.error(f"AI {ai_name} not found")
        return None
    try:
        if ai_info["type"] == "uci":
            return await get_best_move_uci(board, ai_info, depth, skill_level)
        elif ai_info["type"] == "keras":
            return get_best_move_keras(board, ai_info)
    except Exception as e:
        logger.error(f"AI error {ai_name}: {str(e)}")
        return None

async def get_best_move_uci(board: chess.Board, ai_info: dict, depth: int, skill_level: int) -> Optional[chess.Move]:
    command = ai_info.get("command") or ai_info.get("path")
    if not command:
        logger.error(f"No command or path for AI: {ai_info}")
        return None
    logger.debug(f"Starting UCI engine with command: {command}")
    logger.debug(f"Sending position to UCI engine: FEN={board.fen()}")
    if isinstance(command, list) and command[0] == "python3":
        script_path = command[1]
        if not os.path.exists(script_path):
            logger.error(f"Script file not found: {script_path}")
            return None
        logger.info(f"Confirmed script file exists: {script_path}")
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
            logger.info(f"AI returned move: {move.uci()}")
            return move
        else:
            logger.error(f"Illegal move returned by AI: {move.uci() if move else 'None'} in position {board.fen()}")
            return None
    except chess.engine.EngineError as e:
        logger.error(f"UCI engine error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected UCI engine error: {str(e)}")
        return None
    finally:
        try:
            if 'engine' in locals():
                await engine.quit()
        except Exception as e:
            logger.error(f"Error closing UCI engine: {str(e)}")

def get_best_move_keras(board: chess.Board, ai_info: dict) -> Optional[chess.Move]:
    try:
        model = load_custom_light_model()
        if not model:
            logger.error("Keras model not loaded")
            return None
        input_data = board_to_input(board, ai_info["path"])
        predictions = model.predict(input_data)
        return predictions_to_move(predictions, board, "custom_light")
    except Exception as e:
        logger.error(f"Keras model error: {str(e)}")
        return None
