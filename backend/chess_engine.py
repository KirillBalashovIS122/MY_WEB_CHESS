import chess

def create_board() -> chess.Board:
    """Создает новую шахматную доску с начальной позицией."""
    return chess.Board()

def is_game_over(board: chess.Board) -> bool:
    """Проверяет, завершена ли игра."""
    return board.is_game_over()

def get_legal_moves(board: chess.Board, square: str = None) -> list:
    """Возвращает допустимые ходы для указанной клетки или всей доски."""
    if square:
        try:
            square_idx = chess.parse_square(square)
            return [move for move in board.legal_moves if move.from_square == square_idx]
        except ValueError:
            return []
    return list(board.legal_moves)

def make_move(board: chess.Board, move: str) -> bool:
    """Выполняет ход на доске. Возвращает True при успехе."""
    try:
        move_obj = chess.Move.from_uci(move)
        if move_obj in board.legal_moves:
            board.push(move_obj)
            return True
        return False
    except ValueError:
        return False

def get_game_result(board: chess.Board) -> str:
    """Возвращает результат завершенной игры."""
    if board.is_game_over():
        return board.result()
    return None