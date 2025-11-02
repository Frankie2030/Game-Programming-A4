# FLOW

## 🧩 1. Overall Execution Flow

### **Entry Point**

* **`main.py`** is the launcher.
* It initializes Pygame, sets up the UI state machine, loads or starts a new game, and invokes:

  ```python
  from game_ui import GameUI
  GameUI().run()
  ```
* The UI manages menus, game modes (AI vs Human, Online vs Local), and state transitions.

---

## 🕹️ 2. Core Game Logic

### **`gomoku_game.py`**

* Contains the **`GomokuGame`** class — represents the **game state** (board, current player, move legality, win/draw detection).
* Provides:

  * `make_move(row, col)`
  * `check_win()`
  * `is_valid_move()`
  * `get_legal_moves()`
  * `reset()`
* Tracks **turn order** and **board matrix**.
* Used by both AI and UI.

---

## 🧠 3. Artificial Intelligence

### **`ai_player.py`**

* Implements AI logic via **Minimax or Alpha–Beta pruning**.
* Contains:

  * Base `AIPlayer` class with interface for `choose_move(board_state)`.
  * `RandomAI` (random legal move baseline).
  * Possibly advanced AI like `MinimaxAI(depth=2)` or `ExpertAI(depth=4)` with heuristic evaluation.
* Used when you play against the computer.

---

## 🌐 4. Networking Layer

### **`stable_client.py`**

* Handles **client-side networking**.
* Connects to the server (local or remote, via `server_config.json`).
* Supports:

  * Joining or creating rooms.
  * Sending and receiving moves.
  * Synchronizing board state.
  * Graceful disconnects and reconnections.

### **`dedicated_server.py`**

* Runs the **authoritative server** for multiplayer games.
* Uses sockets (TCP or WebSocket) to:

  * Host matches.
  * Validate moves.
  * Broadcast game state to connected clients.
  * Handle lobby and disconnections.

### **`lobby_manager.py`**

* Provides a **matchmaking and lobby system**.
* Handles:

  * Listing rooms.
  * Creating rooms.
  * Player ready status.

### **`server_config.py`**

* Loads configuration from **`server_configs.json`**.
* Supports multiple server types:

  * Localhost.
  * Local Network.
  * AWS Lambda / Azure Functions (for cloud-based multiplayer).

---

## 🎨 5. User Interface & State Machine

### **`game_ui.py`**

* Manages **visual rendering and input** using Pygame.
* Defines UI states:

  * Main Menu
  * Game Mode Select
  * AI Difficulty Select
  * Network Setup
  * Lobby
  * Gameplay
  * Game Over
  * Pause
  * Continue
* Handles:

  * Button clicks, mouse events.
  * Drawing board grid and stones.
  * Rendering game over messages.
  * Saving/resuming via **`saved_game.json`**.

### **`game_states.py`**

* Defines **state management logic** and enums for game phases.
* Used by `game_ui.py` to transition between menu → gameplay → game over → continue.

---

## 💾 6. Persistence & Config

### **`saved_game.json`**

* Stores snapshot of:

  ```json
  {
    "board": [[...]],
    "current_player": 1,
    "move_history": [...],
    "game_mode": "ai_game",
    "ai_difficulty": "expert"
  }
  ```
* Enables the “Continue” feature to restore previous progress.

### **`server_configs.json`**

* Defines network environments:

  * Local Development
  * Local Network
  * AWS Lambda
  * Azure Functions

---

## 🐳 7. Deployment

### **`Dockerfile` + `DOCKER.md`**

* Provides containerized setup to run:

  * Game server (`dedicated_server.py`).
  * Or possibly the full game client if GUI libraries are supported.
* Likely exposes port `12345` (from configs).

### **`requirements.txt`**

* Includes dependencies like:

  ```
  pygame
  socketio
  requests
  json
  ```

  (Exact contents define whether it uses sockets, HTTP APIs, or WebSockets.)

---

## ⚙️ 8. Execution Summary

| Step | Action                    | Component                                    |
| ---- | ------------------------- | -------------------------------------------- |
| 1    | Run `python main.py`      | Starts UI (Pygame)                           |
| 2    | Choose mode (AI / Online) | `game_ui.py` & `gomoku_game.py`              |
| 3    | If AI mode                | `AIPlayer` selects moves                     |
| 4    | If online                 | `StableClient` connects to `DedicatedServer` |
| 5    | Gameplay loop             | Renders, checks for win/draw                 |
| 6    | Game over or Pause        | `saved_game.json` updated                    |
| 7    | Continue later            | Game restored from saved JSON                |
