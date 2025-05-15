import React from 'react';
import '../styles.css';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : '/api';

const PlayerInfo = ({ player, moves, playerNumber, gameId }) => {
  const handleSurrender = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/game/surrender`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_id: gameId, player: playerNumber })
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to surrender');
      }
      console.log('Surrender successful');
    } catch (error) {
      console.error('Error surrendering:', error);
      alert(error.message);
    }
  };

  const playerMoves = moves.filter((_, index) => 
    playerNumber === 1 ? index % 2 === 0 : index % 2 !== 0
  );

  const displayMoves = playerNumber === 2 ? [...playerMoves].reverse() : playerMoves;

  return (
    <div className={`player-info player-${playerNumber}`}>
      <h3>{player}</h3>
      <ul>
        {displayMoves.map((move, i) => (
          <li key={i}>
            {Math.floor((playerNumber === 1 ? i : playerMoves.length - 1 - i) / 2) + 1}. {move}
          </li>
        ))}
      </ul>
      <button className="surrender-button" onClick={handleSurrender}>
        Сдаться
      </button>
    </div>
  );
};

export default PlayerInfo;