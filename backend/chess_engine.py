import chess

def create_board():
    """Создает новую шахматную доску."""
    return chess.Board()

def is_game_over(board: chess.Board):
    """Проверяет, завершена ли игра."""
    return board.is_game_over()

def get_legal_moves(board: chess.Board, square: str = None):
    """Возвращает список допустимых ходов для указанной клетки или всей доски."""
    if square:
        try:
            square = chess.parse_square(square)
            return [move.uci() for move in board.legal_moves if move.from_square == square]
        except ValueError:
            return []
    return [move.uci() for move in board.legal_moves]

def make_move(board: chess.Board, move: str):
    """Делает ход на доске. Возвращает True, если ход успешен."""
    try:
        move_obj = chess.Move.from_uci(move)
        if move_obj in board.legal_moves:
            board.push(move_obj)
            return True
        return False
    except ValueError:
        return False

def get_game_result(board: chess.Board):
    """Возвращает результат игры."""
    if not board.is_game_over():
        return None
    return board.result()
