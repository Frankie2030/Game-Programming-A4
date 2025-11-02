"""
Pygame UI for Gomoku Game
Handles all graphics, user input, and game states.
"""

import pygame
import sys
import os
import time
import threading
import math
from typing import Tuple, Optional, Dict, Any
from enum import Enum

from gomoku_game import GomokuGame, Player, GameState
from ai_player import AIPlayer, RandomAI
from stable_client import StableGomokuClient
from server_config import get_server_config, ServerConfig, ServerType


class UIState(Enum):
    """UI state enumeration"""
    MAIN_MENU = "main_menu"
    GAME_MODE_SELECT = "game_mode_select"
    AI_DIFFICULTY_SELECT = "ai_difficulty_select"
    NETWORK_SETUP = "network_setup"
    PLAYER_NAME_INPUT = "player_name_input"
    SERVER_SELECT = "server_select"
    LOBBY_BROWSER = "lobby_browser"
    ROOM_CREATE = "room_create"
    ROOM_WAITING = "room_waiting"
    GAMEPLAY = "gameplay"
    GAME_OVER = "game_over"
    PAUSE_MENU = "pause_menu"
    SETTINGS = "settings"


class GameMode(Enum):
    """Game mode enumeration"""
    LOCAL_PVP = "local_pvp"
    AI_GAME = "ai_game"
    NETWORK_GAME = "network_game"


class Colors:
    """Modern color constants"""
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BROWN = (139, 69, 19)
    LIGHT_BROWN = (160, 82, 45)
    DARK_BROWN = (101, 67, 33)
    GRAY = (128, 128, 128)
    LIGHT_GRAY = (243, 244, 246)
    DARK_GRAY = (55, 65, 81)
    GREEN = (34, 197, 94)      # Modern green
    RED = (239, 68, 68)        # Modern red
    BLUE = (59, 130, 246)      # Modern blue
    YELLOW = (255, 255, 0)
    
    # Additional modern colors
    BACKGROUND = (248, 250, 252)  # Light blue-gray background
    CARD_BG = (255, 255, 255)     # Card background
    ACCENT = (99, 102, 241)       # Indigo accent
    SUCCESS = (16, 185, 129)      # Success green
    WARNING = (245, 158, 11)      # Warning amber
    ERROR = (239, 68, 68)         # Error red
    TEXT_PRIMARY = (17, 24, 39)   # Dark text
    TEXT_SECONDARY = (107, 114, 128)  # Gray text


