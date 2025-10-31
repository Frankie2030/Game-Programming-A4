# Local Testing Guide for 3D Multiplayer Gomoku

This guide will help you set up and test all features of the 3D Multiplayer Gomoku game locally. We'll go through each requirement from the checklist and verify its functionality.

## Prerequisites

- Python 3.11 or higher
- Godot 4.x
- Docker and Docker Compose (optional, for containerized backend)
- Git (for version control)

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd A4
```

2. Start the backend server (choose one method):

   **Using Python directly:**
   ```bash
   # Install dependencies
   pip install -r backend/requirements.txt
   
   # Start the server
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   **Using Docker:**
   ```bash
   docker-compose up --build
   ```

3. Launch the Godot client:
   - Open Godot 4.x
   - Import the project from the `client` folder
   - Click the "Play" button or press F5

## Feature Testing Guide

### I. Game Concept & Rules

1. **Basic Game Rules**
   - Start a single-player game against AI
   - Place stones alternately (black first)
   - Verify win condition by getting 5 in a row
   - Try placing stones on occupied spots (should be blocked)
   - Test board boundaries

2. **Win Conditions**
   - Test horizontal win
   - Test vertical win
   - Test diagonal win
   - Test draw condition (full board)

### II. Artificial Intelligence

1. **Random AI (Easy Mode)**
   - Start game vs AI
   - Select "Easy" difficulty
   - Verify AI makes legal moves
   - Check response time (should be immediate)

2. **Minimax/Alpha-Beta AI (Medium Mode)**
   - Select "Medium" difficulty
   - Verify AI blocks winning moves
   - Check strategic play
   - Observe pruning in debug logs

3. **MCTS AI (Hard Mode)**
   - Select "Hard" difficulty
   - Test AI strength
   - Verify improved performance vs Medium
   - Check thinking time (~3 seconds)

### III. Networking Features

1. **Connection Testing**
   - Start two game instances
   - Host game on first instance
   - Join game on second instance using code
   - Verify connection establishment

2. **Multiplayer Gameplay**
   - Test turn alternation
   - Verify move synchronization
   - Test illegal move prevention
   - Use chat system

3. **Error Handling**
   - Test disconnection handling
   - Close one client and verify other client's response
   - Test reconnection
   - Try invalid moves and malformed inputs

### IV. Menu System & Save States

1. **Menu Navigation**
   - Test all menu buttons
   - Verify transitions
   - Check settings persistence
   - Test game mode selection

2. **Save/Load System**
   - Start a game
   - Make some moves
   - Save the game
   - Load the game in a new session
   - Verify state restoration

## Visual Features

1. **3D Board**
   - Check board rendering
   - Verify grid lines
   - Test stone materials
   - Check lighting and shadows

2. **Camera Controls**
   - Test rotation (middle mouse button)
   - Test zoom (mouse wheel)
   - Verify camera limits
   - Check smooth transitions

3. **UI Elements**
   - Verify turn indicators
   - Check move highlights
   - Test chat window
   - Verify message displays

## Testing Checklist

- [ ] Core game rules work correctly
- [ ] All three AI difficulties are distinct
- [ ] Multiplayer connectivity works
- [ ] Game state synchronizes properly
- [ ] Menu system functions correctly
- [ ] Save/Load system works
- [ ] 3D visualization is correct
- [ ] Camera controls are smooth
- [ ] UI is responsive and clear

## Troubleshooting

### Backend Issues
```bash
# Check backend logs
docker-compose logs -f

# Restart backend
docker-compose restart

# Clean start
docker-compose down
docker-compose up --build
```

### Client Issues
- Check Godot output window for errors
- Verify WebSocket connection in browser dev tools
- Check file permissions for save games

## Development

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_gomoku.py
pytest tests/test_ai.py
pytest tests/test_backend.py
```

### Environment Variables
The backend supports different environments through .env files:
- `.env.development` for development
- `.env.production` for production

### Directory Structure
```
A4/
├── backend/              # FastAPI server
├── client/              # Godot project
│   ├── scenes/          # Game scenes
│   ├── scripts/         # GDScript code
│   └── assets/          # 3D models, textures
├── src/                 # Shared game logic
├── tests/               # Test suite
└── docker-compose.yml   # Container configuration
```

## Performance Optimization

If you experience performance issues:

1. **Backend:**
   - Adjust AI thinking time in .env file
   - Modify WebSocket message frequency
   - Tune connection limits

2. **Client:**
   - Lower shadow quality in settings
   - Reduce particle effects
   - Adjust camera smooth factor

## Contributing

1. Create a feature branch
2. Make changes
3. Run tests
4. Submit pull request

## License

This project is licensed under the MIT License.
