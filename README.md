# Gomoku - Five in a Row

A complete implementation of the classic Gomoku board game with AI opponents and online multiplayer support, built with Python and Pygame.

## Team Members - Group 6

| **Student Name** | **Student ID** |
|------------------|----------------|
| Nguyễn Ngọc Khôi | 2252378 |
| Nguyễn Quang Phú | 2252621 |
| Nguyễn Tấn Bảo Lễ | 2252428 |
| Nguyễn Minh Khôi | 2252377 |

## Overview

This project implements Gomoku (also known as Five in a Row or Connect Five) as part of Assignment 4 for the Game Programming course. The game features multiple play modes, intelligent AI opponents, and network multiplayer capabilities.

**Key Features**

- **Multiple Game Modes**: Local PvP, Player vs AI, Online multiplayer
- **Intelligent AI**: Minimax algorithm with Alpha-Beta pruning and real-time debugging
- **Difficulty Levels**: Easy, Medium, Hard, and Expert AI opponents
- **Network Play**: Host or join online games with other players
- **Save/Resume**: Complete save and load functionality
- **Modern UI**: Clean, intuitive interface with background images and visual effects
- **Sound System**: Sound effects for moves, game start, and winner announcements
- **Background Music**: Ambient background music that loops during gameplay
- **AI Debug Viewer**: Real-time visualization of AI thinking process (press 'D' key)
- **Advanced Features**: Pause/resume, turn timers, resign functionality

## Installation & Setup

Prerequisites: Python 3.7+; Pygame library

1. **Clone or download the project**
   ```bash
   git clone <link>
   cd A4
   ```

2. **Install dependencies**
   ```bash
   pip install pygame
   ```

3. **Run the game**
   ```bash
   python main.py
   ```

## How to Play

### Rules
1. Objective
   - Players take turns placing stones (Black goes first).
   - The goal is to be the first to form an unbroken line of exactly five stones horizontally, vertically, or diagonally.
2. Winning Condition
   - A player wins immediately when they create a line of five stones in a row.
   - The line may be either: open at one end, open at both ends, or blocked at one or both ends.
   - Lines of 6 or more (overlines) also count as a victory.
3. Board
   - The standard board is 15×15 cells (commonly used in competitive play).
4. Notes
   - You cannot move or remove stones already placed.
   - You cannot place on an occupied intersection.
5. Draw Conditions
   - A game may end in a draw only if both players agree, or the board is completely full with no five-in-a-row for either player.

### Start the game

1. **Launch the application**
   ```bash
   python main.py
   ```

2. **Main Menu Options**:
   - **New Game**: Start a fresh game
   - **Continue**: Resume a saved game (if available)
   - **Settings**: Adjust game preferences
   - **Quit**: Exit the application

### Game Modes

#### 1. Player vs AI
- Human player (Black) vs Computer opponent (White)
- Choose from 4 difficulty levels:
  - **Easy**: Depth 3, basic evaluation (~1K-3K nodes/move)
  - **Medium**: Depth 5, smart move selection (~5K-20K nodes/move)
  - **Hard**: Depth 7, advanced pruning (~20K-100K nodes/move)
  - **Expert**: Depth 9, maximum strength (~50K-500K nodes/move)

#### 2. Multi-player Mode

The game supports online multiplayer through a dedicated server system with configurable server endpoints. It includes a server configuration system that supports multiple deployment targets:

- **Local Development**: `localhost:12345` (default)
- **Local Network**: `0.0.0.0:12345` (accessible from other devices)
- **AWS Lambda**: For serverless deployment on AWS
- **Azure Functions**: For serverless deployment on Azure
- **Custom Servers**: Any custom server endpoint

Server configurations are stored in `server_configs.json` and can be managed through the UI.

**Step 1: Start Dedicated Server**
```bash
python main.py --server
```

or:

```bash
python main.py
# Select "New Game" → "Host Network Game"
# This creates a server and waits for connections
```

**Step 2: Connect Players**
```bash
python main.py
# Select "New Game" → "Join Network Game"
# Connects to the host's server (localhost, AWS, Azure, etc.)
# Enter your player name
# Browse available rooms or create a new one
# Wait for another player to join
# Game starts automatically when room is full
```

