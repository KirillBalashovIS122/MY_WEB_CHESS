import React, { useState } from 'react';
import '../styles.css';

const PlayerNameModal = ({ mode, onSubmit }) => {
  const [player1, setPlayer1] = useState('');
  const [player2, setPlayer2] = useState('');

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Введите имена игроков</h2>
        <input
          type="text"
          placeholder="Игрок 1"
          value={player1}
          onChange={(e) => setPlayer1(e.target.value)}
        />
        {mode === 'pvp' && (
          <input
            type="text"
            placeholder="Игрок 2"
            value={player2}
            onChange={(e) => setPlayer2(e.target.value)}
          />
        )}
        <button onClick={() => onSubmit(player1, mode === 'pvp' ? player2 : 'AI')}>
          Начать игру
        </button>
      </div>
    </div>
  );
};

export default PlayerNameModal;