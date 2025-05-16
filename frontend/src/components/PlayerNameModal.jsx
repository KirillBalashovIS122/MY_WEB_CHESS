import React, { useState, useEffect } from 'react';
import '../styles.css';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : '/api';

const PlayerNameModal = ({ mode, onSubmit }) => {
  const [player1, setPlayer1] = useState('');
  const [player2, setPlayer2] = useState('');
  const [selectedModel, setSelectedModel] = useState('stockfish');
  const [availableModels, setAvailableModels] = useState(['stockfish']);

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/ai/models`);
        if (response.ok) {
          const data = await response.json();
          setAvailableModels(['stockfish', ...data.models]);
        }
      } catch (error) {
        console.error('Error fetching models:', error);
      }
    };
    
    if (mode === 'pvai') fetchModels();
  }, [mode]);

  const handleSubmit = () => {
    if (mode === 'pvai') {
      onSubmit(player1, selectedModel);
    } else {
      onSubmit(player1, player2);
    }
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Настройка игры</h2>
        <input
          type="text"
          placeholder="Ваше имя"
          value={player1}
          onChange={(e) => setPlayer1(e.target.value)}
          required
        />
        
        {mode === 'pvp' && (
          <input
            type="text"
            placeholder="Игрок 2"
            value={player2}
            onChange={(e) => setPlayer2(e.target.value)}
          />
        )}

        {mode === 'pvai' && (
          <div className="model-selector">
            <h3>Выберите модель ИИ:</h3>
            <div className="model-buttons">
              {availableModels.map(model => (
                <button
                  key={model}
                  type="button"
                  onClick={() => setSelectedModel(model)}
                  className={selectedModel === model ? 'selected' : ''}
                >
                  {model.replace('.h5', '')}
                </button>
              ))}
            </div>
          </div>
        )}

        <button onClick={handleSubmit} disabled={!player1.trim()}>
          Начать игру
        </button>
      </div>
    </div>
  );
};

export default PlayerNameModal;