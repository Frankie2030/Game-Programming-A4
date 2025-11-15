# AI Implementation

## Algorithm: Minimax with Alpha-Beta Pruning

The AI opponent uses the **Minimax algorithm with Alpha-Beta pruning**, a classic adversarial search algorithm that assumes both players play optimally. The algorithm recursively explores the game tree to find the best move.

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

## Difficulty Levels & Node Expansion

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

**Position Evaluation Heuristic**:

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

## Performance Optimizations

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

## AI Statistics & Debugging

Press **'D'** during AI gameplay to see real-time statistics:
- **Nodes Evaluated**: Total positions examined
- **Search Depth**: Maximum depth reached in search tree
- **Pruning Count**: Number of branches pruned
- **Pruning Efficiency**: Percentage of branches eliminated
- **Search Time**: Time taken for current move
- **Nodes per Second**: Search speed metric
- **Nodes by Depth**: Distribution of nodes across depths
- **Move Evaluations**: Scores for all candidate moves
- 
This feature helps you understand:
- How the AI evaluates positions
- Which moves are being considered
- How alpha-beta pruning reduces search space
- Why the AI chooses specific moves
- 

# Network Architecture

## Client-Server Model

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

### Message Protocol
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

## Network Setup Instructions

### For Local Network Play

1. **Host Setup**:
   ```bash
   python main.py --server
   ```
   Server runs on `localhost:12345`

2. **Client Connection**:
   - Use "Join Network Game" in GUI
   - Or run: `python main.py --client`

### For Internet Play

1. **Port Forwarding**: Forward port 12345 on router
2. **Firewall**: Allow Python through firewall
3. **IP Address**: Share public IP with other player
4. **Connection**: Other player connects to your public IP

### Troubleshooting Network Issues

- **Connection Refused**: Check if server is running
- **Timeout**: Verify network connectivity and firewall
- **Lag**: Check network latency (game needs <200ms RTT)

# File Structure

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


# Testing

```bash
# Run basic functionality tests
python main.py --test

# Run specific test modules (future)
python -m pytest tests/
```

### Planned Improvements
- [ ] Spectator mode for network games
- [ ] Tournament bracket system
- [ ] AI vs AI demonstration mode
- [ ] Enhanced graphics and animations
- [ ] Replay system
- [ ] Online matchmaking
- [ ] Coordinate display option
- [ ] Move history viewer