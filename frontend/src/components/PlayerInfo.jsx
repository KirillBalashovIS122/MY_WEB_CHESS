import React from 'react';
import '../styles.css';

const PlayerInfo = ({ player, moves }) => (
  <div className="player-info">
    <h3>{player}</h3>
    <ul>{moves.map((move, i) => <li key={i}>{move}</li>)}</ul>
  </div>
);

export default PlayerInfo;