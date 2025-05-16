import React, { useState, useEffect } from 'react';
import MainMenu from './components/MainMenu.jsx';
import PlayerNameModal from './components/PlayerNameModal.jsx';
import ChessBoard from './components/ChessBoard.jsx';
import PlayerInfo from './components/PlayerInfo.jsx';
import GameOverModal from './components/GameOverModal.jsx';
import './styles.css';

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : '/api';

const App = () => {
  const [mode, setMode] = useState(null);
  const [gameId, setGameId] = useState(null);
  const [players, setPlayers] = useState({ player1: '', player2: '' });
  const [gameState, setGameState] = useState(null);

  const startGame = async (player1, aiModelOrPlayer2) => {
    try {
      const body = {
        mode: mode,
        player1: player1,
        ...(mode === 'pvp' ? { player2: aiModelOrPlayer2 } : {}),
        ...(mode === 'pvai' ? { 
          ai_config: {
            use_stockfish: aiModelOrPlayer2 === 'stockfish',
            model: aiModelOrPlayer2 !== 'stockfish' ? aiModelOrPlayer2 : null
          }
        } : {})
      };

      const response = await fetch(`${API_BASE_URL}/api/game/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Ошибка сервера");
      }
      
      const data = await response.json();
      setGameId(data.game_id);
      setPlayers({ 
        player1, 
        player2: mode === 'pvp' ? aiModelOrPlayer2 : 'AI' 
      });
      setGameState(null);
    } catch (error) {
      alert(error.message);
      console.error('Error starting game:', error);
    }
  };

  useEffect(() => {
    if (gameId) {
      const fetchState = async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/game/state?game_id=${gameId}`);
          if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Ошибка сервера");
          }
          const data = await response.json();
          setGameState(data);
          console.log('Game state updated:', data);
        } catch (error) {
          console.error('Error fetching game state:', error);
        }
      };
      
      fetchState();
      const interval = setInterval(fetchState, 1000);
      return () => clearInterval(interval);
    }
  }, [gameId]);

  const handleRestart = () => {
    setGameId(null);
    setGameState(null);
  };

  const handleExit = () => {
    setMode(null);
    setGameId(null);
    setGameState(null);
  };

  if (!mode) {
    return <MainMenu onSelectMode={setMode} />;
  }
  if (!gameId) {
    return <PlayerNameModal mode={mode} onSubmit={startGame} />;
  }
  return (
    <div className="game-container">
      {gameState ? (
        <>
          <div className="turn-indicator">
            Ход: {gameState.turn === 'white' ? 'Белые' : 'Чёрные'}
          </div>
          <PlayerInfo player={players.player1} moves={gameState.moves} playerNumber={1} gameId={gameId} />
          <div className="board-container">
            <ChessBoard gameId={gameId} gameState={gameState} onMove={setGameState} />
          </div>
          <PlayerInfo player={players.player2} moves={gameState.moves} playerNumber={2} gameId={gameId} />
          {gameState.game_over && (
            <GameOverModal
              winner={gameState.winner}
              onRestart={handleRestart}
              onExit={handleExit}
            />
          )}
        </>
      ) : (
        <div>Loading game...</div>
      )}
    </div>
  );
};

export default App;