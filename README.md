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

### Key Features

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

## Game Rules

### Objective
Be the first player to get exactly **5 stones in a row** (horizontally, vertically, or diagonally) on a 15×15 board.

### Gameplay
1. **Turn Order**: Black (X) always plays first, then White (O)
2. **Placing Stones**: Players alternate placing stones on empty intersections
3. **Winning**: First player to achieve 5 consecutive stones wins
4. **Draw**: Game ends in draw if board is full with no winner

### Win Conditions
- **5 in a row**: Horizontal, vertical, or diagonal
- **No overlines**: Exactly 5 stones (not 6 or more)
- **No captures**: Stones cannot be removed once placed

### Legal Moves
- Stones must be placed on empty intersections
- No moves allowed outside the 15×15 board
- No moves allowed after game ends

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- Pygame library

### Installation Steps

1. **Clone or download the project**
   ```bash
   cd A4
   ```

2. **Install dependencies**
   ```bash
   pip install pygame
   ```
   
   Or if you have the requirements file:
   ```bash
   pip install -r ../requirements.txt
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

### Starting the Game

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

#### 1. Local Player vs Player
- Two human players take turns on the same computer
- Black player goes first
- Click on the board to place stones

#### 2. Player vs AI
- Human player (Black) vs Computer opponent (White)
- Choose from 4 difficulty levels:
  - **Easy**: Depth 3, basic evaluation (~1K-3K nodes/move)
  - **Medium**: Depth 5, smart move selection (~5K-20K nodes/move)
  - **Hard**: Depth 7, advanced pruning (~20K-100K nodes/move)
  - **Expert**: Depth 9, maximum strength (~50K-500K nodes/move)

**AI Debug Viewer** (Press 'D' during gameplay):
- Real-time display of AI thinking process
- Shows nodes evaluated, pruning count, search depth
- Displays move evaluations with scores as AI thinks
- Visualizes best move found so far
- See how alpha-beta pruning works in real-time

---

## AI Implementation Details

### Algorithm: Minimax with Alpha-Beta Pruning

The AI opponent uses the **Minimax algorithm with Alpha-Beta pruning**, a classic adversarial search algorithm that assumes both players play optimally. The algorithm recursively explores the game tree to find the best move.

#### Core Algorithm Components

1. **Minimax Search**
   - Explores game tree by simulating both players' moves
   - Maximizing player (AI) tries to maximize score
   - Minimizing player (opponent) tries to minimize score
   - Returns the best move based on evaluation scores

2. **Alpha-Beta Pruning**
   - Optimization technique that eliminates unnecessary branches
   - Maintains alpha (best MAX score) and beta (best MIN score)
   - Prunes branches where beta ≤ alpha (no better move possible)
   - **Reduces nodes evaluated by ~60-80%** in typical games

3. **Iterative Deepening**
   - Starts search at depth 1, gradually increases depth
   - Allows time management (stops when time limit reached)
   - Ensures AI always has a valid move (best from completed depth)
   - Better move ordering improves pruning efficiency

4. **Smart Move Selection**
   - Generates candidate moves near existing stones (within 1 square)
   - Reduces branching factor from ~225 to ~30-50 moves
   - Orders moves by static evaluation for better pruning
   - Critical for performance in deeper searches

#### Difficulty Levels & Node Expansion

| Difficulty | Max Depth | Time Limit | Candidates | Typical Nodes Evaluated |
|------------|-----------|------------|------------|------------------------|
| **Easy** | 3 | 2.0s | 25 | 1,000 - 3,000 nodes |
| **Medium** | 5 | 5.0s | 45 | 5,000 - 20,000 nodes |
| **Hard** | 7 | 8.0s | 55 | 20,000 - 100,000 nodes |
| **Expert** | 9 | 15.0s | 70 | 50,000 - 500,000 nodes |

**Node Expansion Capacity**:
- **Easy**: ~25 × 30² = **~22,500 theoretical** (minimal pruning, ~2K actual)
- **Medium**: ~45 × 40⁴ = **~115M theoretical** (heavy pruning, ~15K actual)
- **Hard**: ~55 × 40⁶ = **~2.3T theoretical** (heavy pruning, ~60K actual)
- **Expert**: ~70 × 40⁸ = **~460T theoretical** (heavy pruning, ~300K actual)

*Note: Actual nodes evaluated are much lower due to alpha-beta pruning (60-80% reduction) and time limits.*

#### Position Evaluation Heuristic

The AI evaluates board positions using an **advanced pattern-based scoring system** with tactical awareness:

```python
def evaluate_position(board, player):
    score = 0
    
    # Pattern Recognition for EXISTING stones:
    for each stone on board:
        for each direction:
            analyze_consecutive_pattern()
            
            # Scoring for existing patterns:
            # Five in a row: +50,000 (instant win)
            # Open four: +10,000 (unstoppable threat)
            # Four (one end): +5,000 (strong threat)
            # Open three: +2,000 (can become open four)
            # Three (one end): +500 (moderate threat)
            # Open two: +100 (building position)
            # Single stone: +2 (minimal value)
    
    # Potential Analysis for EMPTY positions:
    for each empty position:
        simulate_placing_stone()
        
        # Scoring for potential moves:
        # Would make five: +100,000 (winning move!)
        # Would make four: +50,000 (critical move)
        # Would make open three: +5,000 (strong move)
        # Would make three: +1,000 (good move)
        # Would make open two: +500 (developing move)
        # Would make two: +100 (useful move)
    
    # Defensive weighting: opponent threats × 1.1
    return score(AI) - score(opponent) × 1.1
