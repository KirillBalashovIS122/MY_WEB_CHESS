import React, { useState, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : '/api';

const ChessBoard = ({ gameId, gameState }) => {
  const [boardFen, setBoardFen] = useState('start');
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [possibleMoves, setPossibleMoves] = useState([]);

  useEffect(() => {
    if (gameState) {
      setBoardFen(gameState.board);
    }
  }, [gameState]);

  const onSquareClick = async (square) => {
    console.log(`Square clicked: ${square}, Selected: ${selectedSquare}`);
    
    if (!selectedSquare) {
      try {
        const response = await fetch(`${API_BASE_URL}/game/select?game_id=${gameId}&square=${square}`);
        if (!response.ok) throw new Error('Failed to select piece');
        const data = await response.json();
        console.log('Possible moves:', data.possible_moves);
        if (data.possible_moves.length > 0) {
          setSelectedSquare(square);
          setPossibleMoves(data.possible_moves);
        }
      } catch (error) {
        console.error('Error selecting piece:', error);
      }
    } else {
      const moveUci = `${selectedSquare}${square}`;
      console.log(`Attempting move: ${moveUci}`);
      if (!possibleMoves.includes(moveUci)) {
        console.log('Move not allowed, resetting selection');
        setSelectedSquare(null);
        setPossibleMoves([]);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/game/move`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            game_id: gameId, 
            from_square: selectedSquare, 
            to_square: square
          })
        });
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to make move');
        }
        const data = await response.json();
        console.log('Move successful:', data);
        setBoardFen(data.state.board);
        setSelectedSquare(null);
        setPossibleMoves([]);
      } catch (error) {
        console.error('Error making move:', error);
        alert(error.message);
        setSelectedSquare(null);
        setPossibleMoves([]);
      }
    }
  };

  const getCheckSquare = () => {
    if (!gameState || !gameState.board) return null;
    const chess = new Chess(gameState.board);
    if (!chess.isCheck()) return null;

    const turn = chess.turn();
    const board = chess.board();
    for (let row = 0; row < 8; row++) {
      for (let col = 0; col < 8; col++) {
        const piece = board[row][col];
        if (piece && piece.type === 'k' && piece.color === turn) {
          const file = String.fromCharCode(97 + col);
          const rank = 8 - row;
          return `${file}${rank}`;
        }
      }
    }
    return null;
  };

  const checkSquare = getCheckSquare();
  const squareStyles = {
    ...(selectedSquare
      ? {
          [selectedSquare]: { backgroundColor: 'rgba(76, 175, 80, 0.4)' },
          ...possibleMoves.reduce((acc, move) => {
            const toSquare = move.slice(2, 4);
            acc[toSquare] = {
              background: 'radial-gradient(circle, rgba(76, 175, 80, 0.7) 10%, transparent 10%)',
              backgroundSize: '100% 100%',
              backgroundPosition: 'center'
            };
            return acc;
          }, {})
        }
      : {}),
    ...(checkSquare ? { [checkSquare]: { backgroundColor: 'rgba(244, 67, 54, 0.4)' } } : {})
  };

  return (
    <div>
      <Chessboard
        position={boardFen}
        onSquareClick={onSquareClick}
        boardWidth={500}
        arePiecesDraggable={false}
        customSquareStyles={squareStyles}
      />
    </div>
  );
};

export default ChessBoard;