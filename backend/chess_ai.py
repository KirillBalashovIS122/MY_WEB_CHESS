import logging
import os
import chess
import chess.engine
import numpy as np
import tensorflow as tf
from typing import Optional
from ais import available_ais
import random

logger = logging.getLogger(__name__)

custom_light_model = None

def load_custom_light_model():
    global custom_light_model
    if custom_light_model is None:
        from tensorflow import keras
        logger.debug("Загрузка модели custom_light при старте")
        model = keras.models.load_model("models/light_model.keras")
        custom_light_model = ChessAIModel(model)
    return custom_light_model

class ChessAIModel:
    def __init__(self, model):
        self.model = model
    
    @tf.function(reduce_retracing=True)
    def predict(self, input_data):
        return self.model(input_data, training=False)

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
    
    logger.debug(f"Входной тензор для {ai_name}: shape={tensor.shape}")
    logger.debug(f"Пример значений тензора: {tensor[0, :, :, 0]} (пешки белых)")
    return tensor

def predictions_to_move(predictions, board: chess.Board, ai_name: str) -> Optional[chess.Move]:
    legal_moves = list(board.legal_moves)
    if not legal_moves:
        logger.warning("Нет допустимых ходов")
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
                logger.warning("Все вероятности нулевые, выбираем случайный ход")
                return random.choice(legal_moves)
            best_move = max(move_scores.items(), key=lambda x: x[1])[0]
            logger.debug(f"Лучший ход: {best_move.uci()} (score: {move_scores[best_move]:.4f})")
            return best_move
        else:
            logger.error(f"Неверный формат предсказаний: {type(predictions)}")
            return random.choice(legal_moves)
    return None

async def get_best_move(board: chess.Board, ai_name: str, depth: int = 3, skill_level: int = 20) -> Optional[chess.Move]:
    logger.debug(f"Запрос лучшего хода для ИИ: {ai_name}")
    ai_info = available_ais.get(ai_name)
    if not ai_info:
        logger.error(f"ИИ {ai_name} не найден")
        return None

    try:
        if ai_info["type"] == "uci":
            return await get_best_move_uci(board, ai_info, depth, skill_level)
        elif ai_info["type"] == "keras":
            return get_best_move_keras(board, ai_info)
    except Exception as e:
        logger.error(f"Ошибка ИИ {ai_name}: {str(e)}")
        return None

async def get_best_move_uci(board: chess.Board, ai_info: dict, depth: int, skill_level: int) -> Optional[chess.Move]:
    try:
        logger.debug(f"Запуск UCI-движка: {ai_info['path']}")
        transport, engine = await chess.engine.popen_uci(ai_info["path"])
        
        if ai_info["path"].endswith("stockfish"):
            await engine.configure({"Skill Level": skill_level})
        
        result = await engine.play(
            board,
            chess.engine.Limit(depth=depth),
            info=chess.engine.INFO_ALL
        )
        
        await engine.quit()
        
        if result and result.move:
            logger.info(f"ИИ вернул ход: {result.move.uci()}")
            return result.move
        else:
            logger.warning("ИИ не вернул допустимый ход")
            return None
    except Exception as e:
        logger.error(f"Ошибка UCI-движка: {str(e)}")
        return None

def get_best_move_keras(board: chess.Board, ai_info: dict) -> Optional[chess.Move]:
    try:
        model = load_custom_light_model()
        input_data = board_to_input(board, ai_info["path"])
        predictions = model.predict(input_data)
        return predictions_to_move(predictions, board, "custom_light")
    except Exception as e:
        logger.error(f"Ошибка Keras модели: {str(e)}")
        return None
