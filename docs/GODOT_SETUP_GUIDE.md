# Godot Setup Guide for 3D Gomoku

This guide will walk you through setting up Godot Engine for the 3D Gomoku game on both macOS and Windows systems.

## System Requirements

### macOS
- macOS 10.13 (High Sierra) or newer
- 8 GB RAM (16 GB recommended)
- OpenGL 3.3 compatible hardware
- 4 GB free disk space

### Windows
- Windows 7 SP1 or newer
- 8 GB RAM (16 GB recommended)
- OpenGL 3.3 or DirectX 11 compatible hardware
- 4 GB free disk space

## Installation Steps

### macOS Installation

1. **Using Homebrew (Recommended)**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Godot
brew install --cask godot
```

2. **Manual Installation**
- Visit the [Godot Downloads Page](https://godotengine.org/download)
- Download "Godot Engine" for macOS (x86_64 or ARM64 for M1/M2 Macs)
- Open the downloaded DMG file
- Drag Godot to your Applications folder
- First launch: Right-click Godot → Open to bypass security

3. **Command Line Setup (optional)**
```bash
# Add Godot to PATH (for bash/zsh)
echo 'export PATH="/Applications/Godot.app/Contents/MacOS:$PATH"' >> ~/.zshrc
# Or for bash
echo 'export PATH="/Applications/Godot.app/Contents/MacOS:$PATH"' >> ~/.bash_profile

# Reload shell configuration
source ~/.zshrc  # or source ~/.bash_profile
```

### Windows Installation

1. **Using winget (Windows Package Manager)**
```powershell
# Open PowerShell as Administrator and run:
winget install --id=GodotEngine.GodotEngine
```

2. **Manual Installation**
- Visit the [Godot Downloads Page](https://godotengine.org/download)
- Download "Godot Engine" for Windows (64-bit)
- Create a folder: `C:\Program Files\Godot`
- Extract the downloaded ZIP to this folder
- Create a desktop shortcut (optional)

3. **Add to PATH (optional)**
```powershell
# Open PowerShell as Administrator
$oldPath = [Environment]::GetEnvironmentVariable('Path', [EnvironmentVariableTarget]::Machine)
$newPath = $oldPath + ';C:\Program Files\Godot'
[Environment]::SetEnvironmentVariable('Path', $newPath, [EnvironmentVariableTarget]::Machine)
```

## Project Setup

## Development and Code Reloading

When modifying code during development, there are several ways to reload your changes:

1. **Automatic Reloading (While Running)**
   - Script changes are automatically reloaded when you save the file
   - Press F6 (or Fn+F6 on Mac) to reload all scripts
   - Use Ctrl+R (Cmd+R on Mac) to restart the current scene

2. **Manual Reloading**
   - If automatic reloading doesn't work, stop the game (F8)
   - Make your code changes
   - Save the file
   - Run the game again (F5)

3. **Force Recompilation**
   - If you experience any strange behavior
   - Go to Project > Tools > Reload Current Project
   - This will force Godot to recompile all scripts

Note: Some changes (like adding new nodes, changing scene structure) require a full scene reload to take effect.

### Opening the Project (Both Platforms)

1. **Clone the Repository**
```bash
# macOS Terminal or Windows PowerShell
git clone <repository-url>
cd HK251_Game-Programming/A4
```

2. **Launch Godot**
- Open Godot Engine
- Click "Import"
- Navigate to `A4/client`
- Click "Import & Edit"

### First-Time Setup Verification

1. **Verify Installation**
```bash
# Check Godot version
godot --version

# Expected output should be 4.x or newer
```

2. **Test Project Loading**
- Open Godot
- Click "Import"
- Select `A4/client/project.godot`
- Project should load without errors

3. **Run the Game**
- Press F5 or click Play button (►)
- Main menu should appear
- 3D graphics should render correctly

## Platform-Specific Settings

### macOS Settings

1. **Performance Settings**
```
Godot → Preferences → Display
- Enable Vsync: On
- Display FPS: Optional
```

2. **Security Settings**
- System Preferences → Security & Privacy
- Allow Godot in:
  - Privacy → Camera (if using)
  - Privacy → Microphone (if using)
  - Privacy → Full Disk Access (if needed)

3. **Graphics Settings**
```
Editor → Project → Project Settings → Display
- Window → Size → Viewport Width: 1280
- Window → Size → Viewport Height: 720
```

### Windows Settings

1. **Graphics Driver**
- Ensure latest GPU drivers are installed
- For NVIDIA: Use NVIDIA Control Panel
- For AMD: Use AMD Radeon Settings

2. **Performance Settings**
```
Editor → Editor Settings
- Enable Low Processor Usage Mode: Off
- Physics → Enable Frame Timer: On
```

3. **Windows Display Settings**
- Enable Game Mode: Optional
- Set Display scaling to 100%

## Troubleshooting

### Common Issues on macOS

1. **Godot Won't Open**
```bash
# Reset Godot preferences
rm -rf ~/Library/Application\ Support/Godot/
# For project-specific issues:
rm -rf .godot/
```

2. **Graphics Issues**
- Check System Preferences → Displays
- Disable automatic graphics switching
- Force discrete GPU if available

3. **Performance Issues**
```bash
# Clear derived data
rm -rf ~/Library/Caches/Godot/
# Reset project cache
rm -rf .import/
```

### Common Issues on Windows

1. **Missing DLL Errors**
- Install Visual C++ Redistributable
- Update DirectX
- Verify Windows is up to date

2. **Graphics Issues**
```powershell
# Reset Godot settings
Remove-Item -Path "$env:APPDATA\Godot" -Recurse
# Clear shader cache
Remove-Item -Path ".godot\shader_cache" -Recurse
```

3. **Performance Issues**
- Check Task Manager
- Close background applications
- Update graphics drivers

## Development Tools

### Recommended IDEs/Editors

**macOS:**
- Visual Studio Code with Godot extension
- Sublime Text with GDScript package

**Windows:**
- Visual Studio Code with Godot extension
- Notepad++ with GDScript highlighting

### Debugging Tools

1. **macOS Terminal Commands**
```bash
# Run with debug output
godot --verbose --debug-collisions

# Check for file system issues
find . -name "*.import" -type f -delete
```

2. **Windows PowerShell Commands**
```powershell
# Run with debug output
godot.exe --verbose --debug-collisions

# Check for file system issues
Get-ChildItem -Recurse -Filter "*.import" | Remove-Item
```

## Next Steps

After setup:
1. Follow the UI Testing Guide
2. Run through the test scenarios
3. Check multiplayer functionality
4. Verify 3D rendering performance

Need help? Contact:
- Create an issue in the repository
- Check Godot documentation
- Ask in the project discussion forum

Would you like me to:
1. Add more detailed troubleshooting steps?
2. Include setup for specific development tools?
3. Add performance optimization guides?
4. Create platform-specific debugging guides?
