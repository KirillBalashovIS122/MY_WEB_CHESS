import React from 'react';

const GameOverModal = ({ winner, onRestart, onExit }) => {
  const getMessage = () => {
    if (winner === "Ничья") {
      return "Игра завершилась вничью!";
    }
    return `${winner} побеждает!`;
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>Игра завершена</h2>
        <p className="winner-message">{getMessage()}</p>
        
        <div className="modal-buttons">
          <button 
            className="rematch-button"
            onClick={onRestart}
          >
            Реванш
          </button>
          
          <button 
            className="exit-button"
            onClick={onExit}
          >
            В главное меню
          </button>
        </div>
      </div>
    </div>
  );
};

export default GameOverModal;