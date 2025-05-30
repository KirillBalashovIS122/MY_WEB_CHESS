import chess
import pytest
from backend.chess_engine import create_board, is_game_over, get_legal_moves, make_move, get_game_result

def test_create_board():
    board = create_board()
    assert board.fen() == chess.STARTING_FEN

def test_is_game_over_initial(new_board):
    assert not is_game_over(new_board)

def test_is_game_over_checkmate():
    board = chess.Board("8/8/8/8/8/8/6k1/6RK b - - 0 1")
    assert is_game_over(board)

def test_get_legal_moves_initial_count(new_board):
    moves = get_legal_moves(new_board)
    assert len(moves) == 20  # 20 возможных ходов в начальной позиции

def test_get_legal_moves_for_square(new_board):
    moves = get_legal_moves(new_board, "e2")
    assert "e4" in moves or "e3" in moves

def test_make_move_valid(new_board):
    assert make_move(new_board, "e2e4")
    assert new_board.fen() == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"

def test_make_move_invalid(new_board):
    assert not make_move(new_board, "e2e5")  # недопустимый ход

def test_get_game_result_ongoing(new_board):
    assert get_game_result(new_board) is None

def test_get_game_result_white_wins():
    board = chess.Board("8/8/8/8/8/8/6k1/6RK b - - 0 1")
    assert get_game_result(board) == "1-0"