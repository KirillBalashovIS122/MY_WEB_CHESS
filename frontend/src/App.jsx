import React, { useState, useEffect } from 'react';
import MainMenu from './components/MainMenu.jsx';
import PlayerNameModal from './components/PlayerNameModal.jsx';
import ChessBoard from './components/ChessBoard.jsx';
import PlayerInfo from './components/PlayerInfo.jsx';
import GameOverModal from './components/GameOverModal.jsx';
import './styles.css';

const App = () => {
  const [mode, setMode] = useState(null);
  const [gameId, setGameId] = useState(null);
  const [players, setPlayers] = useState({ player1: '', player2: '' });
  const [gameState, setGameState] = useState(null);

  const startGame = async (player1, player2) => {
    try {
      const response = await fetch(`http://localhost:8000/game/start?mode=${mode}&player1=${player1}&player2=${player2}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to start game');
      const data = await response.json();
      setGameId(data.game_id);
      setPlayers({ player1, player2 });
    } catch (error) {
      console.error('Error starting game:', error);
    }
  };

  useEffect(() => {
    if (gameId) {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`http://localhost:8000/game/state?game_id=${gameId}`);
          if (!response.ok) throw new Error('Failed to fetch game state');
          const data = await response.json();
          setGameState(data);
        } catch (error) {
          console.error('Error fetching game state:', error);
        }
      }, 1000);
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
      {gameState && (
        <>
          <PlayerInfo player={players.player1} moves={gameState.moves} />
          <ChessBoard gameId={gameId} />
          <PlayerInfo player={players.player2} moves={gameState.moves} />
          {gameState.game_over && (
            <GameOverModal
              winner={gameState.winner}
              onRestart={handleRestart}
              onExit={handleExit}
            />
          )}
        </>
      )}
    </div>
  );
};

export default App;