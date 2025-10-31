# UI Testing Guide for 3D Gomoku

This guide walks you through launching and testing all UI components of the 3D Gomoku game.

## Quick Start Guide

### Prerequisites
- Godot Engine 4.x installed
- Python 3.11+ installed (for backend)
- Docker (optional, for containerized backend)

### 1. Launch Backend Server
```bash
# Option 1: Using Python directly
cd A4/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using Docker
cd A4
docker-compose up --build
```

### 2. Launch Game Client
```bash
cd A4/client
godot -e    # Opens Godot Editor
# Press F5 or click Play button (►) to run
```

## UI Testing Checklist

### Main Menu Testing
- [ ] Launch game client
- [ ] Verify main menu appears with:
  - "Single Player" button
  - "Multiplayer" button
  - "Settings" button
  - "Quit" button
- [ ] Check menu layout and theme
- [ ] Test button hover effects
- [ ] Verify text is readable and centered

### Single Player Flow
1. Click "Single Player"
2. Verify AI difficulty selection screen:
   - [ ] Easy option
   - [ ] Medium option
   - [ ] Hard option
   - [ ] Back button
3. Select difficulty:
   - [ ] Game board appears
   - [ ] 3D camera positioned correctly
   - [ ] Player pieces (black) ready
   - [ ] AI opponent (white) responsive

### Multiplayer Flow
1. Start two game instances:
```bash
# Terminal 1 - First player
cd A4/client
godot --position 0,0

# Terminal 2 - Second player
cd A4/client
godot --position 1280,0
```

2. Host Game (First Player):
   - [ ] Click "Multiplayer"
   - [ ] Click "Host Game"
   - [ ] Verify room code appears
   - [ ] Wait for opponent message shown

3. Join Game (Second Player):
   - [ ] Click "Multiplayer"
   - [ ] Click "Join Game"
   - [ ] Enter room code
   - [ ] Connection confirmation appears

### In-Game UI Elements
1. Game Board:
   - [ ] 3D grid visible
   - [ ] Board properly centered
   - [ ] Grid lines clear and visible
   - [ ] Hover effect on valid moves

2. Player Information:
   - [ ] Current player indicator
   - [ ] Game status messages
   - [ ] Score/move counter (if applicable)
   - [ ] Player colors clearly distinguished

3. Camera Controls:
   - [ ] Middle mouse button - rotate camera
   - [ ] Mouse wheel - zoom in/out
   - [ ] Camera limits working
   - [ ] Smooth transitions

4. Chat System (Multiplayer):
   - [ ] Chat window visible
   - [ ] Can type messages
   - [ ] Messages appear for both players
   - [ ] Scroll works for long conversations

### Settings Menu
1. Access Settings:
   - [ ] Click "Settings" from main menu
   - [ ] Settings panel appears

2. Check Options:
   - [ ] Volume controls
   - [ ] Graphics settings
   - [ ] Network settings (if applicable)
   - [ ] Changes are saved when applied

### Error Handling
Test these scenarios:
1. Network Disconnection:
   - [ ] Error message appears
   - [ ] Reconnection option shown
   - [ ] Can return to main menu

2. Invalid Room Code:
   - [ ] Error message shown
   - [ ] Can retry
   - [ ] Can go back

3. Server Unavailable:
   - [ ] Clear error message
   - [ ] Retry option
   - [ ] Offline mode or exit options

## Visual Verification

### Theme Consistency
- [ ] Colors match theme
- [ ] Font sizes readable
- [ ] Button styles consistent
- [ ] Spacing and alignment correct

### Animations
- [ ] Menu transitions smooth
- [ ] Piece placement animations
- [ ] Victory/defeat animations
- [ ] Loading indicators

### Responsiveness
- [ ] UI scales with window
- [ ] Text remains readable
- [ ] Buttons remain clickable
- [ ] No overlapping elements

## Troubleshooting

### Common Issues

1. UI Not Appearing:
```bash
# Check Godot project settings
cd A4/client
cat project.godot  # Verify main_scene setting

# Verify scene files exist
ls scenes/main_menu.tscn
ls scenes/game.tscn
```

2. Theme Not Loading:
```bash
# Check theme location
ls assets/theme/default_theme.tres

# Verify theme is set in project
grep -r "theme" project.godot
```

3. Buttons Not Responding:
- Open scene in editor
- Check Node tab for signal connections
- Verify scripts attached

### Quick Fixes

1. Reset UI State:
```bash
# Delete temporary files
rm -rf .godot/
# Restart Godot
godot -e
```

2. Refresh Resources:
- In Godot Editor: Project → Reload Current Project

3. Clear Cache:
```bash
# Remove cached files
rm -rf .import/
# Reimport assets
godot --build-solutions
```

## Development Tools

### Scene Testing
Test specific scenes directly:
```bash
# Test main menu
godot --main-scene scenes/main_menu.tscn

# Test game board
godot --main-scene scenes/game.tscn

# Test with specific mode
godot --main-scene scenes/game.tscn --mode single-player
```

### Debug Mode
Enable debug overlay:
```bash
# Run with debug overlay
godot --debug-collisions --visible-collision-shapes
```

### Performance Testing
Monitor UI performance:
```bash
# Run with monitoring
godot --debug-fps --print-fps
```

## Additional Testing Notes

### Cross-Resolution Testing
Test on different window sizes:
```bash
# Test specific resolution
godot --resolution 1920x1080

# Test windowed mode
godot --windowed
```

### Input Testing
- Mouse interaction
- Keyboard shortcuts
- Touch input (if applicable)
- Gamepad support (if implemented)

### Accessibility
- [ ] Color contrast sufficient
- [ ] Text size adjustable
- [ ] Audio feedback present
- [ ] Navigation logical

## Next Steps

After completing UI testing:
1. Report any issues found
2. Document any UI improvements needed
3. Test with different user scenarios
4. Verify against design specifications

Need help with specific tests or encountering issues? Please provide the exact scenario and any error messages for further assistance.
