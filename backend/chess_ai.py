import chess
import chess.engine
import asyncio

async def get_best_move(board: chess.Board, use_model: bool = False):
    if use_model:
        print("Custom model not implemented")
        return None
    try:
        engine = chess.engine.SimpleEngine.popen_uci("/usr/bin/stockfish")
        try:
            result = await engine.play(board, chess.engine.Limit(depth=3))
            print(f"Stockfish move: {result.move.uci()}")
            return result.move
        finally:
            await engine.quit()
    except Exception as e:
        print(f"Stockfish error: {str(e)}")
        return None
