#!/usr/bin/env python3
"""
Gomoku Game - Main Entry Point
A complete implementation of Gomoku (Five in a Row) with AI and networking support.

Features:
- Local Player vs Player
- Player vs AI with multiple difficulty levels (Easy, Medium, Hard, Expert)
- Online multiplayer (Host/Join network games)
- Save/Load game functionality
- Minimax AI with Alpha-Beta pruning
- Complete menu system with Continue/Resume capability

Usage:
    python main.py              # Start the game with GUI
    python main.py --server     # Start dedicated server
    python main.py --client     # Start as client only
    python main.py --test       # Run basic tests
"""

import sys
import argparse
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game_ui import GomokuUI, main as ui_main
from gomoku_game import GomokuGame, Player
from ai_player import AIPlayer


def run_server(host="localhost", port=12345):
    """Run a dedicated game server"""
    print(f"Starting Dedicated Gomoku Server on {host}:{port}")
    
    # Import the dedicated server
    from src.dedicated_server import DedicatedGomokuServer
    
    server = DedicatedGomokuServer(host, port)
    
    try:
        if server.start():
            print("✅ Dedicated server started successfully!")
            print("📝 Features:")
            print("   - Multiple simultaneous games")
            print("   - Player name management")
            print("   - Room creation and joining")
            print("   - Automatic cleanup")
            print("\n🎮 Connect with: python main.py")
            print("⏹️  Press Ctrl+C to stop the server\n")
            
            # Main server loop
            while server.running:
                import time
                time.sleep(5)
                server.print_stats()
                
        else:
            print("❌ Failed to start server")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested...")
    finally:
        server.stop()
    
    return 0


def run_client(host="localhost", port=12345):
    """Run a test client using the stable client"""
    print(f"Testing connection to Gomoku server at {host}:{port}")
    
    # Import the stable client
    from src.stable_client import StableGomokuClient
    
    client = StableGomokuClient()
    
    # Set up handlers
    def on_room_list(data):
        rooms = data.get("rooms", [])
        print(f"📋 Available rooms: {len(rooms)}")
        for room in rooms:
            print(f"   - {room['name']} (Host: {room['host_name']}, Players: {room['players']}/{room['max_players']})")
    
    def on_game_started(data):
        print(f"🎯 Game started! Players: {data.get('players', [])}")
    
    client.set_message_handler("room_list", on_room_list)
    client.set_message_handler("game_started", on_game_started)
    
    try:
        if client.connect(host, port):
            print("✅ Connected! Testing lobby functionality...")
            
            # Test lobby functions
            client.join_lobby("TestPlayer")
            time.sleep(1)
            
            client.get_rooms()
            time.sleep(1)
            
            client.create_room("Test Room")
            time.sleep(2)
            
            print("✅ Test completed successfully!")
            
        else:
            print("❌ Failed to connect to server")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
    finally:
        client.disconnect()
    
    return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Gomoku - Five in a Row Game")
    parser.add_argument("--server", action="store_true", help="Run as dedicated server")
    parser.add_argument("--client", action="store_true", help="Run as test client")
    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--port", type=int, default=12345, help="Server port (default: 12345)")
    
    args = parser.parse_args()
    
    try:
        if args.server:
            return run_server(args.host, args.port)
        elif args.client:
            return run_client(args.host, args.port)
        else:
            # Run the main GUI game
            print("Starting Gomoku Game...")
            print("Controls:")
            print("- Click on the board to place stones")
            print("- Use the menu to access different game modes")
            print("- Press ESC or use the Pause button during gameplay")
            print()
            ui_main()
            return 0
            
    except KeyboardInterrupt:
        print("\nExiting...")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