```

**Key Improvements**:
- **Dual Evaluation**: Analyzes both existing patterns AND potential moves
- **Open-End Detection**: Distinguishes between open and blocked formations
- **Defensive Priority**: Weights opponent threats 1.3x-2.0x based on severity
  - Normal positions: ×1.3
  - Strong threats (open three): ×1.8
  - Critical threats (open four): ×2.0
- **Threat Recognition**: Identifies forcing moves (open fours, open threes)
- **Strategic Depth**: Evaluates long-term positional value
- **Critical Block Detection**: Pre-scans for opponent winning moves and prioritizes blocking them

#### Performance Optimizations

1. **Move Ordering**
   - Evaluates all candidate moves at root level
   - Sorts by score before minimax search
   - Best moves evaluated first → more pruning
   - **Critical Blocks Prioritized**: Detects opponent winning threats and checks blocking moves first

2. **Defensive Threat Detection**
   - Scans for opponent winning moves before search
   - Prioritizes blocking critical threats
   - Weighted defense: opponent threats × 1.3-2.0 depending on severity
   - **Immediate threat response**: Open fours and winning moves blocked first

3. **Enhanced Evaluation Weighting**
   - Normal play: Opponent score × 1.3
   - Strong threats (open three+): Opponent score × 1.8
   - Critical threats (open four+): Opponent score × 2.0
   - Ensures AI always blocks winning moves

#### AI Statistics & Debugging

Press **'D'** during AI games to view real-time statistics:

- **Nodes Evaluated**: Total positions examined
- **Search Depth**: Maximum depth reached in search tree
- **Pruning Count**: Number of branches pruned
- **Pruning Efficiency**: Percentage of branches eliminated
- **Search Time**: Time taken for current move
- **Nodes per Second**: Search speed metric
- **Nodes by Depth**: Distribution of nodes across depths
- **Move Evaluations**: Scores for all candidate moves

**Example Output**:
```
AI Statistics (Expert):
  Nodes Evaluated: 142,538
  Search Depth: 8
  Pruning Count: 89,241 (62.6%)
  Search Time: 4.2s
  Nodes/Second: 33,937
  
Move Evaluations:
  (7,7) → +850
  (7,8) → +720
  (8,7) → +650
  ...
