import React from 'react';
import '../styles.css';

const GameOverModal = ({ winner, onRestart, onExit }) => (
  <div className="modal">
    <div className="modal-content">
      <h2>{winner ? `${winner} выиграл!` : 'Ничья!'}</h2>
      <button onClick={onRestart}>Реванш</button>
      <button onClick={onExit}>Выход</button>
    </div>
  </div>
);

export default GameOverModal;