class Button:
    """Simple button class for UI"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 font: pygame.font.Font, color: Tuple[int, int, int] = Colors.LIGHT_GRAY,
                 text_color: Tuple[int, int, int] = Colors.BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.text_color = text_color
        self.hovered = False
        self.enabled = True
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events, return True if clicked"""
        if not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                return True
        return False
    
    def draw(self, screen: pygame.Surface):
        """Draw the button"""
        color = Colors.WHITE if self.hovered and self.enabled else self.color
        if not self.enabled:
            color = Colors.GRAY
            
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, Colors.BLACK, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class GomokuUI:
    """Main UI class for Gomoku game"""
    
    def __init__(self):
        pygame.init()
        
        # Smaller screen settings for side-by-side viewing
        self.WINDOW_WIDTH = 800   # Reduced from 1000
        self.WINDOW_HEIGHT = 600  # Reduced from 700
        self.BOARD_SIZE = 450  # Further reduced to fit better in 800x600
        self.BOARD_OFFSET_X = 60
        self.BOARD_OFFSET_Y = 100   # Moved up more to ensure full visibility
        self.CELL_SIZE = self.BOARD_SIZE // GomokuGame.BOARD_SIZE
        
        # Center the window on screen
        import os
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'centered'
        
        # Initialize display
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Gomoku - Five in a Row")
        
        # Initialize fonts (adjusted for smaller 800x600 screen)
        self.font_large = pygame.font.Font(None, 42)   # Reduced from 48
        self.font_medium = pygame.font.Font(None, 28)  # Reduced from 32
        self.font_small = pygame.font.Font(None, 22)   # Reduced from 24
        
        # Game state
        self.ui_state = UIState.MAIN_MENU
        self.game_mode = None
        self.game = GomokuGame()
        self.ai_player = None
        self.ai_difficulty = "medium"
        self.network_manager = None
        self.is_network_game = False
        self.pause_initiator = None  # Tracks who initiated the pause
        # === Turn Timer ===
        self.turn_start_time = None
        self.move_time_limit = 20  # seconds
        self.elapsed_before_pause = 0  # how much time elapsed before pausing

        # Pause control per player
        self.paused = False
        self.pause_sent = False  # prevents multiple pause sends per click
        self.pause_start_time = None
        self.pause_allowance = {Player.BLACK: 2, Player.WHITE: 2}
        self.pause_remaining = {Player.BLACK: 30, Player.WHITE: 30}
        
        # AI threading
        self.ai_thinking = False
        self.ai_thread = None
        self.ai_move_result = None
        self.thinking_start_time = 0
        self.my_player = Player.BLACK
        self.waiting_for_network = False
        
        # Player names for display
        self.player_names = {
            Player.BLACK: "Player 1",
            Player.WHITE: "Player 2"
        }
        
        # Server configuration
        self.server_config_manager = get_server_config()
        self.selected_server_config = None
        
        # UI elements
        self.buttons = {}
        self.text_inputs = {}
        self.messages = []
        self.last_move_pos = None
        
        # Game state management
        self.saved_game_exists = False
        self.check_saved_game()
        
        # Lobby and networking state
        self.player_name = ""
        self.current_room_list = []
        self.selected_room = None
        self.room_info = None
        
        # Text input state
        self.text_input_active = False
        self.text_input_content = ""
        self.text_input_prompt = ""
        
        # Clock for FPS
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialize UI elements
        self._init_ui_elements()
    
    def check_saved_game(self):
        """Check if a saved game exists"""
        self.saved_game_exists = os.path.exists("saved_game.json")
    
    def _init_ui_elements(self):
        """Initialize UI elements for different states"""
        # Main menu buttons (centered for 800px width)
        self.buttons["main_menu"] = [
            Button(300, 200, 200, 50, "New Game", self.font_medium),
            Button(300, 270, 200, 50, "Continue", self.font_medium),
            Button(300, 340, 200, 50, "Settings", self.font_medium),
            Button(300, 410, 200, 50, "Quit", self.font_medium)
        ]
        
        # Game mode selection buttons (centered for 800px width)
        self.buttons["game_mode"] = [
            Button(200, 200, 400, 50, "Local Player vs Player", self.font_medium),
            Button(200, 270, 400, 50, "Player vs AI", self.font_medium),
            Button(200, 340, 400, 50, "Network Game", self.font_medium),
            Button(300, 450, 200, 50, "Back", self.font_medium)
        ]
        
        # AI difficulty selection buttons (centered for 800px width)
        self.buttons["ai_difficulty"] = [
            Button(250, 200, 300, 50, "Easy", self.font_medium),
            Button(250, 270, 300, 50, "Medium", self.font_medium),
            Button(250, 340, 300, 50, "Hard", self.font_medium),
            Button(250, 410, 300, 50, "Expert", self.font_medium),
            Button(300, 500, 200, 50, "Back", self.font_medium)
        ]
        
        # Network setup buttons
        self.buttons["network_setup"] = [
            Button(400, 400, 200, 50, "Start/Connect", self.font_medium),
            Button(400, 470, 200, 50, "Back", self.font_medium)
        ]
        
        # Player name input buttons (centered for 800px width)
        self.buttons["player_name_input"] = [
            Button(300, 350, 200, 50, "Continue", self.font_medium),
            Button(300, 420, 200, 50, "Back", self.font_medium)
        ]
        
        # Server selection buttons (will be populated dynamically)
        self.buttons["server_select"] = []
        self._update_server_buttons()
        
        # Lobby browser buttons (centered for 800px width)
        self.buttons["lobby_browser"] = [
            Button(100, 500, 130, 40, "Create Room", self.font_small),
            Button(240, 500, 130, 40, "Join Selected", self.font_small),
            Button(380, 500, 130, 40, "Refresh", self.font_small),
            Button(520, 500, 100, 40, "Back", self.font_small)
        ]
        
        # Room create buttons (centered for 800px width)
        self.buttons["room_create"] = [
            Button(250, 400, 150, 50, "Create", self.font_medium),
            Button(420, 400, 150, 50, "Cancel", self.font_medium)
        ]
        
        # Room waiting buttons (centered for 800px width)
        self.buttons["room_waiting"] = [
            Button(300, 450, 200, 50, "Leave Room", self.font_medium)
        ]
        
        # Gameplay buttons (better positioned for 800px width)
        self.buttons["gameplay"] = [
            Button(540, 500, 100, 40, "Pause", self.font_small),
            Button(660, 500, 100, 40, "Resign", self.font_small)
        ]
        
        # Pause menu buttons (centered for 800px width)
        self.buttons["pause_menu"] = [
            Button(300, 250, 200, 50, "Resume", self.font_medium),
            Button(300, 320, 200, 50, "Save Game", self.font_medium),
            Button(300, 390, 200, 50, "Main Menu", self.font_medium)
        ]
        
        # Game over buttons (centered for 800px width)
        self.buttons["game_over"] = [
            Button(250, 400, 150, 50, "New Game", self.font_medium),
            Button(420, 400, 150, 50, "Main Menu", self.font_medium)
        ]
        
        # Settings buttons (centered for 800px width)
        self.buttons["settings"] = [
            Button(200, 200, 400, 50, "Sound: On", self.font_medium),
            Button(200, 270, 400, 50, "Music: On", self.font_medium),
            Button(200, 340, 400, 50, "Show Coordinates: Off", self.font_medium),
            Button(200, 410, 400, 50, "Highlight Last Move: On", self.font_medium),
            Button(300, 500, 200, 50, "Back", self.font_medium)
        ]
    
    def run(self):
        """Main game loop"""
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    def _handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._cleanup_and_quit()
            
            # Handle ESC key for navigation
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._handle_escape_key()
            
            # Handle different UI states
            if self.ui_state == UIState.MAIN_MENU:
                self._handle_main_menu_events(event)
            elif self.ui_state == UIState.GAME_MODE_SELECT:
                self._handle_game_mode_events(event)
            elif self.ui_state == UIState.AI_DIFFICULTY_SELECT:
                self._handle_ai_difficulty_events(event)
            elif self.ui_state == UIState.GAMEPLAY:
                self._handle_gameplay_events(event)
            elif self.ui_state == UIState.PAUSE_MENU:
                self._handle_pause_menu_events(event)
            elif self.ui_state == UIState.GAME_OVER:
                self._handle_game_over_events(event)
            elif self.ui_state == UIState.SETTINGS:
                self._handle_settings_events(event)
            elif self.ui_state == UIState.PLAYER_NAME_INPUT:
                self._handle_player_name_input_events(event)
            elif self.ui_state == UIState.SERVER_SELECT:
                self._handle_server_select_events(event)
            elif self.ui_state == UIState.LOBBY_BROWSER:
                self._handle_lobby_browser_events(event)
            elif self.ui_state == UIState.ROOM_CREATE:
                self._handle_room_create_events(event)
            elif self.ui_state == UIState.ROOM_WAITING:
                self._handle_room_waiting_events(event)
    
    def _handle_main_menu_events(self, event):
        """Handle main menu events"""
        buttons = self.buttons["main_menu"]
        
        # Update continue button state
        buttons[1].enabled = self.saved_game_exists
        
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # New Game
                    self.ui_state = UIState.GAME_MODE_SELECT
                elif i == 1 and self.saved_game_exists:  # Continue
                    self._load_game()
                elif i == 2:  # Settings
                    self.ui_state = UIState.SETTINGS
                elif i == 3:  # Quit
                    self.running = False
    
    def _handle_game_mode_events(self, event):
        """Handle game mode selection events"""
        buttons = self.buttons["game_mode"]
        
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # Local PvP
                    self.game_mode = GameMode.LOCAL_PVP
                    self._start_new_game()
                elif i == 1:  # Player vs AI
                    self.game_mode = GameMode.AI_GAME
                    self.ui_state = UIState.AI_DIFFICULTY_SELECT
                elif i == 2:  # Network Game
                    self.game_mode = GameMode.NETWORK_GAME
                    self.ui_state = UIState.SERVER_SELECT
                elif i == 3:  # Back
                    self.ui_state = UIState.MAIN_MENU
    
    def _handle_ai_difficulty_events(self, event):
        """Handle AI difficulty selection events"""
        buttons = self.buttons["ai_difficulty"]
        difficulties = ["easy", "medium", "hard", "expert"]
        
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i < 4:  # Difficulty selection
                    self.ai_difficulty = difficulties[i]
                    self._start_new_game()
                elif i == 4:  # Back
                    self.ui_state = UIState.GAME_MODE_SELECT
    
    def _handle_network_setup_events(self, event):
        """Handle network setup events"""
        buttons = self.buttons["network_setup"]
        
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # Start/Connect
                    self._setup_network_game()
                elif i == 1:  # Back
                    self.ui_state = UIState.GAME_MODE_SELECT
    
    def _handle_gameplay_events(self, event):
        """Handle gameplay events"""
        buttons = self.buttons["gameplay"]

        # Handle button clicks (require actual click on the button)
        for i, button in enumerate(buttons):
            if button.handle_event(event):  # ← gate all actions on a real button click
                if i == 0:  # Pause
                    if (not self.paused
                            and not self.pause_sent
                            and self.pause_allowance[self.game.current_player] > 0):
                        self.paused = True
                        self.pause_initiator = self.my_player
                        self.pause_sent = True  # prevent multiple sends per press
                        self.ui_state = UIState.PAUSE_MENU
                        self.pause_start_time = time.time()
                        self.pause_allowance[self.game.current_player] -= 1

                        # Calculate remaining time on the move timer
                        if self.turn_start_time:
                            elapsed_time = time.time() - self.turn_start_time
                            remaining_turn = max(0, self.move_time_limit - elapsed_time)
                            self.elapsed_before_pause += elapsed_time
                            self.turn_start_time = None
                        else:
                            remaining_turn = max(0, self.move_time_limit - self.elapsed_before_pause)

                        # Send pause signal only once
                        if self.is_network_game and self.network_manager:
                            self.network_manager.send_message("player_pause", {
                                "player": self.player_names[self.game.current_player],
                                "remaining_turn": remaining_turn
                            })

                        print(f"{self.game.current_player.name} paused the game "
                            f"({self.pause_allowance[self.game.current_player]} pauses left)")

                elif i == 1:  # Resign
                    self._resign_game()

        # Reset debounce when mouse is released (so next click can pause again)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pause_sent = False

        # Handle board clicks for making moves (only on left click down)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._can_make_move():
                pos = self._get_board_position(event.pos)
                if pos:
                    self._make_move(pos[0], pos[1])

    def _handle_pause_menu_events(self, event):
        """Handle pause menu events"""
        buttons = self.buttons["pause_menu"]

        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # Resume
                    current_player = self.game.current_player

                    # Only initiator can resume
                    if self.is_network_game and self.my_player != self.pause_initiator:
                        print(f"⏸ You cannot resume — waiting for {self.player_names[self.pause_initiator]} to resume.")
                        return

                    if self.paused and self.pause_start_time:
                        elapsed_pause = time.time() - self.pause_start_time
                        self.pause_remaining[current_player] = max(
                            0, self.pause_remaining[current_player] - int(elapsed_pause)
                        )

                        # Clear pause state & debounce
                        self.paused = False
                        self.pause_start_time = None
                        self.pause_sent = False  # ← important: allow future pauses

                        # Resume move timer from where it left off
                        remaining_turn = max(0, self.move_time_limit - self.elapsed_before_pause)
                        self.turn_start_time = time.time()
                        print(f"{current_player.name} resumed — "
                            f"{self.pause_remaining[current_player]} s pause time left, "
                            f"{remaining_turn}s remaining turn time")

                        self.ui_state = UIState.GAMEPLAY

                        # Notify opponent when resuming
                        if self.is_network_game and self.network_manager:
                            self.network_manager.send_message("player_resume", {
                                "player": self.player_names[self.game.current_player],
                                "remaining_turn": remaining_turn
                            })

                elif i == 1:  # Save Game
                    self._save_game()
                elif i == 2:  # Main Menu
                    self._return_to_main_menu()

    
    def _handle_game_over_events(self, event):
        """Handle game over events"""
        buttons = self.buttons["game_over"]
        
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # New Game
                    if self.is_network_game:
                        # In network games, need to coordinate with other player
                        self._request_new_network_game()
                    else:
                        # Local games can start immediately
                        self._start_new_game()
                elif i == 1:  # Main Menu
                    if self.is_network_game:
                        # Disconnect from network and return to main menu
                        self._return_to_main_menu()
                    else:
                        self.ui_state = UIState.MAIN_MENU
    
    def _handle_settings_events(self, event):
        """Handle settings events"""
        buttons = self.buttons["settings"]
        
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # Sound toggle
                    # Toggle sound setting (placeholder)
                    if "On" in button.text:
                        button.text = "Sound: Off"
                    else:
                        button.text = "Sound: On"
                elif i == 1:  # Music toggle
                    # Toggle music setting (placeholder)
                    if "On" in button.text:
                        button.text = "Music: Off"
                    else:
                        button.text = "Music: On"
                elif i == 2:  # Show coordinates toggle
                    # Toggle coordinates setting (placeholder)
                    if "Off" in button.text:
                        button.text = "Show Coordinates: On"
                    else:
                        button.text = "Show Coordinates: Off"
                elif i == 3:  # Highlight last move toggle
                    # Toggle highlight setting (placeholder)
                    if "On" in button.text:
                        button.text = "Highlight Last Move: Off"
                    else:
                        button.text = "Highlight Last Move: On"
                elif i == 4:  # Back
                    self.ui_state = UIState.MAIN_MENU
    
    def _handle_player_name_input_events(self, event):
        """Handle player name input events"""
        # Handle text input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text_input_content = self.text_input_content[:-1]
            elif event.key == pygame.K_RETURN:
                if self.text_input_content.strip():
                    self.player_name = self.text_input_content.strip()
                    self._connect_to_lobby()
            elif len(self.text_input_content) < 20 and event.unicode.isprintable():
                self.text_input_content += event.unicode
        
        # Handle buttons
        buttons = self.buttons["player_name_input"]
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # Continue
                    if self.text_input_content.strip():
                        self.player_name = self.text_input_content.strip()
                        self._connect_to_lobby()
                elif i == 1:  # Back
                    self.ui_state = UIState.GAME_MODE_SELECT
    
    def _handle_lobby_browser_events(self, event):
        """Handle lobby browser events"""
        # Handle room list clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if clicked on a room in the list
            start_y = 200
            item_height = 60
            for i, room in enumerate(self.current_room_list):
                room_rect = pygame.Rect(150, start_y + i * (item_height + 10), 500, item_height)  # Match the drawing rect
                if room_rect.collidepoint(event.pos):
                    self.selected_room = room
                    break
        
        # Handle buttons
        buttons = self.buttons["lobby_browser"]
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # Create Room
                    self.ui_state = UIState.ROOM_CREATE
                    self.text_input_content = ""
                elif i == 1:  # Join Selected
                    if self.selected_room:
                        self._join_room(self.selected_room["room_id"])
                elif i == 2:  # Refresh
                    self._refresh_room_list()
                elif i == 3:  # Back
                    self._disconnect_from_lobby()
    
    def _handle_room_create_events(self, event):
        """Handle room creation events"""
        # Handle text input for room name
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text_input_content = self.text_input_content[:-1]
            elif event.key == pygame.K_RETURN:
                if self.text_input_content.strip():
                    self._create_room(self.text_input_content.strip())
            elif len(self.text_input_content) < 30 and event.unicode.isprintable():
                self.text_input_content += event.unicode
        
        # Handle buttons
        buttons = self.buttons["room_create"]
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # Create
                    if self.text_input_content.strip():
                        self._create_room(self.text_input_content.strip())
                elif i == 1:  # Cancel
                    self.ui_state = UIState.LOBBY_BROWSER
    
    def _handle_room_waiting_events(self, event):
        """Handle room waiting events"""
        buttons = self.buttons["room_waiting"]
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # Leave Room
                    self._leave_room()
    
    def _handle_escape_key(self):
        """Handle ESC key press for navigation"""
        if self.ui_state == UIState.GAME_MODE_SELECT:
            self.ui_state = UIState.MAIN_MENU
        elif self.ui_state == UIState.AI_DIFFICULTY_SELECT:
            self.ui_state = UIState.GAME_MODE_SELECT
        elif self.ui_state == UIState.PLAYER_NAME_INPUT:
            self.ui_state = UIState.SERVER_SELECT
        elif self.ui_state == UIState.SERVER_SELECT:
            self.ui_state = UIState.GAME_MODE_SELECT
        elif self.ui_state == UIState.LOBBY_BROWSER:
            self._disconnect_from_lobby()
        elif self.ui_state == UIState.ROOM_CREATE:
            self.ui_state = UIState.LOBBY_BROWSER
        elif self.ui_state == UIState.ROOM_WAITING:
            self._leave_room()
        elif self.ui_state == UIState.GAMEPLAY and not self.is_network_game:
            self.ui_state = UIState.PAUSE_MENU
        elif self.ui_state == UIState.PAUSE_MENU:
            self.ui_state = UIState.GAMEPLAY
        elif self.ui_state == UIState.SETTINGS:
            self.ui_state = UIState.MAIN_MENU
    
    def _cleanup_and_quit(self):
        """Properly cleanup network connections before quitting"""
        print("Cleaning up connections...")
        
        # Disconnect from network if connected
        if self.network_manager:
            try:
                # Leave room if in one
                if self.ui_state == UIState.ROOM_WAITING and hasattr(self, 'room_info') and self.room_info:
                    self.network_manager.leave_room()
                
                # Disconnect from server
                self.network_manager.disconnect()
                self.network_manager = None
                print("Network disconnected successfully")
            except Exception as e:
                print(f"Error during network cleanup: {e}")
        
        self.running = False
    
    def _update(self):
        """Update game state"""
        # Handle network messages if connected
        if self.network_manager and self.network_manager.connected:
            # Give network time to process messages
            try:
                # This allows the network threads to process messages
                import time
                time.sleep(0.001)  # Small delay to prevent blocking
            except:
                pass
        import time

        # Enforce per-move 20s limit
        if self.ui_state == UIState.GAMEPLAY and self.game.game_state == GameState.PLAYING:
            if self.turn_start_time is None:
                self.turn_start_time = time.time()
                
            # Skip countdown while paused
            if self.paused:
                return

            if self.turn_start_time:
                elapsed = self.elapsed_before_pause + (time.time() - self.turn_start_time)
            else:
                elapsed = self.elapsed_before_pause  # frozen time during pause

            if elapsed > self.move_time_limit:
                print(f"⏰ Player {self.game.current_player.name} exceeded 20 s — auto-resign.")
                self._resign_game()
                self.turn_start_time = None
                self.elapsed_before_pause = 0
                return
        if self.ui_state == UIState.GAMEPLAY:
            # Handle AI moves
            if (self.game_mode == GameMode.AI_GAME and 
                self.game.current_player != Player.BLACK and 
                self.game.game_state == GameState.PLAYING and
                self.ai_player):
                
                # Start AI thinking if not already started
                if not self.ai_thinking and (self.ai_thread is None or not self.ai_thread.is_alive()):
                    self._start_ai_thinking()
                
                # Check if AI has finished thinking
                elif self.ai_thinking and self.ai_move_result is not None:
                    move = self.ai_move_result
                    self.ai_move_result = None
                    self.ai_thinking = False
                    
                    if move:
                        self._make_move(move[0], move[1])
            
            # Check for game over
            if self.game.game_state != GameState.PLAYING:
                self.ui_state = UIState.GAME_OVER
        # While paused, decrease current player's remaining pause time
        if self.paused and self.pause_start_time:
            current_player = self.game.current_player
            elapsed_pause = time.time() - self.pause_start_time
            if elapsed_pause >= self.pause_remaining[current_player]:
                print(f"{current_player.name}'s pause expired automatically")
                self.paused = False
                self.pause_start_time = None
                self.ui_state = UIState.GAMEPLAY
    
    def _draw(self):
        """Draw the current UI state"""
        self.screen.fill(Colors.BACKGROUND)
        
        if self.ui_state == UIState.MAIN_MENU:
            self._draw_main_menu()
        elif self.ui_state == UIState.GAME_MODE_SELECT:
            self._draw_game_mode_select()
        elif self.ui_state == UIState.AI_DIFFICULTY_SELECT:
            self._draw_ai_difficulty_select()
        elif self.ui_state == UIState.GAMEPLAY:
            self._draw_gameplay()
        elif self.ui_state == UIState.PAUSE_MENU:
            self._draw_pause_menu()
        elif self.ui_state == UIState.GAME_OVER:
            self._draw_game_over()
        elif self.ui_state == UIState.SETTINGS:
            self._draw_settings()
        elif self.ui_state == UIState.PLAYER_NAME_INPUT:
            self._draw_player_name_input()
        elif self.ui_state == UIState.SERVER_SELECT:
            self._draw_server_select()
        elif self.ui_state == UIState.LOBBY_BROWSER:
            self._draw_lobby_browser()
        elif self.ui_state == UIState.ROOM_CREATE:
            self._draw_room_create()
        elif self.ui_state == UIState.ROOM_WAITING:
            self._draw_room_waiting()
            
        if self.ui_state in [UIState.GAMEPLAY, UIState.PAUSE_MENU] and (
            self.turn_start_time or self.elapsed_before_pause
        ):
            # Calculate frozen or live remaining time
            if self.turn_start_time:
                elapsed = self.elapsed_before_pause + (time.time() - self.turn_start_time)
            else:
                elapsed = self.elapsed_before_pause
            remaining = max(0, int(self.move_time_limit - elapsed))

            # Color logic
            if remaining > 10:
                color = Colors.SUCCESS
            elif remaining > 5:
                color = Colors.WARNING
            else:
                color = Colors.ERROR

            # === 1️⃣ Main move timer ===
            timer_rect = pygame.Rect(self.WINDOW_WIDTH - 180, 20, 130, 45)
            pygame.draw.rect(self.screen, Colors.BACKGROUND, timer_rect)   # flat background
            pygame.draw.rect(self.screen, color, timer_rect, 2)       # no radius
            timer_text = self.font_medium.render(f"{remaining:02d}s", True, color)
            self.screen.blit(timer_text, timer_text.get_rect(center=timer_rect.center))

            # === 2️⃣ Pause info boxes (below main timer) ===
            y = 10
            box_width = 200
            box_height = 36
            for player in [Player.BLACK, Player.WHITE]:
                label = self.player_names[player]
                pauses_left = self.pause_allowance[player]
                pause_time = self.pause_remaining[player]

                pause_rect = pygame.Rect(20, y, box_width, box_height)
                pygame.draw.rect(self.screen, Colors.BACKGROUND, pause_rect)
                pygame.draw.rect(self.screen, Colors.TEXT_SECONDARY, pause_rect, 2)

                pause_text = f"{label}: {pauses_left}× {pause_time}s"
                text_surface = self.font_small.render(pause_text, True, Colors.TEXT_SECONDARY)
                self.screen.blit(text_surface, text_surface.get_rect(center=pause_rect.center))

                y += box_height + 8
        
        pygame.display.flip()
    
    def _draw_main_menu(self):
        """Draw main menu"""
        # Title (centered for 800px width)
        title = self.font_large.render("GOMOKU", True, Colors.TEXT_PRIMARY)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Five in a Row", True, Colors.TEXT_SECONDARY)
        subtitle_rect = subtitle.get_rect(center=(self.WINDOW_WIDTH // 2, 140))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Buttons
        for button in self.buttons["main_menu"]:
            button.draw(self.screen)
    
    def _draw_game_mode_select(self):
        """Draw game mode selection"""
        title = self.font_large.render("Select Game Mode", True, Colors.TEXT_PRIMARY)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        for button in self.buttons["game_mode"]:
            button.draw(self.screen)
    
    def _draw_ai_difficulty_select(self):
        """Draw AI difficulty selection"""
        title = self.font_large.render("Select AI Difficulty", True, Colors.TEXT_PRIMARY)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        for button in self.buttons["ai_difficulty"]:
            button.draw(self.screen)
    
    
    def _draw_gameplay(self):
        """Draw gameplay screen"""
        # Draw board
        self._draw_board()
        
        # Draw game info
        self._draw_game_info()
        
        # Draw buttons
        for button in self.buttons["gameplay"]:
            button.draw(self.screen)
    
    def _draw_pause_menu(self):
        """Draw pause menu overlay"""
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(Colors.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause menu
        title = self.font_large.render("PAUSED", True, Colors.WHITE)
        # === Show live pause countdown while paused ===
        if self.paused and self.pause_start_time:
            current_player = self.game.current_player
            elapsed_pause = time.time() - self.pause_start_time
            remaining_pause = max(0, int(self.pause_remaining[current_player] - elapsed_pause))

            # Centered rectangle box
            pause_rect = pygame.Rect(self.WINDOW_WIDTH // 2 - 80, 180, 160, 50)
            pygame.draw.rect(self.screen, Colors.BACKGROUND, pause_rect)
            pygame.draw.rect(self.screen, Colors.WARNING, pause_rect, 2)

            pause_text = self.font_medium.render(f"Pause: {remaining_pause:02d}s", True, Colors.WARNING)
            self.screen.blit(pause_text, pause_text.get_rect(center=pause_rect.center))

        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        for button in self.buttons["pause_menu"]:
            button.draw(self.screen)
        for button in self.buttons["pause_menu"]:
            # Disable Resume if not allowed
            if button.text == "Resume":
                if self.is_network_game and self.pause_initiator and self.pause_initiator != self.my_player:
                    button.enabled = False
                else:
                    button.enabled = True
            button.draw(self.screen)
    
    def _draw_game_over(self):
        """Draw game over screen"""
        # Draw board (faded)
        self._draw_board()
        
        # Draw overlay
        overlay = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(Colors.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Draw game over message with player names
        if self.game.game_state == GameState.BLACK_WINS:
            winner_name = self.player_names.get(Player.BLACK, "Black")
            message = f"{winner_name} WINS!"
            color = Colors.WHITE
        elif self.game.game_state == GameState.WHITE_WINS:
            winner_name = self.player_names.get(Player.WHITE, "White")
            message = f"{winner_name} WINS!"
            color = Colors.WHITE
        else:
            message = "Draw!"
            color = Colors.YELLOW
        
        title = self.font_large.render(message, True, color)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)
        
        for button in self.buttons["game_over"]:
            button.draw(self.screen)
    
    def _draw_settings(self):
        """Draw settings menu"""
        title = self.font_large.render("Settings", True, Colors.BLACK)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Instructions
        instruction = self.font_small.render("Click buttons to toggle settings", True, Colors.GRAY)
        instruction_rect = instruction.get_rect(center=(self.WINDOW_WIDTH // 2, 150))
        self.screen.blit(instruction, instruction_rect)
        
        for button in self.buttons["settings"]:
            button.draw(self.screen)
    
    def _draw_player_name_input(self):
        """Draw player name input screen"""
        title = self.font_large.render("Enter Your Name", True, Colors.BLACK)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Instruction
        instruction = self.font_medium.render("Please enter your player name:", True, Colors.GRAY)
        instruction_rect = instruction.get_rect(center=(self.WINDOW_WIDTH // 2, 200))
        self.screen.blit(instruction, instruction_rect)
        
        # Text input box
        input_rect = pygame.Rect(self.WINDOW_WIDTH // 2 - 150, 250, 300, 40)
        pygame.draw.rect(self.screen, Colors.WHITE, input_rect)
        pygame.draw.rect(self.screen, Colors.BLACK, input_rect, 2)
        
        # Text content
        display_text = self.text_input_content if self.text_input_content else "Enter name here..."
        text_color = Colors.BLACK if self.text_input_content else Colors.GRAY
        text_surface = self.font_medium.render(display_text, True, text_color)
        text_rect = text_surface.get_rect()
        text_rect.centery = input_rect.centery
        text_rect.x = input_rect.x + 10
        self.screen.blit(text_surface, text_rect)
        
        # Cursor
        if len(self.text_input_content) > 0:
            cursor_x = text_rect.right + 2
            pygame.draw.line(self.screen, Colors.BLACK, 
                           (cursor_x, input_rect.y + 5), 
                           (cursor_x, input_rect.bottom - 5), 2)
        
        # Help text
        help_text = self.font_small.render("Press Enter to continue or click Continue button", True, Colors.GRAY)
        help_rect = help_text.get_rect(center=(self.WINDOW_WIDTH // 2, 310))
        self.screen.blit(help_text, help_rect)
        
        # Buttons
        for button in self.buttons["player_name_input"]:
            button.draw(self.screen)
    
    def _draw_server_select(self):
        """Draw server selection screen"""
        title = self.font_large.render("Select Server", True, Colors.TEXT_PRIMARY)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Current server info
        current_config = self.server_config_manager.get_current_config()
        if current_config:
            current_text = f"Current: {current_config.name}"
            current_surface = self.font_medium.render(current_text, True, Colors.TEXT_SECONDARY)
            current_rect = current_surface.get_rect(center=(self.WINDOW_WIDTH // 2, 90))
            self.screen.blit(current_surface, current_rect)
        
        # Server list
        configs = self.server_config_manager.get_all_configs()
        start_y = 130
        
        for i, (name, config) in enumerate(configs.items()):
            y_pos = start_y + i * 60
            
            # Server name and type
            server_text = f"{name} ({config.server_type.value})"
            server_surface = self.font_small.render(server_text, True, Colors.TEXT_PRIMARY)
            self.screen.blit(server_surface, (100, y_pos))
            
            # Server details
            details_text = f"{config.host}:{config.port}"
            if config.use_ssl:
                details_text += " (SSL)"
            details_surface = self.font_small.render(details_text, True, Colors.TEXT_SECONDARY)
            self.screen.blit(details_surface, (100, y_pos + 20))
            
            # Current indicator
            if name == self.server_config_manager.current_config:
                indicator = self.font_small.render("← CURRENT", True, Colors.SUCCESS)
                self.screen.blit(indicator, (500, y_pos + 10))
        
        # Instructions
        instructions = [
            "Click on a server to select it",
            "Press Enter to continue with selected server",
            "ESC to go back"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, Colors.TEXT_SECONDARY)
            text_rect = text.get_rect(center=(self.WINDOW_WIDTH // 2, 450 + i * 20))
            self.screen.blit(text, text_rect)
        
        # Buttons
        for button in self.buttons["server_select"]:
            button.draw(self.screen)
    
    def _draw_lobby_browser(self):
        """Draw lobby browser screen"""
        title = self.font_large.render(f"Welcome, {self.player_name}!", True, Colors.BLACK)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Room list title
        rooms_title = self.font_medium.render("Available Games:", True, Colors.BLACK)
        rooms_title_rect = rooms_title.get_rect(x=200, y=150)
        self.screen.blit(rooms_title, rooms_title_rect)
        
        # Room list
        if self.current_room_list:
            start_y = 200
            item_height = 60
            
            for i, room in enumerate(self.current_room_list):
                y = start_y + i * (item_height + 10)
                room_rect = pygame.Rect(150, y, 500, item_height)  # Reduced width from 600 to 500, moved left
                
                # Background color with better visual feedback
                is_selected = (self.selected_room and room["room_id"] == self.selected_room["room_id"])
                
                if is_selected:
                    # Selected room: modern accent color with green border
                    pygame.draw.rect(self.screen, Colors.ACCENT, room_rect)
                    pygame.draw.rect(self.screen, Colors.SUCCESS, room_rect, 3)
                    text_color = Colors.WHITE
                else:
                    # Unselected room: clean white background
                    pygame.draw.rect(self.screen, Colors.CARD_BG, room_rect)
                    pygame.draw.rect(self.screen, Colors.GRAY, room_rect, 2)
                    text_color = Colors.TEXT_PRIMARY
                
                # Room info
                room_name = room.get("name", "Unknown Room")
                host_name = room.get("host_name", "Unknown")
                player_count = room.get("players", 0)
                max_players = room.get("max_players", 2)
                
                # Room name
                name_surface = self.font_medium.render(room_name, True, text_color)
                name_rect = name_surface.get_rect(x=room_rect.x + 10, y=room_rect.y + 5)
                self.screen.blit(name_surface, name_rect)
                
                # Host and player info with appropriate color
                info_text = f"Host: {host_name} | Players: {player_count}/{max_players}"
                info_color = Colors.LIGHT_GRAY if is_selected else Colors.TEXT_SECONDARY
                info_surface = self.font_small.render(info_text, True, info_color)
                info_rect = info_surface.get_rect(x=room_rect.x + 10, y=room_rect.y + 35)
                self.screen.blit(info_surface, info_rect)
        else:
            no_rooms = self.font_medium.render("No games available. Create one!", True, Colors.GRAY)
            no_rooms_rect = no_rooms.get_rect(center=(self.WINDOW_WIDTH // 2, 300))
            self.screen.blit(no_rooms, no_rooms_rect)
        
        # Instructions
        instructions = [
            "Click on a room to select it",
            "Use buttons below to create, join, or refresh"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font_small.render(instruction, True, Colors.GRAY)
            text_rect = text.get_rect(center=(self.WINDOW_WIDTH // 2, 450 + i * 25))
            self.screen.blit(text, text_rect)
        
        # Buttons
        for button in self.buttons["lobby_browser"]:
            button.draw(self.screen)
    
    def _draw_room_create(self):
        """Draw room creation screen"""
        title = self.font_large.render("Create New Room", True, Colors.BLACK)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Instruction
        instruction = self.font_medium.render("Enter room name:", True, Colors.GRAY)
        instruction_rect = instruction.get_rect(center=(self.WINDOW_WIDTH // 2, 200))
        self.screen.blit(instruction, instruction_rect)
        
        # Text input box
        input_rect = pygame.Rect(self.WINDOW_WIDTH // 2 - 200, 250, 400, 40)
        pygame.draw.rect(self.screen, Colors.WHITE, input_rect)
        pygame.draw.rect(self.screen, Colors.BLACK, input_rect, 2)
        
        # Text content
        display_text = self.text_input_content if self.text_input_content else "Enter room name..."
        text_color = Colors.BLACK if self.text_input_content else Colors.GRAY
        text_surface = self.font_medium.render(display_text, True, text_color)
        text_rect = text_surface.get_rect()
        text_rect.centery = input_rect.centery
        text_rect.x = input_rect.x + 10
        self.screen.blit(text_surface, text_rect)
        
        # Cursor
        if len(self.text_input_content) > 0:
            cursor_x = text_rect.right + 2
            pygame.draw.line(self.screen, Colors.BLACK, 
                           (cursor_x, input_rect.y + 5), 
                           (cursor_x, input_rect.bottom - 5), 2)
        
        # Help text
        help_text = self.font_small.render("Press Enter to create or click Create button", True, Colors.GRAY)
        help_rect = help_text.get_rect(center=(self.WINDOW_WIDTH // 2, 310))
        self.screen.blit(help_text, help_rect)
        
        # Buttons
        for button in self.buttons["room_create"]:
            button.draw(self.screen)
    
    def _draw_room_waiting(self):
        """Draw room waiting screen"""
        title = self.font_large.render("Waiting for Players", True, Colors.BLACK)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        if self.room_info:
            room_name = self.room_info.get("name", "Unknown Room")
            room_title = self.font_medium.render(f"Room: {room_name}", True, Colors.BLACK)
            room_title_rect = room_title.get_rect(center=(self.WINDOW_WIDTH // 2, 200))
            self.screen.blit(room_title, room_title_rect)
            
            player_count = self.room_info.get("players", 0)
            max_players = self.room_info.get("max_players", 2)
            
            status_text = f"Players: {player_count}/{max_players}"
            status_surface = self.font_medium.render(status_text, True, Colors.GRAY)
            status_rect = status_surface.get_rect(center=(self.WINDOW_WIDTH // 2, 250))
            self.screen.blit(status_surface, status_rect)
            
            if player_count >= max_players:
                ready_text = "Game can start!"
                ready_surface = self.font_medium.render(ready_text, True, Colors.GREEN)
            else:
                ready_text = "Waiting for more players..."
                ready_surface = self.font_medium.render(ready_text, True, Colors.GRAY)
            
            ready_rect = ready_surface.get_rect(center=(self.WINDOW_WIDTH // 2, 300))
            self.screen.blit(ready_surface, ready_rect)
        
        # Buttons
        for button in self.buttons["room_waiting"]:
            button.draw(self.screen)
    
    def _draw_board(self):
        """Draw the game board"""
        # Draw board background
        board_rect = pygame.Rect(self.BOARD_OFFSET_X, self.BOARD_OFFSET_Y, 
                                self.BOARD_SIZE, self.BOARD_SIZE)
        pygame.draw.rect(self.screen, Colors.LIGHT_BROWN, board_rect)
        
        # Draw grid lines
        for i in range(GomokuGame.BOARD_SIZE + 1):
            # Vertical lines
            x = self.BOARD_OFFSET_X + i * self.CELL_SIZE
            pygame.draw.line(self.screen, Colors.BLACK, 
                           (x, self.BOARD_OFFSET_Y), 
                           (x, self.BOARD_OFFSET_Y + self.BOARD_SIZE), 2)
            
            # Horizontal lines
            y = self.BOARD_OFFSET_Y + i * self.CELL_SIZE
            pygame.draw.line(self.screen, Colors.BLACK, 
                           (self.BOARD_OFFSET_X, y), 
                           (self.BOARD_OFFSET_X + self.BOARD_SIZE, y), 2)
        
        # Draw stones
        for row in range(GomokuGame.BOARD_SIZE):
            for col in range(GomokuGame.BOARD_SIZE):
                if self.game.board[row][col] != Player.EMPTY:
                    self._draw_stone(row, col, self.game.board[row][col])
        
        # Highlight last move
        if self.last_move_pos:
            self._highlight_last_move(self.last_move_pos[0], self.last_move_pos[1])
    
    def _draw_stone(self, row: int, col: int, player: Player):
        """Draw a stone on the board"""
        center_x = self.BOARD_OFFSET_X + col * self.CELL_SIZE + self.CELL_SIZE // 2
        center_y = self.BOARD_OFFSET_Y + row * self.CELL_SIZE + self.CELL_SIZE // 2
        radius = self.CELL_SIZE // 2 - 3
        
        color = Colors.BLACK if player == Player.BLACK else Colors.WHITE
        border_color = Colors.WHITE if player == Player.BLACK else Colors.BLACK
        
        pygame.draw.circle(self.screen, color, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, border_color, (center_x, center_y), radius, 2)
    
    def _highlight_last_move(self, row: int, col: int):
        """Highlight the last move"""
        center_x = self.BOARD_OFFSET_X + col * self.CELL_SIZE + self.CELL_SIZE // 2
        center_y = self.BOARD_OFFSET_Y + row * self.CELL_SIZE + self.CELL_SIZE // 2
        radius = self.CELL_SIZE // 2 - 1
        
        pygame.draw.circle(self.screen, Colors.RED, (center_x, center_y), radius, 3)
    
    def _draw_game_info(self):
        """Draw game information panel (adjusted for 800px width)"""
        info_x = 520  # Adjusted for new board position
        info_y = 120  # Moved up to align with new board position
        
        # Player names
        black_name = self.player_names.get(Player.BLACK, "Player 1")
        white_name = self.player_names.get(Player.WHITE, "Player 2")
        
        # Current player with name (highlighted)
        current_player_name = self.player_names.get(self.game.current_player, "Unknown")
        current_text = f"Current Player: {current_player_name}"
        current_surface = self.font_medium.render(current_text, True, Colors.TEXT_PRIMARY)
        self.screen.blit(current_surface, (info_x, info_y))
        
        # Show both players with better network game indication
        if self.is_network_game and hasattr(self, 'network_game_info'):
            # In network games, highlight your own name differently
            your_role = self.network_game_info.get('your_role', 'black')
            
            # Current player highlighting with modern colors
            black_color = Colors.SUCCESS if self.game.current_player == Player.BLACK else Colors.TEXT_PRIMARY
            white_color = Colors.SUCCESS if self.game.current_player == Player.WHITE else Colors.TEXT_PRIMARY
            
            # Add "YOU" indicator for network games
            if your_role == 'black':
                black_text = f"● {black_name} (YOU)"
                white_text = f"○ {white_name}"
            else:
                black_text = f"● {black_name}"
                white_text = f"○ {white_name} (YOU)"
        else:
            # Local games - normal highlighting with modern colors
            black_color = Colors.SUCCESS if self.game.current_player == Player.BLACK else Colors.TEXT_PRIMARY
            white_color = Colors.SUCCESS if self.game.current_player == Player.WHITE else Colors.TEXT_PRIMARY
            
            black_text = f"● {black_name}"
            white_text = f"○ {white_name}"
        
        black_surface = self.font_small.render(black_text, True, black_color)
        white_surface = self.font_small.render(white_text, True, white_color)
        
        self.screen.blit(black_surface, (info_x, info_y + 35))
        self.screen.blit(white_surface, (info_x, info_y + 55))
        
        # Move count
        move_text = f"Moves: {len(self.game.move_history)}"
        move_surface = self.font_small.render(move_text, True, Colors.TEXT_SECONDARY)
        self.screen.blit(move_surface, (info_x, info_y + 80))
        
        # Game mode
        mode_text = f"Mode: {self.game_mode.value.replace('_', ' ').title()}"
        mode_surface = self.font_small.render(mode_text, True, Colors.TEXT_SECONDARY)
        self.screen.blit(mode_surface, (info_x, info_y + 100))
        
        # AI info
        if self.game_mode == GameMode.AI_GAME and self.ai_player:
            ai_text = f"AI Difficulty: {self.ai_difficulty.title()}"
            ai_surface = self.font_small.render(ai_text, True, Colors.TEXT_SECONDARY)
            self.screen.blit(ai_surface, (info_x, info_y + 120))
            
            # Show thinking animation
            if self.ai_thinking:
                thinking_time = time.time() - self.thinking_start_time
                dots = "." * (int(thinking_time * 2) % 4)
                thinking_text = f"AI Thinking{dots}"
                
                # Add a subtle pulsing effect
                pulse = abs(math.sin(thinking_time * 3)) * 0.3 + 0.7
                thinking_color = (int(0 * pulse), int(100 * pulse), int(255 * pulse))
                thinking_surface = self.font_small.render(thinking_text, True, thinking_color)
                self.screen.blit(thinking_surface, (info_x, info_y + 140))
            else:
                stats = self.ai_player.get_statistics()
                if stats["nodes_evaluated"] > 0:
                    stats_text = f"AI Nodes: {stats['nodes_evaluated']}"
                    stats_surface = self.font_small.render(stats_text, True, Colors.GRAY)
                    self.screen.blit(stats_surface, (info_x, info_y + 140))
        
        # Network info (moved down to avoid overlap)
        if self.is_network_game:
            if self.waiting_for_network:
                network_text = "Waiting for opponent..."
                color = Colors.ERROR
            else:
                network_text = "Network Game Active"
                color = Colors.SUCCESS
            
            network_surface = self.font_small.render(network_text, True, color)
            self.screen.blit(network_surface, (info_x, info_y + 160))  # Moved from +100 to +160
    
    def _get_board_position(self, mouse_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Convert mouse position to board coordinates"""
        x, y = mouse_pos
        
        if (x < self.BOARD_OFFSET_X or x > self.BOARD_OFFSET_X + self.BOARD_SIZE or
            y < self.BOARD_OFFSET_Y or y > self.BOARD_OFFSET_Y + self.BOARD_SIZE):
            return None
        
        col = (x - self.BOARD_OFFSET_X) // self.CELL_SIZE
        row = (y - self.BOARD_OFFSET_Y) // self.CELL_SIZE
        
        if 0 <= row < GomokuGame.BOARD_SIZE and 0 <= col < GomokuGame.BOARD_SIZE:
            return (row, col)
        
        return None
    
    def _can_make_move(self) -> bool:
        """Check if the current player can make a move"""
        if self.game.game_state != GameState.PLAYING:
            return False
        
        if self.is_network_game and self.game.current_player != self.my_player:
            return False
        
        if self.game_mode == GameMode.AI_GAME and self.game.current_player != Player.BLACK:
            return False
        
        # Prevent moves while AI is thinking
        if self.ai_thinking:
            return False
        
        return True
    
    def _make_move(self, row: int, col: int):
        """Make a move on the board"""
        if self.game.make_move(row, col):
            self.last_move_pos = (row, col)
            # Reset turn timer after valid move
            self.turn_start_time = time.time()  
            self.elapsed_before_pause = 0
            
            # Send move over network if needed
            if self.is_network_game and self.network_manager:
                player_id = self.game.move_history[-1].player.value
                success = self.network_manager.send_game_move(row, col, player_id)
                if not success:
                    print("Failed to send move over network")
    
    def _handle_network_move(self, row: int, col: int):
        """Handle a move received from the network"""
        try:
            if self.game.is_valid_move(row, col):
                if self.game.make_move(row, col):
                    self.last_move_pos = (row, col)
                    # Reset turn timer after valid move
                    self.turn_start_time = time.time()
                    self.elapsed_before_pause = 0
                    print(f"Network move applied: ({row}, {col})")
                else:
                    print(f"Failed to apply network move: ({row}, {col})")
            else:
                print(f"Invalid network move received: ({row}, {col})")
        except Exception as e:
            print(f"Error handling network move: {e}")
    
    def _start_new_game(self):
        """Start a new game"""
        # Clean up any running AI threads
        self.ai_thinking = False
        self.ai_move_result = None
        if self.ai_thread and self.ai_thread.is_alive():
            # Thread will finish naturally since it's daemon
            pass
        
        self.game.reset_game()
        self.last_move_pos = None
        
        # Set player names based on game mode
        if self.game_mode == GameMode.AI_GAME:
            self.ai_player = AIPlayer(Player.WHITE, self.ai_difficulty)
            self.player_names = {
                Player.BLACK: "You",
                Player.WHITE: f"AI ({self.ai_difficulty.title()})"
            }
        elif self.game_mode == GameMode.LOCAL_PVP:
            self.ai_player = None
            self.player_names = {
                Player.BLACK: "Player 1",
                Player.WHITE: "Player 2"
            }
        elif self.game_mode == GameMode.NETWORK_GAME:
            self.ai_player = None
            # Network player names will be set by _start_network_game() after this
            self.player_names = {
                Player.BLACK: "Player 1",
                Player.WHITE: "Player 2"
            }
        else:
            self.ai_player = None
        
        self.ui_state = UIState.GAMEPLAY
    
    
    def _save_game(self):
        """Save current game state"""
        try:
            import json
            
            game_data = {
                "board": [[cell.value for cell in row] for row in self.game.board],
                "current_player": self.game.current_player.value,
                "move_history": [(move.row, move.col, move.player.value) for move in self.game.move_history],
                "game_mode": self.game_mode.value,
                "ai_difficulty": self.ai_difficulty if self.game_mode == GameMode.AI_GAME else None
            }
            
            with open("saved_game.json", "w") as f:
                json.dump(game_data, f)
            
            self.saved_game_exists = True
            print("Game saved successfully!")
            
        except Exception as e:
            print(f"Error saving game: {e}")
    
    def _load_game(self):
        """Load saved game state"""
        try:
            import json
            
            with open("saved_game.json", "r") as f:
                game_data = json.load(f)
            
            # Restore game state
            self.game.reset_game()
            
            # Restore board
            for row in range(GomokuGame.BOARD_SIZE):
                for col in range(GomokuGame.BOARD_SIZE):
                    self.game.board[row][col] = Player(game_data["board"][row][col])
            
            # Restore other state
            self.game.current_player = Player(game_data["current_player"])
            self.game_mode = GameMode(game_data["game_mode"])
            
            if game_data.get("ai_difficulty"):
                self.ai_difficulty = game_data["ai_difficulty"]
                self.ai_player = AIPlayer(Player.WHITE, self.ai_difficulty)
            
            # Restore move history
            for move_data in game_data["move_history"]:
                from gomoku_game import Move
                move = Move(move_data[0], move_data[1], Player(move_data[2]))
                self.game.move_history.append(move)
            
            if self.game.move_history:
                last_move = self.game.move_history[-1]
                self.last_move_pos = (last_move.row, last_move.col)
            
            self.ui_state = UIState.GAMEPLAY
            print("Game loaded successfully!")
            
        except Exception as e:
            print(f"Error loading game: {e}")
    
    def _resign_game(self):
        """Resign the current game"""
        if self.game.current_player == Player.BLACK:
            self.game.game_state = GameState.WHITE_WINS
            self.game.winner = Player.WHITE
        else:
            self.game.game_state = GameState.BLACK_WINS
            self.game.winner = Player.BLACK
        
        self.ui_state = UIState.GAME_OVER
    
    def _return_to_main_menu(self):
        """Return to main menu"""
        if self.network_manager:
            self.network_manager.disconnect()
            self.network_manager = None
        
        self.is_network_game = False
        self.ui_state = UIState.MAIN_MENU
    
    def _connect_to_lobby(self):
        """Connect to lobby with player name"""
        try:
            self.network_manager = StableGomokuClient()
            
            # Set up message handlers
            def handle_connect():
                print(f"Connected to lobby as {self.player_name}")
                # Join lobby with player name
                self.network_manager.join_lobby(self.player_name)
                self.ui_state = UIState.LOBBY_BROWSER
                self._refresh_room_list()
            
            def handle_disconnect():
                print("Disconnected from lobby")
                if self.ui_state in [UIState.LOBBY_BROWSER, UIState.ROOM_CREATE, UIState.ROOM_WAITING]:
                    self.ui_state = UIState.MAIN_MENU
            
            def handle_room_list(data):
                self.current_room_list = data.get("rooms", [])
                print(f"Received room list: {len(self.current_room_list)} rooms")
            
            def handle_room_info(data):
                if data.get("success"):
                    self.room_info = data.get("room_info")
                    if self.room_info:
                        print(f"Joined/Created room: {self.room_info}")
                        self.ui_state = UIState.ROOM_WAITING
                else:
                    print(f"Room operation failed: {data.get('error', 'Unknown error')}")
                    
            def handle_player_pause(data):
                sender = data.get("player", "Unknown")
                remaining_turn = data.get("remaining_turn", None)
                print(f"🔶 Received pause signal from {sender}")

                # Freeze game on both sides
                self.paused = True
                self.ui_state = UIState.PAUSE_MENU
                self.pause_start_time = time.time()
                # Record who paused — determine opponent
                if self.my_player == Player.BLACK:
                    self.pause_initiator = Player.WHITE
                else:
                    self.pause_initiator = Player.BLACK

                # Synchronize timer with sender
                if remaining_turn is not None:
                    self.turn_start_time = None
                    self.elapsed_before_pause = self.move_time_limit - remaining_turn
                    print(f"Synchronized pause — remaining turn time: {remaining_turn}s")

            def handle_player_resume(data):
                sender = data.get("player", "Unknown")
                remaining_turn = data.get("remaining_turn", None)
                print(f"▶️ Received resume signal from {sender}")

                self.paused = False
                self.pause_start_time = None
                self.ui_state = UIState.GAMEPLAY
                self.pause_initiator = None  # Reset pause owner

                # Sync countdown continuation
                if remaining_turn is not None:
                    self.elapsed_before_pause = self.move_time_limit - remaining_turn
                    self.turn_start_time = time.time()
                    print(f"Synchronized resume — remaining turn: {remaining_turn}s")
            
            def handle_game_start(data):
                print("Game starting!")
                print(f"Game start data: {data}")
                
                # Extract player role and names from server
                your_role = data.get('your_role', 'black')  # 'black' or 'white'
                your_name = data.get('your_name', self.player_name)
                opponent_name = data.get('opponent_name', 'Opponent')
                players_dict = data.get('players', {})
                your_turn = data.get('your_turn', True)
                
                # Set network game info
                self.network_game_info = {
                    'your_role': your_role,
                    'your_name': your_name,
                    'opponent_name': opponent_name,
                    'players': players_dict,
                    'your_turn': your_turn
                }
                
                print(f"You are: {your_name} ({your_role})")
                print(f"Opponent: {opponent_name}")
                print(f"Your turn: {your_turn}")
                
                self._start_network_game()
            
            def handle_game_move(data):
                print(f"Received move from {data.get('player', 'Unknown')}: ({data.get('row')}, {data.get('col')})")
                if 'row' in data and 'col' in data:
                    self._handle_network_move(data['row'], data['col'])
            
            def handle_new_game_request(data):
                print(f"Opponent requested a new game")
                # Show confirmation dialog or automatically accept
                # For now, automatically accept
                if self.network_manager:
                    self.network_manager.send_message("new_game_response", {
                        "room_id": data.get("room_id"),
                        "accepted": True
                    })
                    print("Accepted new game request")
            
            def handle_new_game_response(data):
                if data.get("accepted"):
                    print("Opponent accepted new game!")
                    self._start_network_game()
                else:
                    print("Opponent declined new game")
            
            self.network_manager.set_connection_callback("connect", handle_connect)
            self.network_manager.set_connection_callback("disconnect", handle_disconnect)
            self.network_manager.set_message_handler("room_list", handle_room_list)
            self.network_manager.set_message_handler("room_info", handle_room_info)
            self.network_manager.set_message_handler("game_started", handle_game_start)
            self.network_manager.set_message_handler("game_move", handle_game_move)
            self.network_manager.set_message_handler("new_game_request", handle_new_game_request)
            self.network_manager.set_message_handler("new_game_response", handle_new_game_response)
            self.network_manager.set_message_handler("player_pause", handle_player_pause)
            self.network_manager.set_message_handler("player_resume", handle_player_resume)
            
            # Get server configuration
            server_config = self.server_config_manager.get_current_config()
            if server_config:
                host, port = server_config.host, server_config.port
                print(f"Connecting to {server_config.name}: {host}:{port}")
                
                if self.network_manager.connect(host, port):
                    print("Connecting to lobby...")
                else:
                    print(f"Failed to connect to server {server_config.name}")
            else:
                print("No server configuration selected")
                self.ui_state = UIState.GAME_MODE_SELECT
                
        except Exception as e:
            print(f"Error connecting to lobby: {e}")
            self.ui_state = UIState.GAME_MODE_SELECT
    
    def _disconnect_from_lobby(self):
        """Disconnect from lobby"""
        if self.network_manager:
            self.network_manager.disconnect()
            self.network_manager = None
        self.ui_state = UIState.MAIN_MENU
    
    def _refresh_room_list(self):
        """Request updated room list"""
        if self.network_manager:
            self.network_manager.get_rooms()
    
    def _create_room(self, room_name: str):
        """Create a new room"""
        if self.network_manager:
            self.network_manager.create_room(room_name)
    
    def _join_room(self, room_id: str):
        """Join an existing room"""
        if self.network_manager:
            self.network_manager.join_room(room_id)
    
    def _leave_room(self):
        """Leave current room"""
        if self.network_manager:
            self.network_manager.leave_room()
            # Small delay to ensure message is sent
            import time
            time.sleep(0.1)
        
        # Clear room info and return to lobby
        self.room_info = None
        self.ui_state = UIState.LOBBY_BROWSER
        self._refresh_room_list()
    
    def _start_network_game(self):
        """Start the actual network game"""
        self.is_network_game = True
        
        # Start the game first
        self._start_new_game()
        
        # Then override with network game info if available
        if hasattr(self, 'network_game_info'):
            game_info = self.network_game_info
            
            # Set player role
            if game_info['your_role'] == 'black':
                self.my_player = Player.BLACK
            else:
                self.my_player = Player.WHITE
            
            # Set player names from server data
            players_dict = game_info.get('players', {})
            if 'black' in players_dict and 'white' in players_dict:
                self.player_names = {
                    Player.BLACK: players_dict['black'],
                    Player.WHITE: players_dict['white']
                }
            else:
                # Fallback using your_name and opponent_name
                your_name = game_info.get('your_name', 'You')
                opponent_name = game_info.get('opponent_name', 'Opponent')
                
                if game_info['your_role'] == 'black':
                    self.player_names = {
                        Player.BLACK: your_name,
                        Player.WHITE: opponent_name
                    }
                else:
                    self.player_names = {
                        Player.BLACK: opponent_name,
                        Player.WHITE: your_name
                    }
            
            print(f"Network game started:")
            print(f"  You are: {game_info['your_name']} ({game_info['your_role']})")
            print(f"  Opponent: {game_info['opponent_name']}")
            print(f"  Player names: {self.player_names}")
            print(f"  Your turn: {game_info.get('your_turn', False)}")
            
        else:
            # Fallback if no network game info
            self.my_player = Player.BLACK
            self.player_names = {
                Player.BLACK: getattr(self, 'player_name', 'Player 1'),
                Player.WHITE: "Player 2"
            }
            print(f"Set fallback player names: {self.player_names}")
    
    def _request_new_network_game(self):
        """Request a new game in network mode"""
        if self.network_manager:
            # Send new game request to server
            room_id = self.network_game_info.get('room_id') if hasattr(self, 'network_game_info') else None
            self.network_manager.send_message("new_game_request", {
                "room_id": room_id
            })
            print("Requested new game from opponent...")
            
            # Show waiting message
            # TODO: Could add a waiting state here
        else:
            # Fallback to local new game
            self._start_new_game()
    
    def _start_ai_thinking(self):
        """Start AI thinking in a separate thread"""
        if self.ai_thinking or not self.ai_player:
            return
        
        self.ai_thinking = True
        self.ai_move_result = None
        self.thinking_start_time = time.time()
        
        def ai_worker():
            try:
                # Create a copy of the game state for the AI thread
                game_copy = GomokuGame()
                game_copy.board = [row[:] for row in self.game.board]
                game_copy.current_player = self.game.current_player
                game_copy.move_history = self.game.move_history[:]
                game_copy.game_state = self.game.game_state
                
                # Get AI move
                move = self.ai_player.get_move(game_copy)
                self.ai_move_result = move
            except Exception as e:
                print(f"AI thinking error: {e}")
                self.ai_move_result = None
        
        self.ai_thread = threading.Thread(target=ai_worker, daemon=True)
        self.ai_thread.start()
        print(f"AI started thinking... (difficulty: {self.ai_difficulty})")
    
    def _update_server_buttons(self):
        """Update server selection buttons (centered for 800px width)"""
        self.buttons["server_select"] = [
            Button(300, 500, 100, 40, "Continue", self.font_small),
            Button(420, 500, 100, 40, "Back", self.font_small)
        ]
    
    def _handle_server_select_events(self, event):
        """Handle server selection events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Continue with current server
                self.ui_state = UIState.PLAYER_NAME_INPUT
                return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check server list clicks
            configs = self.server_config_manager.get_all_configs()
            start_y = 130
            
            for i, (name, config) in enumerate(configs.items()):
                y_pos = start_y + i * 60
                server_rect = pygame.Rect(100, y_pos, 400, 40)
                
                if server_rect.collidepoint(mouse_pos):
                    # Select this server
                    self.server_config_manager.set_current_config(name)
                    print(f"Selected server: {name}")
                    break
            
            # Check buttons
            buttons = self.buttons["server_select"]
            for i, button in enumerate(buttons):
                if button.handle_event(event):
                    if i == 0:  # Continue
                        self.ui_state = UIState.PLAYER_NAME_INPUT
                    elif i == 1:  # Back
                        self.ui_state = UIState.GAME_MODE_SELECT


def main():
    """Main function to run the game"""
    game_ui = GomokuUI()
    game_ui.run()


if __name__ == "__main__":
    main()
