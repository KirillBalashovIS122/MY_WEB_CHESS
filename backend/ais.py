available_ais = {
    "stockfish": {"type": "uci", "path": "/usr/games/stockfish"},
    "custom_light": {"type": "keras", "path": "models/light_model.keras"},
    "numfish": {
        "type": "uci", 
        "command": ["python3", "/app/backend/engines/numbfish/numbfish.py"]
    }
}