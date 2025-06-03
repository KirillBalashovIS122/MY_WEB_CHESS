
import chess
from typing import Tuple, Optional

def create_board() -> chess.Board:
    """Создаёт новую шахматную доску с начальной позицией."""
    return chess.Board()

def is_game_over(board: chess.Board) -> bool:
    """Проверяет, завершена ли игра."""
    return board.is_game_over()

def get_legal_moves(board: chess.Board, square: str = None) -> list:
    """Возвращает список допустимых ходов для указанной клетки или всей доски."""
    if square:
        try:
            square_idx = chess.parse_square(square)
            return [move for move in board.legal_moves if move.from_square == square_idx]
        except ValueError:
            return []
    return list(board.legal_moves)

def make_move(board: chess.Board, move: str) -> Tuple[bool, Optional[chess.Piece]]:
    """Выполняет ход на доске, возвращая успех и взятую фигуру."""
    try:
        move_obj = chess.Move.from_uci(move)
        if move_obj not in board.legal_moves:
            return False, None
        captured_piece = board.piece_at(move_obj.to_square)
        board.push(move_obj)
        return True, captured_piece
    except ValueError:
        return False, None

def get_game_result(board: chess.Board) -> str:
    """Возвращает результат завершённой игры."""
    if board.is_game_over():
        return board.result()
    return None