```

#### 3. Network Multiplayer

The game supports online multiplayer through a dedicated server system with configurable server endpoints.

##### Server Configuration System

The game includes a server configuration system that supports multiple deployment targets:

- **Local Development**: `localhost:12345` (default)
- **Local Network**: `0.0.0.0:12345` (accessible from other devices)
- **AWS Lambda**: For serverless deployment on AWS
- **Azure Functions**: For serverless deployment on Azure
- **Custom Servers**: Any custom server endpoint

Server configurations are stored in `server_configs.json` and can be managed through the UI.

##### How to Play Online

**Step 1: Start Dedicated Server**
```bash
python main.py --server
```

**Step 2: Connect Players**
```bash
python main.py
```
- Select "Network Game" from the main menu
- Choose your server (localhost, AWS, Azure, etc.)
- Enter your player name
- Browse available rooms or create a new one
- Wait for another player to join
- Game starts automatically when room is full

##### Multiple Players Support

- The server supports multiple concurrent games
- Each room accommodates exactly 2 players
- Room creator becomes Black player (goes first)
- Room joiner becomes White player (goes second)
- Players can view games side-by-side with the smaller window size (800x600)

##### Method 2: Direct Host-Client Connection

**Step 1: Host Player**
```bash
python main.py
# Select "New Game" → "Host Network Game"
# This creates a server and waits for connections
```

**Step 2: Joining Player**
```bash
python main.py
# Select "New Game" → "Join Network Game"
# Connects to the host's server
```

### Controls

#### During Gameplay
- **Mouse Click**: Place stone on board intersection
- **Pause Button**: Pause game and access menu
- **Resign Button**: Forfeit current game
- **'D' Key**: Toggle AI debug viewer (AI games only)

#### Keyboard Shortcuts
- **ESC**: Pause game
- **D**: Toggle AI debug information panel (shows real-time thinking)
- **Ctrl+S**: Quick save (when available)

### Save & Resume System

#### Saving Games
- **Manual Save**: Use Pause menu → Save Game
- **Quick Save**: Automatic save on exit (if enabled)
- **Auto Save**: Periodic saves during gameplay (if enabled)

#### Loading Games
- **Continue**: Resume most recent save from main menu
- **Load Game**: Select specific save file (future feature)

## AI Implementation

### Algorithm: Minimax with Alpha-Beta Pruning

The AI uses the classic Minimax algorithm enhanced with Alpha-Beta pruning for efficient search.

#### Core Components

1. **Position Evaluation**
   - Analyzes potential winning patterns in all directions
   - Scores based on consecutive stones (1, 2, 3, 4+ in a row)
   - Considers blocking opponent threats
   - Evaluates both offensive and defensive potential
   - Scoring system:
     - 4+ in a row: 1000 points (winning move)
     - 3 unblocked: 100 points
     - 3 blocked: 10 points
     - 2 unblocked: 10 points
     - 2 blocked: 2 points
     - 1 stone: 1 point

2. **Search Strategy**
   - Iterative deepening for time management
   - Smart move ordering for better pruning
   - Focused search on promising areas (moves near existing stones)
   - Real-time statistics tracking

3. **Difficulty Scaling**
   ```python
   Difficulty Settings:
   - Easy:   Depth 2, 1s time limit, random move sampling
   - Medium: Depth 4, 3s time limit, smart moves only
   - Hard:   Depth 6, 5s time limit, full evaluation
   - Expert: Depth 8, 10s time limit, maximum search
   ```

#### Performance Characteristics
- **Easy**: ~100-500 nodes/second, makes obvious mistakes
- **Medium**: ~1000-2000 nodes/second, solid tactical play
- **Hard**: ~2000-5000 nodes/second, strong strategic play
- **Expert**: ~5000+ nodes/second, near-optimal play

#### AI Debug Viewer

Press **'D'** during AI gameplay to see real-time thinking:

**Real-Time Display** (while AI is thinking):
- Current search depth
- Nodes evaluated so far
- Best move found with score
- Currently evaluating moves (shown with "→" indicator)
- Completed move evaluations with scores

**Final Statistics** (after AI moves):
- Total nodes evaluated
- Pruning count and efficiency percentage
- Maximum depth reached
- Search time and nodes per second
- Top 5 move evaluations with scores

This feature helps you understand:
- How the AI evaluates positions
- Which moves are being considered
- How alpha-beta pruning reduces search space
- Why the AI chooses specific moves

## Network Architecture

### Client-Server Model

The multiplayer system uses a reliable TCP-based client-server architecture.

#### Server Features
- **Connection Management**: Handle multiple client connections
- **Game State Synchronization**: Authoritative game state
- **Move Validation**: Server-side move checking
- **Disconnect Handling**: Graceful connection management

#### Client Features
- **Real-time Communication**: Low-latency move transmission
- **State Synchronization**: Automatic board updates
- **Reconnection Support**: Handle temporary disconnections

#### Message Protocol
```json
{
  "type": "move|game_state|chat|ping|pong",
  "timestamp": 1234567890.123,
  "data": {
    "row": 7,
    "col": 7,
    "player": 1
  }
}
```

### Network Setup Instructions

#### For Local Network Play

1. **Host Setup**:
   ```bash
   python main.py --server
   ```
   Server runs on `localhost:12345`

2. **Client Connection**:
   - Use "Join Network Game" in GUI
   - Or run: `python main.py --client`

#### For Internet Play

1. **Port Forwarding**: Forward port 12345 on router
2. **Firewall**: Allow Python through firewall
3. **IP Address**: Share public IP with other player
4. **Connection**: Other player connects to your public IP

#### Troubleshooting Network Issues

- **Connection Refused**: Check if server is running
- **Timeout**: Verify network connectivity and firewall
- **Lag**: Check network latency (game needs <200ms RTT)

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

## Technical Specifications

### Dependencies
- **Python**: 3.7+
- **Pygame**: 2.0+
- **Standard Library**: json, socket, threading, time

### Performance Requirements
- **RAM**: 50MB minimum
- **CPU**: Any modern processor
- **Network**: 56k modem sufficient for online play
- **Display**: 1000×700 minimum resolution

### Platform Support
- **Windows**: Full support
- **macOS**: Full support
- **Linux**: Full support

## Testing

### Running Tests
```bash
# Run basic functionality tests
python main.py --test

