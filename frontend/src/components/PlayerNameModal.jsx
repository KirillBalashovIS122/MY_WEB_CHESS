import React, { useState } from 'react';
import '../styles.css';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : '/api';

const PlayerNameModal = ({ mode, onSubmit }) => {
  const [player1, setPlayer1] = useState('');
  const [player2, setPlayer2] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('light');

  const handleSubmit = () => {
    const aiName = {
      light: 'custom_light',
      medium: 'numfish',
      heavy: 'stockfish'
    }[selectedDifficulty];
    
    const gameConfig = {
      mode,
      player1: mode === 'pvp' ? player1 : (mode === 'pvai' ? player1 : 'ИИ Белые'),
      player2: mode === 'pvp' ? player2 : (mode === 'pvai' ? 'ИИ' : 'ИИ Чёрные'),
      ai_name: mode !== 'pvp' ? aiName : undefined
    };

    console.log('Отправка конфигурации игры:', gameConfig);
    
    if (mode === 'pvp' && (!player1.trim() || !player2.trim())) {
      alert('Введите имена обоих игроков');
      return;
    }
    if (mode === 'pvai' && !player1.trim()) {
      alert('Введите ваше имя');
      return;
    }
    
    onSubmit(gameConfig);
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Настройка игры</h2>
        {mode === 'pvp' && (
          <>
            <input
              type="text"
              placeholder="Игрок 1"
              value={player1}
              onChange={(e) => setPlayer1(e.target.value)}
            />
            <input
              type="text"
              placeholder="Игрок 2"
              value={player2}
              onChange={(e) => setPlayer2(e.target.value)}
            />
          </>
        )}
        {mode !== 'pvp' && (
          <>
            {mode === 'pvai' && (
              <input
                type="text"
                placeholder="Ваше имя"
                value={player1}
                onChange={(e) => setPlayer1(e.target.value)}
              />
            )}
            <div className="difficulty-selector">
              <h3>Выберите сложность:</h3>
              <div className="difficulty-buttons">
                <button
                  type="button"
                  onClick={() => setSelectedDifficulty('light')}
                  className={selectedDifficulty === 'light' ? 'selected' : ''}
                >
                  Легкий
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedDifficulty('medium')}
                  className={selectedDifficulty === 'medium' ? 'selected' : ''}
                >
                  Средний
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedDifficulty('heavy')}
                  className={selectedDifficulty === 'heavy' ? 'selected' : ''}
                >
                  Тяжелый
                </button>
              </div>
            </div>
          </>
        )}
        <button onClick={handleSubmit} disabled={(mode === 'pvai' && !player1.trim()) || (mode === 'pvp' && (!player1.trim() || !player2.trim()))}>
          Начать игру
        </button>
      </div>
    </div>
  );
};

export default PlayerNameModal;