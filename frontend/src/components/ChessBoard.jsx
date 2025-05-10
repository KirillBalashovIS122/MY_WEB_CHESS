import React, { useState, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';

const ChessBoard = ({ gameId }) => {
  const [boardFen, setBoardFen] = useState('start');
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [possibleMoves, setPossibleMoves] = useState([]);

  useEffect(() => {
    const fetchState = async () => {
      try {
        const response = await fetch(`http://localhost:8000/game/state?game_id=${gameId}`);
        if (!response.ok) throw new Error('Failed to fetch game state');
        const data = await response.json();
        setBoardFen(data.board);
      } catch (error) {
        console.error('Error fetching game state:', error);
      }
    };
    fetchState();
  }, [gameId]);

  const onSquareClick = async (square) => {
    if (!selectedSquare) {
      try {
        const response = await fetch(`http://localhost:8000/game/select?game_id=${gameId}&square=${square}`);
        if (!response.ok) throw new Error('Failed to select piece');
        const data = await response.json();
        setSelectedSquare(square);
        setPossibleMoves(data.possible_moves);
      } catch (error) {
        console.error('Error selecting piece:', error);
      }
    } else {
      try {
        const response = await fetch(`http://localhost:8000/game/move`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ game_id: gameId, from_square: selectedSquare, to_square: square })
        });
        if (!response.ok) throw new Error('Failed to make move');
        const data = await response.json();
        setBoardFen(data.state.board);
        setSelectedSquare(null);
        setPossibleMoves([]);
      } catch (error) {
        console.error('Error making move:', error);
      }
    }
  };

  return (
    <div>
      <Chessboard
        position={boardFen}
        onSquareClick={onSquareClick}
        boardWidth={500}
      />
    </div>
  );
};

export default ChessBoard;