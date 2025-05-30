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
            print(f"Move {move} applied successfully. New board state: {board.fen()}")  # Добавлено для отладки
            return True
        print(f"Move {move} is not legal.")  # Добавлено для отладки
        return False
    except ValueError as e:
        print(f"Invalid move {move}: {str(e)}")  # Добавлено для отладки
        return False

def get_game_result(board: chess.Board):
    """Возвращает результат игры."""
    if not board.is_game_over():
        return None
    return board.result()
