import React from 'react';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : '/api';

const PlayerInfo = ({ player, moves, playerNumber, gameId, gameMode }) => {
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

  const playerMoves = moves
    .map((move, index) => ({ move, index }))
    .filter(item => 
      playerNumber === 1 ? item.index % 2 === 0 : item.index % 2 === 1
    );

  return (
    <div className={`player-info player-${playerNumber}`}>
      <h3>{player}</h3>
      
      <div className="moves-container">
        {playerMoves.map((item, i) => (
          <div key={i} className="move-item">
            <span className="move-number">{Math.floor(item.index / 2) + 1}.</span>
            <span className="move-text">{item.move}</span>
          </div>
        ))}
      </div>
      
      {gameMode !== 'aivai' && (
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