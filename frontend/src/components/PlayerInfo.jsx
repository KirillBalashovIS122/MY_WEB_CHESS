import React, { useMemo } from 'react';
import '../styles.css';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : '/api';

const PlayerInfo = ({ player, moves, playerNumber, gameId, gameMode, capturedPieces, opponentCapturedPieces }) => {
  const handleSurrender = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/game/surrender`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          game_id: gameId, 
          player: playerNumber 
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Ошибка при сдаче');
      }
    } catch (error) {
      alert(error.message);
    }
  };

  const isAI = (gameMode === 'pvai' && playerNumber === 2) || gameMode === 'aivai';

  const pieceImages = {
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛',
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕'
  };

  const pieceValues = {
    'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9,
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9
  };

  // Рассчитываем общий перевес (не отрицательный)
  const materialAdvantage = useMemo(() => {
    const capturedValue = capturedPieces.reduce(
      (sum, piece) => sum + (pieceValues[piece] || 0), 0
    );
    const opponentCapturedValue = opponentCapturedPieces.reduce(
      (sum, piece) => sum + (pieceValues[piece] || 0), 0
    );
    return Math.max(0, capturedValue - opponentCapturedValue);
  }, [capturedPieces, opponentCapturedPieces]);

  const renderCapturedPieces = () => {
    return capturedPieces.map((piece, index) => (
      <span key={index} className="captured-piece">
        <span className={`piece-${piece}`}>
          {piece}
          {pieceImages[piece]}
        </span>
      </span>
    ));
  };

  const groupedMoves = [];
  for (let i = 0; i < moves.length; i += 2) {
    groupedMoves.push({
      white: moves[i],
      black: moves[i + 1] || ''
    });
  }

  return (
    <div className={`player-info player-${playerNumber}`}>
      <div className="player-header">
        <h3>{player} ({materialAdvantage > 0 ? `+${materialAdvantage}` : materialAdvantage})</h3>
      </div>
      
      <div className="captured-pieces">
        {renderCapturedPieces()}
      </div>
      
      <div className="moves-container">
        {groupedMoves.map((movePair, index) => (
          <div key={index} className="move-item">
            <span className="move-number">{index + 1}.</span>
            <span className="move-text">{movePair.white}</span>
            <span className="move-text">{movePair.black}</span>
          </div>
        ))}
      </div>
      
      {!isAI && (
        <button 
          className="surrender-button" 
          onClick={handleSurrender}
        >
          Сдаться
        </button>
      )}
    </div>
  );
};

export default PlayerInfo;