# Run specific test modules (future)
python -m pytest tests/
```

### Test Coverage
- ✅ Core game logic (moves, wins, draws)
- ✅ AI functionality (all difficulty levels)
- ✅ Save/load system
- ✅ Network communication basics
- ⏳ UI interaction tests (planned)
- ⏳ Stress testing (planned)

## Known Issues & Limitations

### Current Limitations
1. **Network Security**: Basic validation only, not production-ready
2. **AI Performance**: Expert level may be slow on older hardware
3. **Save Format**: JSON format, not optimized for large files
4. **UI Scaling**: Fixed resolution, not responsive

### Planned Improvements
- [ ] Spectator mode for network games
- [ ] Tournament bracket system
- [ ] AI vs AI demonstration mode
- [ ] Enhanced graphics and animations
- [ ] Replay system
- [ ] Online matchmaking
- [ ] Coordinate display option
- [ ] Move history viewer

## Development Notes

### Architecture Decisions

1. **Modular Design**: Separate concerns (game logic, AI, network, UI)
2. **State Management**: Centralized game state with clear interfaces
3. **Network Protocol**: JSON-based messages for simplicity
4. **AI Algorithm**: Minimax chosen for educational clarity

### Code Quality
- **Type Hints**: Used throughout for better maintainability
- **Documentation**: Comprehensive docstrings and comments
- **Error Handling**: Graceful degradation on failures
- **Testing**: Unit tests for core functionality

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Follow existing code style
4. Add tests for new features
5. Submit pull request

### Code Style Guidelines
- Follow PEP 8 Python style guide
- Use type hints for function signatures
- Document all public methods
- Keep functions focused and small

## License

This project is developed for educational purposes as part of the Game Programming course. All rights reserved by the development team.

## Support & Contact

For technical support or questions about the implementation:

1. **Course Forum**: Post questions in the course discussion forum
2. **Team Contact**: Reach out to any team member listed above
3. **Documentation**: Refer to inline code documentation

---

**Assignment 4 - Board Game (AI + Networking)**  
**Course**: CO3045 - Game Programming  
**Semester**: HK251  
**Team**: Group 6
Enjoy — tell me which engine you want scaffolded and I'll continue.
# Members - Group 6
| **Student name** | **Student ID** |
|-----|--------|
| Nguyễn Ngọc Khôi | 2252378 |
| Nguyễn Quang Phú | 2252621 |
| Nguyễn Tấn Bảo Lễ | 2252428 |
| Nguyễn Minh Khôi | 2252377 |
