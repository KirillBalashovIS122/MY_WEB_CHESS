import React, { useState, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : '/api';

const ChessBoard = ({ gameId, gameState, onMove }) => {
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [possibleMoves, setPossibleMoves] = useState([]);
  const [promotionMove, setPromotionMove] = useState(null);

  const needPromotion = (fen, from, to) => {
    const chess = new Chess(fen);
    const move = {
      from,
      to,
      promotion: 'q'
    };
    return chess.moves(move).some(m => m.includes('='));
  };

  const handlePromotion = async (promotion) => {
    if (!promotionMove) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/game/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: gameId,
          from_square: promotionMove.from,
          to_square: promotionMove.to,
          promotion
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Move failed');
      }
      const data = await response.json();
      onMove(data.state);
      setSelectedSquare(null);
      setPossibleMoves([]);
      setPromotionMove(null);
    } catch (error) {
      console.error('Error making move:', error);
      alert(error.message);
      setSelectedSquare(null);
      setPossibleMoves([]);
      setPromotionMove(null);
    }
  };

  const PromotionDialog = () => (
    <div className="promotion-dialog">
      <h3>Выберите фигуру</h3>
      <div className="promotion-options">
        {['q', 'r', 'b', 'n'].map(piece => (
          <button key={piece} onClick={() => handlePromotion(piece)}>
            {piece.toUpperCase()}
          </button>
        ))}
      </div>
    </div>
  );

  const onSquareClick = async (square) => {
    if (promotionMove) return;

    if (gameState.game_over || gameState.ai_thinking || 
        (gameState.mode === 'pvai' && gameState.turn === 'black')) {
      return;
    }

    if (!selectedSquare) {
      const chess = new Chess(gameState.board);
      const piece = chess.get(square);
      if (!piece || (gameState.mode === 'pvai' && piece.color !== 'w')) {
        return;
      }
      try {
        const response = await fetch(`${API_BASE_URL}/api/game/select?game_id=${gameId}&square=${square}`);
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to select piece');
        }
        const data = await response.json();
        setSelectedSquare(square);
        setPossibleMoves(data.possible_moves);
      } catch (error) {
        console.error('Error selecting piece:', error);
        alert(error.message);
      }
    } else {
      if (needPromotion(gameState.board, selectedSquare, square)) {
        setPromotionMove({ from: selectedSquare, to: square });
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/game/move`, {
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
          throw new Error(error.detail || 'Move failed');
        }
        const data = await response.json();
        onMove(data.state);
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
    if (!gameState?.board) return null;
    const chess = new Chess(gameState.board);
    if (!chess.isCheck()) return null;

    const king = chess.board().flat().find(p => p?.type === 'k' && p.color === chess.turn());
    if (!king) return null;
    
    const file = String.fromCharCode(97 + king.square % 8);
    const rank = 8 - Math.floor(king.square / 8);
    return `${file}${rank}`;
  };

  const checkSquare = getCheckSquare();
  const squareStyles = {
    ...(selectedSquare ? {
      [selectedSquare]: { backgroundColor: 'rgba(76, 175, 80, 0.4)' },
      ...possibleMoves.reduce((acc, move) => {
        const toSquare = move.slice(2, 4);
        acc[toSquare] = {
          background: 'radial-gradient(circle, rgba(76,175,80,0.7) 25%, transparent 25%)',
          borderRadius: '50%'
        };
        return acc;
      }, {})
    } : {}),
    ...(checkSquare ? { [checkSquare]: { backgroundColor: 'rgba(244, 67, 54, 0.4)' } } : {})
  };

  return (
    <div className="chessboard-container">
      {promotionMove && <PromotionDialog />}
      {gameState.ai_thinking && <div className="ai-thinking">ИИ думает...</div>}
      <Chessboard
        position={gameState?.board || 'start'}
        onSquareClick={onSquareClick}
        customSquareStyles={squareStyles}
        boardWidth={500}
        arePiecesDraggable={false}
      />
    </div>
  );
};

export default ChessBoard;