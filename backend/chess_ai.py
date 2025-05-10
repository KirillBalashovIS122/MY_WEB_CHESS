import chess
import chess.engine
import asyncio

async def get_best_move(board: chess.Board, use_custom_model: bool = False):
    """Возвращает лучший ход для текущей позиции."""
    if use_custom_model:
        # TODO: Интеграция с custom_model.h5 (ваша модель)
        # Пример: загрузка модели и предсказание хода
        # import tensorflow as tf
        # model = tf.keras.models.load_model('models/custom_model.h5')
        # move = predict_move(board, model)
        return None  # Заглушка
    else:
        # Используем Stockfish
        try:
            engine = chess.engine.SimpleEngine.popen_uci("/usr/bin/stockfish")
            result = await engine.play(board, chess.engine.Limit(time=0.1))
            await engine.quit()
            return result.move
        except Exception as e:
            print(f"Stockfish error: {e}")
            return None