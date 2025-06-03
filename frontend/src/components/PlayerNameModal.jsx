import React, { useState } from 'react';

const PlayerNameModal = ({ mode, onSubmit }) => {
  const [player1, setPlayer1] = useState('');
  const [player2, setPlayer2] = useState('');
  const [aiWhite, setAiWhite] = useState('light');
  const [aiBlack, setAiBlack] = useState('light');

  const handleSubmit = () => {
    const aiMap = {
      light: 'custom_light',
      medium: 'numfish',
      heavy: 'stockfish'
    };

    const config = {
      mode,
      player1: mode === 'pvp' ? player1 : (mode === 'pvai' ? player1 : 'ИИ Белые'),
      player2: mode === 'pvp' ? player2 : (mode === 'pvai' ? 'ИИ' : 'ИИ Чёрные'),
      ai_white: mode === 'aivai' ? aiMap[aiWhite] : null,
      ai_black: mode !== 'pvp' ? aiMap[aiBlack] : null
    };

    onSubmit(config);
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Настройка игры</h2>

        {mode === 'pvp' && (
          <>
            <input
              type="text"
              placeholder="Игрок 1 (Белые)"
              value={player1}
              onChange={(e) => setPlayer1(e.target.value)}
            />
            <input
              type="text"
              placeholder="Игрок 2 (Чёрные)"
              value={player2}
              onChange={(e) => setPlayer2(e.target.value)}
            />
          </>
        )}

        {mode === 'pvai' && (
          <input
            type="text"
            placeholder="Ваше имя"
            value={player1}
            onChange={(e) => setPlayer1(e.target.value)}
          />
        )}

        {mode !== 'pvp' && (
          <div className="ai-selection">
            {mode === 'aivai' && (
              <div className="ai-option">
                <h3>ИИ за белых:</h3>
                <select value={aiWhite} onChange={(e) => setAiWhite(e.target.value)}>
                  <option value="light">Легкий</option>
                  <option value="medium">Средний</option>
                  <option value="heavy">Тяжелый</option>
                </select>
              </div>
            )}

            <div className="ai-option">
              <h3>ИИ за чёрных:</h3>
              <select value={aiBlack} onChange={(e) => setAiBlack(e.target.value)}>
                <option value="light">Легкий</option>
                <option value="medium">Средний</option>
                <option value="heavy">Тяжелый</option>
              </select>
            </div>
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={
            (mode === 'pvai' && !player1.trim()) ||
            (mode === 'pvp' && (!player1.trim() || !player2.trim()))
          }
        >
          Начать игру
        </button>
      </div>
    </div>
  );
};

export default PlayerNameModal;