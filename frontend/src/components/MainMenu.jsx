import React from 'react';
import '../styles.css';

const MainMenu = ({ onSelectMode }) => (
  <div className="game-menu-container">
    <h1 className="main-title">ШАХМАТЫ</h1>
    <div className="game-buttons">
      <button onClick={() => onSelectMode('pvp')}>ИГРОК ПРОТИВ ИГРОКА</button>
      <button onClick={() => onSelectMode('pvai')}>ИГРОК ПРОТИВ ИИ</button>
      <button onClick={() => onSelectMode('aivai')}>ИИ ПРОТИВ ИИ</button>
    </div>
  </div>
);

export default MainMenu;