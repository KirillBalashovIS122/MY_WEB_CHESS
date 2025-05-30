import pytest
import chess
import numpy as np
from unittest.mock import patch, AsyncMock
from backend.chess_ai import get_best_move, board_to_input, predictions_to_move, ChessAIModel

@pytest.mark.asyncio
async def test_get_best_move_stockfish():
    board = chess.Board()
    
    # Мокируем вызовы Stockfish
    with patch('chess.engine.popen_uci', new_callable=AsyncMock) as mock_popen:
        mock_engine = AsyncMock()
        mock_popen.return_value = (None, mock_engine)
        mock_engine.play.return_value = AsyncMock(move=chess.Move.from_uci("e2e4"))
        
        move = await get_best_move(board, "stockfish")
        assert move.uci() == "e2e4"

def test_board_to_input_shape(new_board):
    input_data = board_to_input(new_board, "custom_light")
    assert input_data.shape == (1, 8, 8, 14)

def test_predictions_to_move(new_board):
    # Создаем фиктивные предсказания
    from_probs = np.zeros((1, 64))
    to_probs = np.zeros((1, 64))
    
    # Устанавливаем высокую вероятность для хода e2e4
    from_square = chess.E2
    to_square = chess.E4
    from_probs[0][from_square] = 1.0
    to_probs[0][to_square] = 1.0
    
    move = predictions_to_move((from_probs, to_probs), new_board, "custom_light")
    assert move.uci() == "e2e4"

def test_chess_ai_model():
    # Создаем фиктивную модель TensorFlow
    class MockModel:
        def __call__(self, input_data):
            return [np.zeros((1, 64)), np.zeros((1, 64))]
    
    model = ChessAIModel(MockModel())
    predictions = model.predict(np.zeros((1, 8, 8, 14)))
    assert len(predictions) == 2