** Key Features:**

- The server supports multiple concurrent games
- Room creator becomes Black player (goes first). Room joiner becomes White player (goes second)
- **Manual Save**: Use Pause menu → Save Game
- **Quick Save**: Automatic save on exit (if enabled)
- **Auto Save**: Periodic saves during gameplay (if enabled)
- **Continue**: Resume most recent save from main menu
- **Load Game**: Select specific save file (future feature)


### Controls
- **Mouse Click**: Place stone on board intersection
- **Pause Button**: Pause game and access menu
- **Resign Button**: Forfeit current game
- **'D' Key**: Toggle AI debug viewer (AI games only)
- **ESC**: Pause game
- **D**: Toggle AI debug information panel (shows real-time thinking)
- **Ctrl+S**: Quick save (when available)


## AI Implementation

The AI opponent uses the **Minimax algorithm with Alpha-Beta pruning & Iterative deepening**. Minimax is an algorithm classic adversarial search algorithm that assumes both players play optimally. The algorithm recursively explores the game tree to find the best move. The harder the difficulty, the more time taken by the AI (to think).

**Difficulty Levels & Node Expansion**

| Difficulty | Max Depth | Time Limit | Candidates | Typical Nodes Evaluated |
|------------|-----------|------------|------------|------------------------|
| **Easy** | 3 | 2.0s | 25 | 1,000 - 3,000 nodes |
| **Medium** | 5 | 5.0s | 45 | 5,000 - 20,000 nodes |
| **Hard** | 7 | 8.0s | 55 | 20,000 - 100,000 nodes |
| **Expert** | 9 | 15.0s | 70 | 50,000 - 500,000 nodes |


### AI Statistics & Debugging

Press **'D'** during AI gameplay to see real-time statistics:
- **Nodes Evaluated**: Total positions examined
- **Search Depth**: Maximum depth reached in search tree
- **Pruning Count**: Number of branches pruned
- **Pruning Efficiency**: Percentage of branches eliminated
- **Search Time**: Time taken for current move
- **Nodes per Second**: Search speed metric
- **Nodes by Depth**: Distribution of nodes across depths
- **Move Evaluations**: Scores for all candidate moves

This feature helps you understand:
- How the AI evaluates positions
- Which moves are being considered
- How alpha-beta pruning reduces search space
- Why the AI chooses specific moves


## Network Architecture

The multiplayer system uses a reliable TCP-based client-server architecture.

### Server Features
- **Connection Management**: Handle multiple client connections
- **Game State Synchronization**: Authoritative game state
- **Move Validation**: Server-side move checking
- **Disconnect Handling**: Graceful connection management

### Client Features
- **Real-time Communication**: Low-latency move transmission
- **State Synchronization**: Automatic board updates
- **Reconnection Support**: Handle temporary disconnections

## File Structure

```
A4/
├── main.py                 # Main entry point
├── README.md              # This file
├── REQUIREMENTS_CHECKLIST.md  # Requirements tracking
├── server_configs.json     # Network server configurations
├── src/                    # Source code
│   ├── gomoku_game.py      # Core game logic
│   ├── ai_player.py        # AI implementation with debug stats
│   ├── ai_validator.py     # AI testing utilities
│   ├── stable_client.py    # Network client implementation
│   ├── dedicated_server.py # Standalone game server
│   ├── lobby_manager.py    # Lobby and room management
│   ├── server_config.py    # Server configuration management
│   ├── game_ui.py          # Pygame user interface
│   ├── game_states.py      # Save/load system
│   ├── sounds/             # Sound effects
│   │   ├── board-start-38127.mp3
│   │   ├── calm-nature-sounds-196258.mp3
│   │   ├── play_turn.mp3
│   │   └── winner-game-sound-404167.mp3
│   └── imgs/               # Background images
│       ├── image_game.webp
│       └── image_start.jpg
├── saved_game.json         # Current saved game (if exists)
└── requirements.txt       # Python dependencies
```

## License

This project is developed for educational purposes as part of the Game Programming course. All rights reserved by the development team.