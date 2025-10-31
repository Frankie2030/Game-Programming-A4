# GOMOKU

This folder contains the Assignment 4 starter for turning the Gomoku board game into a 3D-engine project.

Overview
- A small, engine-agnostic Python implementation of the Gomoku rules lives in `src/gomoku.py`.
- Unit tests are in `tests/test_gomoku.py` and use pytest. These help validate the rule engine before porting to a 3D engine.

Recommended tech stack

Primary: Godot 4 (GDScript)
- Lightweight, open-source, and fast to iterate. Use Godot scenes for the board and pieces. Port `src/gomoku.py` logic to a `Board.gd` script.

Alternative: Unity (C#)
- Use Unity if you prefer C# and the Unity Editor; port the Python logic into a `Gomoku.cs` game manager.

Web option: Three.js / Babylon.js + Node backend
- If you want browser demos, render the 3D board with Three.js and host multiplayer with a Node-based WebSocket server.

Files added
- `src/gomoku.py` — pure-Python Gomoku board & win detection (5-in-a-row)
- `tests/test_gomoku.py` — pytest unit tests covering win directions and edge cases

How to run tests

Create and activate a venv, then install pytest:

```bash
# macOS / zsh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pytest
```

Run tests from repo root:

```bash
pytest A4/tests -q
```

Next steps
- Pick an engine (Godot/Unity/Web). I can create a minimal Godot project skeleton and port the rule logic into GDScript next, or create a Unity C# skeleton if you prefer.

If you'd like the strict mapping to `Assignment4_Board_Game_Specs.pdf`, paste the PDF text or confirm key requirements (board size, AI, multiplayer, platform) and I'll adapt the stack and skeleton accordingly.

Enjoy — tell me which engine you want scaffolded and I'll continue.
# GOMOKU

