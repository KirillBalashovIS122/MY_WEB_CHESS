import chess
import chess.engine
import numpy as np
import asyncio
from tensorflow.keras.models import load_model

PIECE_MAP = {
    'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6,
    'p': -1, 'n': -2, 'b': -3, 'r': -4, 'q': -5, 'k': -6
}

def board_to_matrix(board):
    matrix = np.zeros((8, 8, 12), dtype=np.float32)
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            row = 7 - (square // 8)
            col = square % 8
            layer = PIECE_MAP[piece.symbol()] + 5
            matrix[row, col, layer] = 1.0
    return matrix

async def get_best_move(board: chess.Board, use_model: bool = True):
    if use_model:
        try:
            model = load_model('models/custom_model.h5')
            input_data = board_to_matrix(board)
            predictions = model.predict(np.array([input_data]))
            
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return None
                
            move_scores = []
            for move in legal_moves:
                from_row = 7 - (move.from_square // 8)
                from_col = move.from_square % 8
                to_row = 7 - (move.to_square // 8)
                to_col = move.to_square % 8
                score = predictions[0, from_row, from_col, to_row, to_col]
                move_scores.append((move, score))
            
            return max(move_scores, key=lambda x: x[1])[0]
        except Exception as e:
            print(f"Model error: {e}")
    
    try:
        engine = chess.engine.SimpleEngine.popen_uci("/usr/bin/stockfish")
        result = await engine.play(board, chess.engine.Limit(time=0.1))
        await engine.quit()
        return result.move
    except Exception as e:
        print(f"Stockfish error: {e}")
        return None
