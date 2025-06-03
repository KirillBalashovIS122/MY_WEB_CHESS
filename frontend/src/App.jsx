import React, { useState, useEffect } from 'react';
import MainMenu from './components/MainMenu';
import PlayerNameModal from './components/PlayerNameModal';
import ChessBoard from './components/ChessBoard';
import PlayerInfo from './components/PlayerInfo';
import GameOverModal from './components/GameOverModal';
import './styles.css';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : '/api';

const App = () => {
  const [mode, setMode] = useState(null);
  const [gameId, setGameId] = useState(null);
  const [players, setPlayers] = useState({ player1: '', player2: '' });
  const [gameState, setGameState] = useState(null);
  const [gameScore, setGameScore] = useState("0 - 0");
  const [lastConfig, setLastConfig] = useState(null);
  const [playerScores, setPlayerScores] = useState({ player1: 0, player2: 0, draws: 0 });

  const startGame = async (config) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/game/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Ошибка сервера");
      }
      
      const data = await response.json();
      setGameId(data.game_id);
      setPlayers({ 
        player1: config.player1, 
        player2: data.player2 
      });
      setGameState(null);
      setGameScore("0 - 0");
      setLastConfig(config);
      setPlayerScores({ player1: 0, player2: 0, draws: 0 }); // Сброс счёта только при новой сессии
    } catch (error) {
      alert(error.message);
    }
  };

  const fetchGameScore = async () => {
    if (!gameId) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/game/score?game_id=${gameId}`);
      if (!response.ok) return;
      
      const data = await response.json();
      setGameScore(data.score);
      
      if (data.scores) {
        setPlayerScores({
          player1: data.scores[data.player1].wins || 0,
          player2: data.scores[data.player2].wins || 0,
          draws: data.scores[data.player1].draws || 0
        });
      }
    } catch (error) {
      console.error('Ошибка при получении счета:', error);
    }
  };

  useEffect(() => {
    if (gameId) {
      const fetchState = async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/game/state?game_id=${gameId}`);
          if (!response.ok) return;
          
          const data = await response.json();
          setGameState(data);
        } catch (error) {
          console.error('Ошибка при получении состояния игры:', error);
        }
      };
      
      fetchState();
      fetchGameScore();
      const interval = setInterval(fetchState, 1000);
      return () => clearInterval(interval);
    }
  }, [gameId]);

  const handleRestart = () => {
    if (lastConfig) {
      startGame(lastConfig); // Счёт не сбрасывается, сохраняется через game_scores
    }
  };

  const handleExit = async () => {
    if (mode === 'aivai' && gameId) {
      try {
        await fetch(`${API_BASE_URL}/api/game/stop`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ game_id: gameId })
        });
      } catch (error) {
        console.error('Ошибка при остановке игры:', error);
      }
    }
    
    setMode(null);
    setGameId(null);
    setGameState(null);
    setPlayerScores({ player1: 0, player2: 0, draws: 0 }); // Сброс счёта при выходе
  };

  if (!mode) {
    return <MainMenu onSelectMode={setMode} />;
  }
  if (!gameId) {
    return <PlayerNameModal mode={mode} onSubmit={startGame} />;
  }
  
  return (
    <div className="game-container">
      <div className="game-header">
        <div className="score-board">
          {playerScores.player1} - {playerScores.player2}
          {playerScores.draws > 0 && ` (${playerScores.draws} ничьих)`}
        </div>
        
        <button 
          className="exit-button"
          onClick={handleExit}
        >
          Выход
        </button>
      </div>

      <div className="game-content">
        <PlayerInfo 
          player={players.player1} 
          moves={gameState?.moves || []} 
          playerNumber={1} 
          gameId={gameId} 
          gameMode={mode}
          capturedPieces={gameState?.captured_by_player1 || []}
          opponentCapturedPieces={gameState?.captured_by_player2 || []}
        />
        
        <div className="board-container">
          {gameState && (
            <>
              <div className="turn-indicator">
                Ход: {gameState.turn === 'белые' ? 'Белые' : 'Чёрные'}
              </div>
              <ChessBoard gameId={gameId} gameState={gameState} onMove={setGameState} />
            </>
          )}
        </div>
        
        <PlayerInfo 
          player={players.player2} 
          moves={gameState?.moves || []} 
          playerNumber={2} 
          gameId={gameId} 
          gameMode={mode}
          capturedPieces={gameState?.captured_by_player2 || []}
          opponentCapturedPieces={gameState?.captured_by_player1 || []}
        />
      </div>

      {gameState?.game_over && (
        <GameOverModal
          winner={gameState.winner}
          onRestart={handleRestart}
          onExit={handleExit}
        />
      )}
    </div>
  );
};

export default App;