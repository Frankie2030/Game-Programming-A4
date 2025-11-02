"""
Game State Management for Gomoku
Handles save/load functionality and game state persistence.
"""

import json
import os
import pickle
from datetime import datetime
from typing import Dict, Any, Optional, List
from gomoku_game import GomokuGame, Player, Move, GameState


class GameStateManager:
    """
    Manages game state persistence including save/load functionality.
    """
    
    def __init__(self, save_directory: str = "saves"):
        self.save_directory = save_directory
        self.ensure_save_directory()
    
    def ensure_save_directory(self):
        """Ensure the save directory exists"""
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)
    
    def save_game(self, game: GomokuGame, filename: str = None, 
                  additional_data: Dict[str, Any] = None) -> bool:
        """
        Save a game state to file.
        
        Args:
            game: The GomokuGame instance to save
            filename: Optional filename, if None uses timestamp
            additional_data: Additional data to save (UI state, settings, etc.)
        
        Returns:
            bool: True if save was successful
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"gomoku_save_{timestamp}.json"
            
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = os.path.join(self.save_directory, filename)
            
            # Create save data
            save_data = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "game_state": self._serialize_game(game),
                "additional_data": additional_data or {}
            }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            print(f"Game saved to: {filepath}")
            return True
            
        except Exception as e:
            print(f"Error saving game: {e}")
            return False
    
    def load_game(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load a game state from file.
        
        Args:
            filename: The filename to load from
        
        Returns:
            Dict containing game state and additional data, or None if failed
        """
        try:
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = os.path.join(self.save_directory, filename)
            
            if not os.path.exists(filepath):
                print(f"Save file not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Validate save data
            if not self._validate_save_data(save_data):
                print("Invalid save file format")
                return None
            
            # Deserialize game
            game = self._deserialize_game(save_data["game_state"])
            if game is None:
                return None
            
            return {
                "game": game,
                "additional_data": save_data.get("additional_data", {}),
                "timestamp": save_data.get("timestamp"),
                "version": save_data.get("version")
            }
            
        except Exception as e:
            print(f"Error loading game: {e}")
            return None
    
    def get_save_files(self) -> List[Dict[str, Any]]:
        """
        Get list of available save files with metadata.
        
        Returns:
            List of dictionaries containing save file information
        """
        save_files = []
        
        try:
            for filename in os.listdir(self.save_directory):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.save_directory, filename)
                    
                    try:
                        # Get file stats
                        stat = os.stat(filepath)
                        modified_time = datetime.fromtimestamp(stat.st_mtime)
                        
                        # Try to read save metadata
                        with open(filepath, 'r', encoding='utf-8') as f:
                            save_data = json.load(f)
                        
                        game_data = save_data.get("game_state", {})
                        
                        save_info = {
                            "filename": filename,
                            "filepath": filepath,
                            "modified_time": modified_time,
                            "timestamp": save_data.get("timestamp"),
                            "version": save_data.get("version", "unknown"),
                            "move_count": len(game_data.get("move_history", [])),
                            "current_player": game_data.get("current_player"),
                            "game_state": game_data.get("game_state"),
                            "file_size": stat.st_size
                        }
                        
                        save_files.append(save_info)
                        
                    except Exception as e:
                        print(f"Error reading save file {filename}: {e}")
                        continue
            
            # Sort by modification time (newest first)
            save_files.sort(key=lambda x: x["modified_time"], reverse=True)
            
        except Exception as e:
            print(f"Error listing save files: {e}")
        
        return save_files
    
    def delete_save_file(self, filename: str) -> bool:
        """
        Delete a save file.
        
        Args:
            filename: The filename to delete
        
        Returns:
            bool: True if deletion was successful
        """
        try:
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = os.path.join(self.save_directory, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Deleted save file: {filepath}")
                return True
            else:
                print(f"Save file not found: {filepath}")
                return False
                
        except Exception as e:
            print(f"Error deleting save file: {e}")
            return False
    
    def save_quick_game(self, game: GomokuGame, additional_data: Dict[str, Any] = None) -> bool:
        """
        Quick save to a standard filename (overwrites previous quick save).
        
        Args:
            game: The GomokuGame instance to save
            additional_data: Additional data to save
        
        Returns:
            bool: True if save was successful
        """
        return self.save_game(game, "quick_save.json", additional_data)
    
    def load_quick_game(self) -> Optional[Dict[str, Any]]:
        """
        Load the quick save file.
        
        Returns:
            Dict containing game state and additional data, or None if failed
        """
        return self.load_game("quick_save.json")
    
    def has_quick_save(self) -> bool:
        """
        Check if a quick save file exists.
        
        Returns:
            bool: True if quick save exists
        """
        filepath = os.path.join(self.save_directory, "quick_save.json")
        return os.path.exists(filepath)
    
    def _serialize_game(self, game: GomokuGame) -> Dict[str, Any]:
        """
        Serialize a GomokuGame instance to a dictionary.
        
        Args:
            game: The GomokuGame instance to serialize
        
        Returns:
            Dict containing serialized game data
        """
        return {
            "board": [[cell.value for cell in row] for row in game.board],
            "current_player": game.current_player.value,
            "game_state": game.game_state.value,
            "winner": game.winner.value if game.winner else None,
            "move_history": [
                {
                    "row": move.row,
                    "col": move.col,
                    "player": move.player.value
                }
                for move in game.move_history
            ]
        }
    
    def _deserialize_game(self, game_data: Dict[str, Any]) -> Optional[GomokuGame]:
        """
        Deserialize a dictionary to a GomokuGame instance.
        
        Args:
            game_data: Dictionary containing serialized game data
        
        Returns:
            GomokuGame instance or None if deserialization failed
        """
        try:
            game = GomokuGame()
            
            # Restore board
            for row in range(GomokuGame.BOARD_SIZE):
                for col in range(GomokuGame.BOARD_SIZE):
                    game.board[row][col] = Player(game_data["board"][row][col])
            
            # Restore game state
            game.current_player = Player(game_data["current_player"])
            game.game_state = GameState(game_data["game_state"])
            game.winner = Player(game_data["winner"]) if game_data["winner"] else None
            
            # Restore move history
            game.move_history = []
            for move_data in game_data["move_history"]:
                move = Move(
                    move_data["row"],
                    move_data["col"],
                    Player(move_data["player"])
                )
                game.move_history.append(move)
            
            return game
            
        except Exception as e:
            print(f"Error deserializing game: {e}")
            return None
    
    def _validate_save_data(self, save_data: Dict[str, Any]) -> bool:
        """
        Validate save data structure.
        
        Args:
            save_data: The save data to validate
        
        Returns:
            bool: True if save data is valid
        """
        try:
            # Check required fields
            required_fields = ["version", "timestamp", "game_state"]
            for field in required_fields:
                if field not in save_data:
                    return False
            
            # Check game state structure
            game_state = save_data["game_state"]
            game_required_fields = ["board", "current_player", "game_state", "move_history"]
            for field in game_required_fields:
                if field not in game_state:
                    return False
            
            # Validate board dimensions
            board = game_state["board"]
            if (len(board) != GomokuGame.BOARD_SIZE or 
                any(len(row) != GomokuGame.BOARD_SIZE for row in board)):
                return False
            
            # Validate player values
            valid_players = [Player.EMPTY.value, Player.BLACK.value, Player.WHITE.value]
            for row in board:
                for cell in row:
                    if cell not in valid_players:
                        return False
            
            return True
            
        except Exception:
            return False


class GameSettings:
    """
    Manages game settings and preferences.
    """
    
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            "ai_difficulty": "medium",
            "sound_enabled": True,
            "music_enabled": True,
            "show_coordinates": False,
            "highlight_last_move": True,
            "auto_save": True,
            "network_port": 12345,
            "player_name": "Player",
            "window_width": 1000,
            "window_height": 700
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from file.
        
        Returns:
            Dict containing settings
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults (in case new settings were added)
                settings = self.default_settings.copy()
                settings.update(loaded_settings)
                return settings
            else:
                return self.default_settings.copy()
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self) -> bool:
        """
        Save settings to file.
        
        Returns:
            bool: True if save was successful
        """
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
            
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """Set a setting value"""
        self.settings[key] = value
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.default_settings.copy()


# Global instances
game_state_manager = GameStateManager()
game_settings = GameSettings()

