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

# Initialize pygame mixer for sounds
pygame.mixer.init()


class UIState(Enum):
    """UI state enumeration"""
    MAIN_MENU = "main_menu"
    GAME_MODE_SELECT = "game_mode_select"
    AI_DIFFICULTY_SELECT = "ai_difficulty_select"
    AI_PLAYER_COUNT_SELECT = "ai_player_count_select"
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
    ABOUT = "about"
    CONNECTION_LOST = "connection_lost"
    OPPONENT_DISCONNECTED = "opponent_disconnected"


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
    """Modern button class with improved UI/UX"""
    
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
        self.hover_alpha = 0
    
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
        """Draw the button with modern effects"""
        # Update hover animation
        if self.hovered and self.enabled:
            self.hover_alpha = min(255, self.hover_alpha + 15)
        else:
            self.hover_alpha = max(0, self.hover_alpha - 15)
        
        # Base button color
        if not self.enabled:
            base_color = Colors.GRAY
        else:
            base_color = self.color
        
        # Draw shadow for depth
        shadow_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 3, self.rect.width, self.rect.height)
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height))
        shadow_surface.set_alpha(30)
        shadow_surface.fill(Colors.BLACK)
        screen.blit(shadow_surface, shadow_rect)
        
        # Draw button with rounded corners effect (using gradient-like border)
        pygame.draw.rect(screen, base_color, self.rect)
        
        # Hover effect with smooth transition
        if self.hover_alpha > 0 and self.enabled:
            hover_overlay = pygame.Surface((self.rect.width, self.rect.height))
            hover_overlay.set_alpha(self.hover_alpha // 2)
            hover_color = (min(255, base_color[0] + 20), 
                          min(255, base_color[1] + 20), 
                          min(255, base_color[2] + 20))
            hover_overlay.fill(hover_color)
            screen.blit(hover_overlay, self.rect)
        
        # Modern border (thinner, softer)
        border_color = Colors.ACCENT if self.hovered and self.enabled else Colors.DARK_GRAY
        border_alpha = 200 if self.hovered and self.enabled else 100
        border_surface = pygame.Surface((self.rect.width, self.rect.height))
        border_surface.set_alpha(border_alpha)
        pygame.draw.rect(border_surface, border_color, border_surface.get_rect(), 2)
        screen.blit(border_surface, self.rect)
        
        # Text with shadow for better readability
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        
        # Text shadow
        shadow_text = self.font.render(self.text, True, (0, 0, 0))
        shadow_rect = text_rect.copy()
        shadow_rect.x += 1
        shadow_rect.y += 1
        shadow_surf = pygame.Surface(shadow_text.get_size())
        shadow_surf.set_alpha(50)
        shadow_surf.fill((0, 0, 0))
        screen.blit(shadow_text, shadow_rect)
        
        # Main text
        screen.blit(text_surface, text_rect)


class GomokuUI:
    """Main UI class for Gomoku game"""
    
    def __init__(self):
        pygame.init()
        
        # Screen settings (original size)
        self.WINDOW_WIDTH = 800   # Original size
        self.WINDOW_HEIGHT = 600  # Original size
        self.BOARD_SIZE = 450  # Original board size
        self.BOARD_OFFSET_X = 60
        self.BOARD_OFFSET_Y = 100
        self.CELL_SIZE = self.BOARD_SIZE // GomokuGame.BOARD_SIZE
        
        # Center the window on screen
        import os
        os.environ['SDL_VIDEO_WINDOW_POS'] = 'centered'
        
        # Initialize display
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Gomoku - Five in a Row")
        
        # Initialize fonts (increased sizes for better visibility)
        self.font_large = pygame.font.Font(None, 56)   # Increased from 42
        self.font_medium = pygame.font.Font(None, 36)  # Increased from 28
        self.font_small = pygame.font.Font(None, 28)   # Increased from 22
        self.font_info = pygame.font.Font(None, 32)    # New: for game info
        
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
        self.move_time_limit = 30  # seconds (changed from 20 to 30)
        self.elapsed_before_pause = 0  # how much time elapsed before pausing

        # Pause control per player
        self.paused = False
        self.pause_sent = False
        self.pause_start_time = None
        self.pause_allowance = {Player.BLACK: 2, Player.WHITE: 2}  # tokens
        self.per_pause_limit = 30  # seconds (limit per individual pause, not cumulative)
        self.show_pause_info = False  # Toggle for showing/hiding pause info
        
        # AI threading
        self.ai_thinking = False
        self.ai_thread = None
        self.ai_move_result = None
        self.thinking_start_time = 0
        self.my_player = Player.BLACK
        self.waiting_for_network = False
        
        # Pause info toggle button
        self.pause_icon_rect = pygame.Rect(10, 10, 32, 32)  # Position and size of the icon
        self.pause_icon_color = (200, 200, 200)  # Light gray color for the icon
        self.show_all_players = False  # Whether to show all players or just current
        
        # AI Debug viewer
        self.ai_debug_enabled = False  # Toggle with 'D' key
        self.ai_debug_stats = None  # Store last AI statistics
        
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
        
        # Room & reconnection state
        self.room_id = None
        self.reconnect_info = None
        
        # Disconnection tracking
        self.opponent_disconnect_time = None
        self.opponent_disconnect_timeout = 120  # seconds (not used with graceful termination)
        self.reconnection_attempt = 0
        self.max_reconnection_attempts = 12
        self.disconnect_reason = ""
        self.is_disconnect_win = False  # Track if game ended due to opponent disconnect
        
        # Text input state
        self.text_input_active = False
        self.text_input_content = ""
        self.text_input_prompt = ""
        
        # Clock for FPS
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Sound system
        self.sounds_enabled = True
        self.music_enabled = True
        self.sounds = {}
        self.background_music = None
        self._load_sounds()
        
        # Background images
        self.background_images = {}
        self._load_background_images()
        
        # Start background music automatically
        self._play_background_music()
        
        # Initialize UI elements
        self._init_ui_elements()
    
    def check_saved_game(self):
        """Check if a saved game exists"""
        self.saved_game_exists = os.path.exists("saved_game.json")
    
    def _load_sounds(self):
        """Load all sound files"""
        sound_dir = os.path.join(os.path.dirname(__file__), "sounds")
        try:
            # Load sound effects
            board_start_path = os.path.join(sound_dir, "board-start-38127.mp3")
            winner_path = os.path.join(sound_dir, "winner-game-sound-404167.mp3")
            play_turn_path = os.path.join(sound_dir, "play_turn.mp3")
            background_path = os.path.join(sound_dir, "calm-nature-sounds-196258.mp3")
            
            if os.path.exists(board_start_path):
                self.sounds["board_start"] = pygame.mixer.Sound(board_start_path)
            if os.path.exists(winner_path):
                self.sounds["winner"] = pygame.mixer.Sound(winner_path)
            if os.path.exists(play_turn_path):
                self.sounds["play_turn"] = pygame.mixer.Sound(play_turn_path)
            if os.path.exists(background_path):
                self.background_music = background_path
            
            print("✅ Sounds loaded successfully")
        except Exception as e:
            print(f"⚠️ Error loading sounds: {e}")
            self.sounds = {}
            self.background_music = None
    
    def _load_background_images(self):
        """Load background images"""
        img_dir = os.path.join(os.path.dirname(__file__), "imgs")
        try:
            # Load start image
            start_image_path = os.path.join(img_dir, "image_start.jpg")
            if os.path.exists(start_image_path):
                self.background_images["start"] = pygame.image.load(start_image_path)
                # Scale to window size
                self.background_images["start"] = pygame.transform.scale(
                    self.background_images["start"], 
                    (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
                )
            
            # Load game image
            game_image_path = os.path.join(img_dir, "image_game.webp")
            if os.path.exists(game_image_path):
                self.background_images["game"] = pygame.image.load(game_image_path)
                # Scale to window size
                self.background_images["game"] = pygame.transform.scale(
                    self.background_images["game"], 
                    (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
                )
            
            print("✅ Background images loaded successfully")
        except Exception as e:
            print(f"⚠️ Error loading background images: {e}")
            self.background_images = {}
    
    def _play_sound(self, sound_name: str):
        """Play a sound effect if sounds are enabled"""
        if not self.sounds_enabled:
            return
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception as e:
                print(f"⚠️ Error playing sound {sound_name}: {e}")
    
    def _play_background_music(self):
        """Start playing background music if music is enabled"""
        if not self.music_enabled:
            print("🔇 Background music disabled by user")
            return
        if not self.background_music:
            print("⚠️ No background music file set")
            return
        if not os.path.exists(self.background_music):
            print(f"⚠️ Background music file not found: {self.background_music}")
            return
            
        try:
            # Only start music if it's not already playing
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(self.background_music)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                pygame.mixer.music.set_volume(0.3)  # Lower volume for background
                print(f"🎵 Background music started: {os.path.basename(self.background_music)}")
            else:
                print("🎵 Background music already playing")
        except Exception as e:
            print(f"⚠️ Error playing background music: {e}")
    
    def _stop_background_music(self):
        """Stop background music"""
        try:
            pygame.mixer.music.stop()
        except:
            pass
    
    def _draw_gradient_background(self, use_image=None):
        """Draw a modern gradient background with optional image"""
        # Determine which background to use
        if use_image == "start" and "start" in self.background_images:
            # Draw start image with overlay
            self.screen.blit(self.background_images["start"], (0, 0))
            # Add dark overlay for better text readability
            overlay = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
            overlay.set_alpha(120)  # Darker overlay for start screen
            overlay.fill(Colors.BLACK)
            self.screen.blit(overlay, (0, 0))
        elif use_image == "game" and "game" in self.background_images:
            # Draw game image with subtle overlay
            self.screen.blit(self.background_images["game"], (0, 0))
            # Add subtle overlay for better visibility
            overlay = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
            overlay.set_alpha(60)  # Lighter overlay for gameplay
            overlay.fill(Colors.BLACK)
            self.screen.blit(overlay, (0, 0))
        else:
            # Default gradient background
            # Fill with base color first (faster)
            self.screen.fill(Colors.BACKGROUND)
            
            # Add enhanced gradient overlay with more depth
            overlay = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
            overlay.set_alpha(50)  # Increased alpha for more visible effect
            for y in range(0, self.WINDOW_HEIGHT, 2):  # More lines for smoother gradient
                ratio = y / self.WINDOW_HEIGHT
                # More pronounced gradient
                color_val = int(255 * ratio * 0.15)
                pygame.draw.line(overlay, (color_val, color_val, color_val), 
                               (0, y), (self.WINDOW_WIDTH, y), 2)
            self.screen.blit(overlay, (0, 0))
            
            # Add subtle vignette effect (darkened edges) - optimized
            edge_overlay = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
            edge_overlay.set_alpha(10)
            edge_overlay.fill((0, 0, 0))
            # Create gradient edges by drawing rectangles with decreasing alpha
            edge_width = 50
            for i in range(edge_width):
                alpha = int(10 * (1 - i / edge_width))
                if alpha > 0:
                    edge_surf = pygame.Surface((self.WINDOW_WIDTH, 1))
                    edge_surf.set_alpha(alpha)
                    edge_surf.fill((0, 0, 0))
                    # Top edge
                    self.screen.blit(edge_surf, (0, i))
                    # Bottom edge
                    self.screen.blit(edge_surf, (0, self.WINDOW_HEIGHT - 1 - i))
                    
                    edge_surf = pygame.Surface((1, self.WINDOW_HEIGHT))
                    edge_surf.set_alpha(alpha)
                    edge_surf.fill((0, 0, 0))
                    # Left edge
                    self.screen.blit(edge_surf, (i, 0))
                    # Right edge
                    self.screen.blit(edge_surf, (self.WINDOW_WIDTH - 1 - i, 0))
    
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list:
        """Wrap text to fit within max_width"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            test_surface = font.render(test_line, True, (0, 0, 0))
            
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines
    
    def _init_ui_elements(self):
        """Initialize UI elements for different states"""
        # Main menu buttons (centered for 800px width)
        self.buttons["main_menu"] = [
            Button(300, 200, 200, 50, "New Game", self.font_medium),
            Button(300, 270, 200, 50, "Continue", self.font_medium),
            Button(300, 340, 200, 50, "Settings", self.font_medium),
            Button(300, 410, 200, 50, "About", self.font_medium),
            Button(300, 480, 200, 50, "Quit", self.font_medium)
        ]
        
        # About page buttons
        self.buttons["about"] = [
            Button(300, 500, 200, 50, "Back", self.font_medium)
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
        
        # AI player count selection buttons (for multiple AI opponents)
        self.buttons["ai_player_count"] = [
            Button(250, 180, 300, 50, "2 Players (1 vs 1)", self.font_medium),
            Button(250, 250, 300, 50, "3 Players (1 vs 2 AI)", self.font_medium),
            Button(250, 320, 300, 50, "4 Players (1 vs 3 AI)", self.font_medium),
            Button(250, 390, 300, 50, "5 Players (1 vs 4 AI)", self.font_medium),
            Button(300, 480, 200, 50, "Back", self.font_medium)
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
            elif self.ui_state == UIState.AI_PLAYER_COUNT_SELECT:
                self._handle_ai_player_count_events(event)
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
            elif self.ui_state == UIState.ABOUT:
                self._handle_about_events(event)
            elif self.ui_state == UIState.OPPONENT_DISCONNECTED:
                self._handle_opponent_disconnected_events(event)
    
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
                elif i == 3:  # About
                    self.ui_state = UIState.ABOUT
                elif i == 4:  # Quit
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
                    self.num_ai_players = 2  # Reset to default
                    self.ui_state = UIState.AI_PLAYER_COUNT_SELECT
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
                    if self.num_ai_players > 2:
                        self.ui_state = UIState.AI_PLAYER_COUNT_SELECT
                    else:
                        self.ui_state = UIState.GAME_MODE_SELECT
    
    def _handle_ai_player_count_events(self, event):
        """Handle AI player count selection events"""
        buttons = self.buttons["ai_player_count"]
        
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i < 4:  # Player count selection (2, 3, 4, 5)
                    self.num_ai_players = i + 2  # 2, 3, 4, or 5 players
                    self.ui_state = UIState.AI_DIFFICULTY_SELECT
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
        # Handle mouse clicks for pause info toggle
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                if self.pause_icon_rect.collidepoint(event.pos):
                    self.show_all_players = not self.show_all_players
                    return  # Skip other button handling if we toggled pause info
        
        # Handle keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:  # Toggle AI debug view
                self.ai_debug_enabled = not self.ai_debug_enabled
                print(f"🔍 AI Debug View: {'ON' if self.ai_debug_enabled else 'OFF'}")
            elif event.key == pygame.K_p:  # Toggle between showing all players and current player only
                self.show_all_players = not self.show_all_players
        
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
                        self.pause_sent = True
                        self.ui_state = UIState.PAUSE_MENU
                        self.pause_start_time = time.time()
                        self.pause_allowance[self.game.current_player] -= 1  # consume 1 token

                        # Freeze/Sync the move timer
                        if self.turn_start_time:
                            elapsed_time = time.time() - self.turn_start_time
                            self.elapsed_before_pause += elapsed_time
                            self.turn_start_time = None

                        if self.is_network_game and self.network_manager:
                            # Share the remaining move time (not pause limit)
                            remaining_turn = max(0, self.move_time_limit - self.elapsed_before_pause)
                            pause_timestamp = time.time()  # Record when pause was initiated
                            self.network_manager.send_message("player_pause", {
                                "player": self.player_names[self.game.current_player],
                                "remaining_turn": remaining_turn,
                                "pauses_remaining": self.pause_allowance[self.game.current_player],  # Send updated pause count
                                "pause_timestamp": pause_timestamp  # Send pause initiation timestamp
                            })
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
                    # Only initiator can resume (in network games)
                    if self.is_network_game and self.my_player != self.pause_initiator:
                        print(f"⏸ You cannot resume — waiting for {self.player_names[self.pause_initiator]} to resume.")
                        return

                    # Clear pause state
                    self.paused = False
                    self.pause_start_time = None
                    self.pause_sent = False  # allow future pauses again

                    # Resume move timer from where it left off
                    remaining_turn = max(0, self.move_time_limit - self.elapsed_before_pause)
                    self.turn_start_time = time.time()

                    # Calculate how long we were paused (for synchronization)
                    pause_duration_used = 0
                    if self.pause_start_time:
                        pause_duration_used = time.time() - self.pause_start_time

                    self.ui_state = UIState.GAMEPLAY
                    
                    # Play board start sound when resuming
                    self._play_sound("board_start")

                    # Notify opponent when resuming
                    if self.is_network_game and self.network_manager:
                        self.network_manager.send_message("player_resume", {
                            "player": self.player_names[self.game.current_player],
                            "remaining_turn": remaining_turn,
                            "pause_duration_used": pause_duration_used  # Send how long we paused
                        })
                elif i == 1:  # Save Game
                    # Only allow save in Local PvP mode
                    if self.game_mode == GameMode.LOCAL_PVP:
                        self._save_game()
                elif i == 2:  # Main Menu
                    self._return_to_main_menu()

    
    def _handle_game_over_events(self, event):
        """Handle game over events"""
        buttons = self.buttons["game_over"]
        
        # For disconnect wins, only handle main menu button
        if self.is_disconnect_win:
            # Only the last button (Main Menu) is available
            if len(buttons) > 0:
                main_menu_button = buttons[-1]
                main_menu_button.enabled = True
                if main_menu_button.handle_event(event):
                    print(f"🔍 DEBUG: Disconnect win Main Menu clicked")
                    print(f"🔍 DEBUG: is_network_game = {self.is_network_game}")
                    print(f"🔍 DEBUG: game_mode = {self.game_mode}")
                    print(f"🔍 DEBUG: network_manager = {self.network_manager}")
                    print(f"🔍 DEBUG: room_info = {getattr(self, 'room_info', None)}")
                    
                    # Check if we're in a network game by mode OR by network_manager presence
                    if self.is_network_game or self.game_mode == GameMode.NETWORK_GAME:
                        # For disconnect wins in network games:
                        # Winner stays in room and becomes host (opponent already disconnected)
                        # Reset game and return to waiting room as the host
                        self.game.reset_game()
                        self.ui_state = UIState.ROOM_WAITING
                        self._stop_background_music()
                        print(f"📋 Returned to waiting room as host after opponent disconnect")
                    else:
                        self.ui_state = UIState.MAIN_MENU
                    self.is_disconnect_win = False  # Reset flag
            return
        
        # Normal game over handling (no disconnect)
        # Ensure buttons are enabled
        for button in buttons:
            button.enabled = True
        
        # Handle button clicks
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # New Game
                    if self.is_network_game:
                        # In network games, need to coordinate with other player
                        self._request_new_network_game()
                    else:
                        # Local games can start immediately
                        self._start_new_game()
                    return  # Exit after handling
                elif i == 1:  # Main Menu
                    if self.is_network_game:
                        # In network games, leaving from game over means:
                        # - Player who clicks leaves the room
                        # - Other player becomes host and goes back to waiting room
                        if self.network_manager:
                            self.network_manager.leave_room()
                        # Then disconnect and return to main menu
                        self._return_to_main_menu()
                    else:
                        self.ui_state = UIState.MAIN_MENU
                    return  # Exit after handling
    
    def _handle_settings_events(self, event):
        """Handle settings events"""
        buttons = self.buttons["settings"]
        
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # Sound toggle
                    # Toggle sound setting
                    self.sounds_enabled = not self.sounds_enabled
                    if self.sounds_enabled:
                        button.text = "Sound: On"
                    else:
                        button.text = "Sound: Off"
                elif i == 1:  # Music toggle
                    # Toggle music setting
                    self.music_enabled = not self.music_enabled
                    if self.music_enabled:
                        button.text = "Music: On"
                        self._play_background_music()
                    else:
                        button.text = "Music: Off"
                        self._stop_background_music()
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
    
    def _handle_opponent_disconnected_events(self, event):
        """Handle opponent disconnected screen events"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if "Leave Game" button was clicked
            button_width = 200
            button_height = 50
            button_x = (self.WINDOW_WIDTH - button_width) // 2
            button_y = 520
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            if button_rect.collidepoint(event.pos):
                # Leave the game and return to main menu
                self._leave_room()
                self.opponent_disconnect_time = None
                self.ui_state = UIState.MAIN_MENU
    
    def _handle_escape_key(self):
        """Handle ESC key press for navigation"""
        if self.ui_state == UIState.GAME_MODE_SELECT:
            self.ui_state = UIState.MAIN_MENU
        elif self.ui_state == UIState.AI_DIFFICULTY_SELECT:
            if self.num_ai_players > 2:
                self.ui_state = UIState.AI_PLAYER_COUNT_SELECT
            else:
                self.ui_state = UIState.GAME_MODE_SELECT
        elif self.ui_state == UIState.AI_PLAYER_COUNT_SELECT:
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
        elif self.ui_state == UIState.ABOUT:
            self.ui_state = UIState.MAIN_MENU
        elif self.ui_state == UIState.OPPONENT_DISCONNECTED:
            # Allow leaving game when opponent is disconnected
            self._leave_room()
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
                print(f"⏰ Player {self.game.current_player.name} exceeded 30 s — auto-resign.")
                # For network games, make sure we're resigning the correct player
                if self.is_network_game:
                    # In network games, only timeout if it's our turn
                    if self.game.current_player == self.my_player:
                        self._resign_game()
                    else:
                        # It's opponent's turn - they should timeout on their side
                        # But if they don't respond, we might need server-side timeout
                        print(f"⏰ Waiting for opponent {self.game.current_player.name} to timeout...")
                else:
                    # Local game - resign current player (they lose)
                    self._resign_game()
                self.turn_start_time = None
                self.elapsed_before_pause = 0
                return
        if self.ui_state == UIState.GAMEPLAY:
            # Handle AI moves (for single or multiple AI players)
            if (self.game_mode == GameMode.AI_GAME and 
                self.game.current_player != Player.BLACK and 
                self.game.game_state == GameState.PLAYING):
                
                # Get the AI player for current player
                current_ai = self.ai_players.get(self.game.current_player)
                if not current_ai and self.ai_player and self.game.current_player == Player.WHITE:
                    current_ai = self.ai_player  # Fallback for backward compatibility
                
                if current_ai:
                    # Start AI thinking if not already started
                    if not self.ai_thinking and (self.ai_thread is None or not self.ai_thread.is_alive()):
                        self._start_ai_thinking(current_ai)
                    
                    # Check if AI has finished thinking
                    elif self.ai_thinking and self.ai_move_result is not None:
                        move = self.ai_move_result
                        self.ai_move_result = None
                        self.ai_thinking = False
                        
                        # Store AI debug statistics
                        if current_ai:
                            self.ai_debug_stats = current_ai.get_statistics()
                            # Print debug info to console
                            if self.ai_debug_stats:
                                print("\n" + "="*60)
                                print(f"🔍 AI DEBUG STATISTICS ({self.game.current_player.name})")
                                print("="*60)
                                print(f"Nodes Evaluated: {self.ai_debug_stats['nodes_evaluated']}")
                                print(f"Pruning Count: {self.ai_debug_stats['pruning_count']}")
                                print(f"Pruning Efficiency: {self.ai_debug_stats['pruning_efficiency']:.2f}%")
                                print(f"Max Depth Reached: {self.ai_debug_stats['max_depth_reached']}")
                                print(f"Search Time: {self.ai_debug_stats['search_time']:.3f}s")
                                print(f"Nodes/Second: {self.ai_debug_stats['nodes_per_second']:.0f}")
                                if self.ai_debug_stats['nodes_by_depth']:
                                    print("\nNodes by Depth:")
                                    for depth, count in sorted(self.ai_debug_stats['nodes_by_depth'].items()):
                                        print(f"  Depth {depth}: {count} nodes")
                                if self.ai_debug_stats['move_evaluations']:
                                    print("\nTop Move Evaluations:")
                                    sorted_moves = sorted(self.ai_debug_stats['move_evaluations'], 
                                                        key=lambda x: x['score'], reverse=True)
                                    for i, eval_info in enumerate(sorted_moves[:5]):  # Show top 5
                                        move_info = eval_info['move']
                                        print(f"  {i+1}. Move ({move_info[0]}, {move_info[1]}): Score={eval_info['score']:.1f}, "
                                              f"Alpha={eval_info['alpha']:.1f}, Beta={eval_info['beta']:.1f}")
                                print("="*60 + "\n")
                        
                        if move:
                            self._make_move(move[0], move[1])
            
            # Check for game over
            if self.game.game_state != GameState.PLAYING:
                if self.ui_state == UIState.GAMEPLAY:  # Only transition once
                    self.ui_state = UIState.GAME_OVER
                    # Play winner sound when game ends
                    if self.game.game_state in [GameState.BLACK_WINS, GameState.WHITE_WINS]:
                        self._play_sound("winner")
        # While paused, auto-resume after per-pause limit (no cumulative depletion)
        if self.paused and self.pause_start_time:
            elapsed_pause = time.time() - self.pause_start_time
            if elapsed_pause >= self.per_pause_limit:
                print("Pause expired automatically")
                self.paused = False
                self.pause_start_time = None
                self.pause_sent = False
                self.ui_state = UIState.GAMEPLAY

                # Resume move timer from where it left off
                self.turn_start_time = time.time()
    
    def _draw(self):
        """Draw the current UI state with modern effects"""
        # Determine which background to use
        if self.ui_state == UIState.GAMEPLAY or self.ui_state == UIState.PAUSE_MENU or self.ui_state == UIState.GAME_OVER:
            # Use game background during gameplay
            self._draw_gradient_background(use_image="game")
        else:
            # Use start background for menus
            self._draw_gradient_background(use_image="start")
        
        if self.ui_state == UIState.MAIN_MENU:
            self._draw_main_menu()
        elif self.ui_state == UIState.GAME_MODE_SELECT:
            self._draw_game_mode_select()
        elif self.ui_state == UIState.AI_DIFFICULTY_SELECT:
            self._draw_ai_difficulty_select()
        elif self.ui_state == UIState.AI_PLAYER_COUNT_SELECT:
            self._draw_ai_player_count_select()
        elif self.ui_state == UIState.GAMEPLAY:
            self._draw_gameplay()
        elif self.ui_state == UIState.PAUSE_MENU:
            self._draw_pause_menu()
        elif self.ui_state == UIState.GAME_OVER:
            self._draw_game_over()
        elif self.ui_state == UIState.SETTINGS:
            self._draw_settings()
        elif self.ui_state == UIState.ABOUT:
            self._draw_about()
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
        elif self.ui_state == UIState.CONNECTION_LOST:
            self._draw_connection_lost()
        elif self.ui_state == UIState.OPPONENT_DISCONNECTED:
            self._draw_opponent_disconnected()
            
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
            timer_rect = pygame.Rect(self.WINDOW_WIDTH - 180, 20, 130, 50)  # Increased height
            # Background panel for better visibility
            timer_bg = pygame.Surface((timer_rect.width, timer_rect.height))
            timer_bg.set_alpha(240)
            timer_bg.fill((20, 20, 30))  # Dark background
            self.screen.blit(timer_bg, timer_rect)
            pygame.draw.rect(self.screen, color, timer_rect, 3)  # Thicker border
            # Text with shadow
            timer_shadow = self.font_medium.render(f"{remaining:02d}s", True, (0, 0, 0))
            timer_shadow_rect = timer_shadow.get_rect(center=(timer_rect.centerx + 1, timer_rect.centery + 1))
            self.screen.blit(timer_shadow, timer_shadow_rect)
            timer_text = self.font_medium.render(f"{remaining:02d}s", True, color)
            self.screen.blit(timer_text, timer_text.get_rect(center=timer_rect.center))

            # Draw list icon button
            button_color = (100, 100, 100, 180) if not self.show_pause_info else (70, 130, 180, 220)
            button_surface = pygame.Surface((self.pause_icon_rect.width, self.pause_icon_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, button_color, (0, 0, self.pause_icon_rect.width, self.pause_icon_rect.height), 0, 5)
            
            # Draw list icon (three horizontal lines)
            line_height = 2
            line_gap = 4
            line_width = 16
            
            # Draw three horizontal lines
            for i in range(3):
                y_pos = self.pause_icon_rect.height // 2 - line_gap + (i * (line_height + line_gap)) - 2
                pygame.draw.rect(button_surface, (255, 255, 255), 
                               ((self.pause_icon_rect.width - line_width) // 2, y_pos, 
                                line_width, line_height), 0, 2)
            
            self.screen.blit(button_surface, self.pause_icon_rect)
            
            # === Pause info boxes (moved to the right to avoid icon) ===
            if True:  # Always show at least the current player
                y = 10
                box_width = 220  # Increased width
                box_height = 42  # Increased height
                x_offset = 45  # Move right to avoid overlapping with list icon
                
                # Get players to show (current player only or all players)
                if hasattr(self.game, 'players') and self.game.players:
                    players_to_show = self.game.players if self.show_all_players else [self.game.current_player]
                else:
                    # Fallback for 2-player games
                    players_to_show = [Player.BLACK, Player.WHITE] if self.show_all_players else [self.game.current_player]
                
                for player in players_to_show:
                    # Skip if player doesn't have pause allowance (shouldn't happen, but safety check)
                    if player not in self.pause_allowance:
                        continue
                        
                    label = self.player_names.get(player, f"Player {player.name}")
                    pauses_left = self.pause_allowance[player]
                    pause_time = self.per_pause_limit  # constant per pause, not a running pool

                    pause_rect = pygame.Rect(20 + x_offset, y, box_width, box_height)
                    
                    # Background panel for better visibility
                    pause_bg = pygame.Surface((pause_rect.width, pause_rect.height))
                    pause_bg.set_alpha(240)
                    pause_bg.fill((20, 20, 30))  # Dark background
                    self.screen.blit(pause_bg, pause_rect)
                    
                    # Highlight current player's box with colored border
                    if self.game.current_player == player:
                        pygame.draw.rect(self.screen, Colors.SUCCESS, pause_rect, 3)  # Green border for current player
                    else:
                        pygame.draw.rect(self.screen, Colors.WHITE, pause_rect, 2)  # White border for others

                    pause_text = f"{label}: {pauses_left}× {pause_time}s"
                    # Text with shadow
                    text_shadow = self.font_info.render(pause_text, True, (0, 0, 0))
                    text_shadow_rect = text_shadow.get_rect(center=(pause_rect.centerx + 1, pause_rect.centery + 1))
                    self.screen.blit(text_shadow, text_shadow_rect)
                    
                    # Highlight current player's text
                    text_color = Colors.SUCCESS if self.game.current_player == player else Colors.WHITE
                    text_surface = self.font_info.render(pause_text, True, text_color)
                    self.screen.blit(text_surface, text_surface.get_rect(center=pause_rect.center))
                    
                    y += box_height + 8
        pygame.display.flip()
    
    def _draw_main_menu(self):
        """Draw main menu with modern effects"""
        # Enhanced title with multiple shadow layers for depth
        title_text = "GOMOKU"
        
        # Multiple shadow layers for 3D effect
        for offset in [(3, 3), (2, 2), (1, 1)]:
            title_shadow = self.font_large.render(title_text, True, (0, 0, 0))
            title_shadow_rect = title_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + offset[0], 100 + offset[1]))
            shadow_surf = pygame.Surface(title_shadow.get_size())
            shadow_surf.set_alpha(40 // offset[0])
            shadow_surf.fill((0, 0, 0))
            self.screen.blit(title_shadow, title_shadow_rect)
        
        # Main title with gradient-like effect (brighter)
        title = self.font_large.render(title_text, True, Colors.WHITE)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Glow effect around title
        glow_surf = pygame.Surface((title_rect.width + 20, title_rect.height + 20))
        glow_surf.set_alpha(30)
        glow_surf.fill(Colors.ACCENT)
        glow_rect = glow_surf.get_rect(center=title_rect.center)
        self.screen.blit(glow_surf, glow_rect)
        
        # Subtitle with modern styling and shadow
        subtitle_shadow = self.font_medium.render("Five in a Row", True, (0, 0, 0))
        subtitle_shadow_rect = subtitle_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 1, 141))
        self.screen.blit(subtitle_shadow, subtitle_shadow_rect)
        
        subtitle = self.font_medium.render("Five in a Row", True, Colors.WHITE)
        subtitle_rect = subtitle.get_rect(center=(self.WINDOW_WIDTH // 2, 140))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Enhanced decorative line with glow
        line_y = 155
        # Glow line
        for i in range(3):
            alpha = 20 - i * 5
            glow_line = pygame.Surface((200, 3))
            glow_line.set_alpha(alpha)
            glow_line.fill(Colors.ACCENT)
            self.screen.blit(glow_line, (self.WINDOW_WIDTH // 2 - 100, line_y - 1 + i))
        # Main line
        pygame.draw.line(self.screen, Colors.ACCENT, 
                        (self.WINDOW_WIDTH // 2 - 100, line_y),
                        (self.WINDOW_WIDTH // 2 + 100, line_y), 3)
        
        # Buttons with modern effects
        for button in self.buttons["main_menu"]:
            button.draw(self.screen)
    
    def _draw_game_mode_select(self):
        """Draw game mode selection with enhanced visibility"""
        # Title with shadow and better contrast
        title_text = "Select Game Mode"
        title_shadow = self.font_large.render(title_text, True, (0, 0, 0))
        title_shadow_rect = title_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 2, 102))
        self.screen.blit(title_shadow, title_shadow_rect)
        
        title = self.font_large.render(title_text, True, Colors.WHITE)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        for button in self.buttons["game_mode"]:
            button.draw(self.screen)
    
    def _draw_ai_difficulty_select(self):
        """Draw AI difficulty selection with enhanced visibility"""
        # Title with shadow and better contrast
        title_text = "Select AI Difficulty"
        title_shadow = self.font_large.render(title_text, True, (0, 0, 0))
        title_shadow_rect = title_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 2, 102))
        self.screen.blit(title_shadow, title_shadow_rect)
        
        title = self.font_large.render(title_text, True, Colors.WHITE)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        for button in self.buttons["ai_difficulty"]:
            button.draw(self.screen)
    
    def _draw_ai_player_count_select(self):
        """Draw AI player count selection screen"""
        # Title with shadow and better contrast
        title_text = "Select Number of Players"
        title_shadow = self.font_large.render(title_text, True, (0, 0, 0))
        title_shadow_rect = title_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 2, 102))
        self.screen.blit(title_shadow, title_shadow_rect)
        
        title = self.font_large.render(title_text, True, Colors.WHITE)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle_text = "You will be Player 1 (Black). Others will be AI opponents."
        subtitle_shadow = self.font_small.render(subtitle_text, True, (0, 0, 0))
        subtitle_shadow_rect = subtitle_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 1, 151))
        self.screen.blit(subtitle_shadow, subtitle_shadow_rect)
        
        subtitle = self.font_small.render(subtitle_text, True, Colors.WHITE)
        subtitle_rect = subtitle.get_rect(center=(self.WINDOW_WIDTH // 2, 150))
        self.screen.blit(subtitle, subtitle_rect)
        
        for button in self.buttons["ai_player_count"]:
            button.draw(self.screen)
    
    
    def _draw_gameplay(self):
        """Draw gameplay screen"""
        # Draw the game board
        self._draw_board()
        
        # Draw game info panel
        self._draw_game_info()
        
        # Draw AI debug panel if enabled
        if self.ai_debug_enabled and self.ai_player:
            self._draw_ai_debug_panel()
            
        # Draw pause menu if game is paused
        if self.paused:
            self._draw_pause_menu()
            
        
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
            elapsed_pause = time.time() - self.pause_start_time
            remaining_pause = max(0, int(self.per_pause_limit - elapsed_pause))

            pause_rect = pygame.Rect(self.WINDOW_WIDTH // 2 - 80, 180, 160, 50)
            pygame.draw.rect(self.screen, Colors.BACKGROUND, pause_rect)
            pygame.draw.rect(self.screen, Colors.WARNING, pause_rect, 2)

            pause_text = self.font_medium.render(f"Pause: {remaining_pause:02d}s", True, Colors.WARNING)
            self.screen.blit(pause_text, pause_text.get_rect(center=pause_rect.center))

        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Draw buttons based on game mode
        # Hide "Save Game" button for AI and Network games (only allow for Local PvP)
        for i, button in enumerate(self.buttons["pause_menu"]):
            # Skip "Save Game" button (index 1) for AI and Network games
            if i == 1 and (self.game_mode == GameMode.AI_GAME or self.game_mode == GameMode.NETWORK_GAME):
                continue  # Don't draw Save Game button
            
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
        if self.game.winner:
            winner_name = self.player_names.get(self.game.winner, self.game.winner.name)
            message = f"{winner_name} WINS!"
            color = Colors.WHITE
        elif self.game.game_state == GameState.BLACK_WINS:
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
        
        # Show disconnect message if applicable
        if self.is_disconnect_win and self.disconnect_reason:
            disconnect_msg = self.font_medium.render(self.disconnect_reason, True, Colors.YELLOW)
            disconnect_rect = disconnect_msg.get_rect(center=(self.WINDOW_WIDTH // 2, 250))
            self.screen.blit(disconnect_msg, disconnect_rect)
            
            # Additional note
            note = self.font_small.render("Opponent has left the game", True, Colors.LIGHT_GRAY)
            note_rect = note.get_rect(center=(self.WINDOW_WIDTH // 2, 290))
            self.screen.blit(note, note_rect)
        
        # Draw buttons ONLY if not a disconnect win (graceful termination)
        # When opponent disconnects, don't show rematch/new game buttons
        if not self.is_disconnect_win:
            for button in self.buttons["game_over"]:
                button.enabled = True
                button.draw(self.screen)
        else:
            # Only show "Main Menu" button for disconnect wins
            # Find and draw only the main menu button (usually the last button)
            if len(self.buttons["game_over"]) > 0:
                main_menu_button = self.buttons["game_over"][-1]  # Last button is usually Main Menu
                main_menu_button.enabled = True
                main_menu_button.draw(self.screen)
    
    def _draw_settings(self):
        """Draw settings menu with enhanced visibility"""
        # Title with shadow and better contrast
        title_text = "Settings"
        title_shadow = self.font_large.render(title_text, True, (0, 0, 0))
        title_shadow_rect = title_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 2, 102))
        self.screen.blit(title_shadow, title_shadow_rect)
        
        title = self.font_large.render(title_text, True, Colors.WHITE)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Instructions with shadow
        instruction_text = "Click buttons to toggle settings"
        instruction_shadow = self.font_small.render(instruction_text, True, (0, 0, 0))
        instruction_shadow_rect = instruction_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 1, 151))
        self.screen.blit(instruction_shadow, instruction_shadow_rect)
        
        instruction = self.font_small.render(instruction_text, True, Colors.WHITE)
        instruction_rect = instruction.get_rect(center=(self.WINDOW_WIDTH // 2, 150))
        self.screen.blit(instruction, instruction_rect)
        
        for button in self.buttons["settings"]:
            button.draw(self.screen)
    
    def _draw_about(self):
        """Draw about page with team members and game info"""
        # Title with shadow
        title_text = "About Gomoku"
        title_shadow = self.font_large.render(title_text, True, (0, 0, 0))
        title_shadow_rect = title_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 2, 52))
        self.screen.blit(title_shadow, title_shadow_rect)
        
        title = self.font_large.render(title_text, True, Colors.WHITE)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        y_offset = 100
        
        # Team Members Section
        team_title = self.font_medium.render("Team Members - Group 6", True, Colors.ACCENT)
        team_title_shadow = self.font_medium.render("Team Members - Group 6", True, (0, 0, 0))
        team_title_shadow_rect = team_title_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 1, y_offset + 1))
        self.screen.blit(team_title_shadow, team_title_shadow_rect)
        team_title_rect = team_title.get_rect(center=(self.WINDOW_WIDTH // 2, y_offset))
        self.screen.blit(team_title, team_title_rect)
        y_offset += 40
        
        # Team members list
        team_members = [
            ("Nguyen Ngoc Khoi", "2252378"),
            ("Nguyen Quang Phu", "2252621"),
            ("Nguyen Tan Bao Le", "2252428"),
            ("Nguyen Minh Khoi", "2252377")
        ]
        
        for name, student_id in team_members:
            member_text = f"{name} - {student_id}"
            member_shadow = self.font_small.render(member_text, True, (0, 0, 0))
            self.screen.blit(member_shadow, (self.WINDOW_WIDTH // 2 - 150 + 1, y_offset + 1))
            member_surf = self.font_small.render(member_text, True, Colors.WHITE)
            self.screen.blit(member_surf, (self.WINDOW_WIDTH // 2 - 150, y_offset))
            y_offset += 30
        
        y_offset += 20
        
        # Game Controls Section
        controls_title = self.font_medium.render("Game Controls", True, Colors.ACCENT)
        controls_title_shadow = self.font_medium.render("Game Controls", True, (0, 0, 0))
        controls_title_shadow_rect = controls_title_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 1, y_offset + 1))
        self.screen.blit(controls_title_shadow, controls_title_shadow_rect)
        controls_title_rect = controls_title.get_rect(center=(self.WINDOW_WIDTH // 2, y_offset))
        self.screen.blit(controls_title, controls_title_rect)
        y_offset += 40
        
        controls = [
            "Mouse Click: Place stone on board",
            "ESC: Pause game",
            "D: Toggle AI debug viewer (AI games)",
            "Pause Button: Pause and access menu",
            "Resign Button: Forfeit current game"
        ]
        
        for control in controls:
            control_shadow = self.font_small.render(control, True, (0, 0, 0))
            self.screen.blit(control_shadow, (self.WINDOW_WIDTH // 2 - 200 + 1, y_offset + 1))
            control_surf = self.font_small.render(control, True, Colors.WHITE)
            self.screen.blit(control_surf, (self.WINDOW_WIDTH // 2 - 200, y_offset))
            y_offset += 25
        
        # Buttons
        for button in self.buttons["about"]:
            button.draw(self.screen)
    
    def _handle_about_events(self, event):
        """Handle about page events"""
        buttons = self.buttons["about"]
        
        for i, button in enumerate(buttons):
            if button.handle_event(event):
                if i == 0:  # Back
                    self.ui_state = UIState.MAIN_MENU
    
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
        """Draw server selection screen with improved visibility"""
        # Title with shadow and better contrast
        title_text = "Select Server"
        title_shadow = self.font_large.render(title_text, True, (0, 0, 0))
        title_shadow_rect = title_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 2, 52))
        self.screen.blit(title_shadow, title_shadow_rect)
        
        title = self.font_large.render(title_text, True, Colors.WHITE)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Current server info with better visibility
        current_config = self.server_config_manager.get_current_config()
        if current_config:
            current_text = f"Current: {current_config.name}"
            current_shadow = self.font_info.render(current_text, True, (0, 0, 0))
            current_shadow_rect = current_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 1, 91))
            self.screen.blit(current_shadow, current_shadow_rect)
            
            current_surface = self.font_info.render(current_text, True, Colors.ACCENT)
            current_rect = current_surface.get_rect(center=(self.WINDOW_WIDTH // 2, 90))
            self.screen.blit(current_surface, current_rect)
        
        # Server list with improved visibility
        configs = self.server_config_manager.get_all_configs()
        start_y = 130
        
        for i, (name, config) in enumerate(configs.items()):
            y_pos = start_y + i * 70
            
            # Background panel for better readability
            panel_rect = pygame.Rect(80, y_pos - 5, 640, 65)
            panel = pygame.Surface((panel_rect.width, panel_rect.height))
            panel.set_alpha(180)
            panel.fill((20, 20, 30))
            self.screen.blit(panel, panel_rect)
            
            # Border for selected server
            if name == self.server_config_manager.current_config:
                pygame.draw.rect(self.screen, Colors.SUCCESS, panel_rect, 3)
            
            # Server name and type - larger font, bright white
            server_text = f"{name} ({config.server_type.value})"
            server_shadow = self.font_info.render(server_text, True, (0, 0, 0))
            self.screen.blit(server_shadow, (100 + 1, y_pos + 1))
            server_surface = self.font_info.render(server_text, True, Colors.WHITE)
            self.screen.blit(server_surface, (100, y_pos))
            
            # Server details - larger font, bright cyan/white
            details_text = f"{config.host}:{config.port}"
            if config.use_ssl:
                details_text += " (SSL)"
            details_shadow = self.font_small.render(details_text, True, (0, 0, 0))
            self.screen.blit(details_shadow, (100 + 1, y_pos + 28))
            details_surface = self.font_small.render(details_text, True, (200, 255, 255))  # Bright cyan
            self.screen.blit(details_surface, (100, y_pos + 27))
            
            # Current indicator - larger and more visible
            if name == self.server_config_manager.current_config:
                indicator_text = "CURRENT"
                indicator_shadow = self.font_info.render(indicator_text, True, (0, 0, 0))
                self.screen.blit(indicator_shadow, (550 + 1, y_pos + 15))
                indicator = self.font_info.render(indicator_text, True, Colors.SUCCESS)
                self.screen.blit(indicator, (550, y_pos + 14))
        
        # Instructions with better visibility
        instructions = [
            "Click on a server to select it",
            "Press Enter to continue with selected server",
            "ESC to go back"
        ]
        
        for i, instruction in enumerate(instructions):
            text_shadow = self.font_small.render(instruction, True, (0, 0, 0))
            text_shadow_rect = text_shadow.get_rect(center=(self.WINDOW_WIDTH // 2 + 1, 450 + i * 22 + 1))
            self.screen.blit(text_shadow, text_shadow_rect)
            
            text = self.font_small.render(instruction, True, Colors.WHITE)
            text_rect = text.get_rect(center=(self.WINDOW_WIDTH // 2, 450 + i * 22))
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
    
    def _draw_connection_lost(self):
        """Draw connection lost screen with reconnection progress"""
        # Dim the background
        overlay = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.font_large.render("Connection Lost", True, Colors.RED)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)
        
        # Reason
        if self.disconnect_reason:
            try:
                reason_lines = self._wrap_text(self.disconnect_reason, self.font_medium, self.WINDOW_WIDTH - 200)
                y_offset = 280
                for line in reason_lines:
                    reason_surface = self.font_medium.render(line, True, Colors.WHITE)
                    reason_rect = reason_surface.get_rect(center=(self.WINDOW_WIDTH // 2, y_offset))
                    self.screen.blit(reason_surface, reason_rect)
                    y_offset += 40
            except Exception as e:
                # Fallback if text wrapping fails
                reason_surface = self.font_medium.render("Connection to server lost", True, Colors.WHITE)
                reason_rect = reason_surface.get_rect(center=(self.WINDOW_WIDTH // 2, 280))
                self.screen.blit(reason_surface, reason_rect)
        
        # Reconnection progress
        if self.reconnection_attempt > 0:
            progress_text = f"Reconnecting... Attempt {self.reconnection_attempt}/{self.max_reconnection_attempts}"
            progress_surface = self.font_medium.render(progress_text, True, Colors.YELLOW)
            progress_rect = progress_surface.get_rect(center=(self.WINDOW_WIDTH // 2, 400))
            self.screen.blit(progress_surface, progress_rect)
            
            # Progress bar
            bar_width = 400
            bar_height = 20
            bar_x = (self.WINDOW_WIDTH - bar_width) // 2
            bar_y = 450
            
            # Background bar
            pygame.draw.rect(self.screen, Colors.DARK_GRAY, 
                           (bar_x, bar_y, bar_width, bar_height), border_radius=10)
            
            # Progress fill
            progress = self.reconnection_attempt / self.max_reconnection_attempts
            fill_width = int(bar_width * progress)
            pygame.draw.rect(self.screen, Colors.YELLOW,
                           (bar_x, bar_y, fill_width, bar_height), border_radius=10)
        
        # Instructions
        instruction = self.font_small.render("Please wait while we reconnect you...", True, Colors.LIGHT_GRAY)
        instruction_rect = instruction.get_rect(center=(self.WINDOW_WIDTH // 2, 520))
        self.screen.blit(instruction, instruction_rect)
    
    def _draw_opponent_disconnected(self):
        """Draw opponent disconnected screen with countdown"""
        # Draw the game board in the background (dimmed)
        try:
            self._draw_gameplay()
        except:
            # If gameplay drawing fails, just use black background
            self.screen.fill(Colors.BLACK)
        
        # Dim overlay
        overlay = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.font_large.render("Opponent Disconnected", True, Colors.WARNING)
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)
        
        # Message
        if self.disconnect_reason:
            try:
                message_lines = self._wrap_text(self.disconnect_reason, self.font_medium, self.WINDOW_WIDTH - 200)
                y_offset = 280
                for line in message_lines:
                    message_surface = self.font_medium.render(line, True, Colors.WHITE)
                    message_rect = message_surface.get_rect(center=(self.WINDOW_WIDTH // 2, y_offset))
                    self.screen.blit(message_surface, message_rect)
                    y_offset += 40
            except Exception as e:
                # Fallback message
                message_surface = self.font_medium.render("Your opponent has disconnected", True, Colors.WHITE)
                message_rect = message_surface.get_rect(center=(self.WINDOW_WIDTH // 2, 280))
                self.screen.blit(message_surface, message_rect)
        
        # Countdown timer
        if self.opponent_disconnect_time:
            elapsed = time.time() - self.opponent_disconnect_time
            remaining = max(0, self.opponent_disconnect_timeout - elapsed)
            
            countdown_text = f"Waiting for reconnection: {int(remaining)} seconds"
            countdown_surface = self.font_medium.render(countdown_text, True, Colors.YELLOW)
            countdown_rect = countdown_surface.get_rect(center=(self.WINDOW_WIDTH // 2, 400))
            self.screen.blit(countdown_surface, countdown_rect)
            
            # Progress bar showing time remaining
            bar_width = 400
            bar_height = 20
            bar_x = (self.WINDOW_WIDTH - bar_width) // 2
            bar_y = 450
            
            # Background bar
            pygame.draw.rect(self.screen, Colors.DARK_GRAY,
                           (bar_x, bar_y, bar_width, bar_height), border_radius=10)
            
            # Time remaining fill
            progress = remaining / self.opponent_disconnect_timeout
            fill_width = int(bar_width * progress)
            color = Colors.GREEN if progress > 0.5 else (Colors.WARNING if progress > 0.25 else Colors.RED)
            pygame.draw.rect(self.screen, color,
                           (bar_x, bar_y, fill_width, bar_height), border_radius=10)
        
        # Leave game button
        button_width = 200
        button_height = 50
        button_x = (self.WINDOW_WIDTH - button_width) // 2
        button_y = 520
        
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = button_rect.collidepoint(mouse_pos)
        
        button_color = Colors.RED if is_hover else Colors.DARK_GRAY
        pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10)
        
        leave_text = self.font_medium.render("Leave Game", True, Colors.WHITE)
        leave_rect = leave_text.get_rect(center=button_rect.center)
        self.screen.blit(leave_text, leave_rect)
    
    def _draw_board(self):
        """Draw the game board with modern effects"""
        # Draw board background with shadow
        board_rect = pygame.Rect(self.BOARD_OFFSET_X, self.BOARD_OFFSET_Y, 
                                self.BOARD_SIZE, self.BOARD_SIZE)
        
        # Shadow effect
        shadow_rect = pygame.Rect(self.BOARD_OFFSET_X + 4, self.BOARD_OFFSET_Y + 4,
                                 self.BOARD_SIZE, self.BOARD_SIZE)
        shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height))
        shadow_surface.set_alpha(40)
        shadow_surface.fill(Colors.BLACK)
        self.screen.blit(shadow_surface, shadow_rect)
        
        # Board background with subtle gradient
        pygame.draw.rect(self.screen, Colors.LIGHT_BROWN, board_rect)
        
        # Add subtle border
        pygame.draw.rect(self.screen, Colors.DARK_BROWN, board_rect, 3)
        
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
        """Draw a stone on the board with color based on player"""
        center_x = self.BOARD_OFFSET_X + col * self.CELL_SIZE + self.CELL_SIZE // 2
        center_y = self.BOARD_OFFSET_Y + row * self.CELL_SIZE + self.CELL_SIZE // 2
        radius = self.CELL_SIZE // 2 - 3
        
        # Get player color from mapping
        player_colors = {
            Player.BLACK: (0, 0, 0),           # Black
            Player.WHITE: (255, 255, 255),    # White
            Player.RED: (220, 38, 38),        # Red
            Player.BLUE: (37, 99, 235),       # Blue
            Player.GREEN: (34, 197, 94)       # Green
        }
        
        color = player_colors.get(player, Colors.BLACK)
        
        # Border color: white for dark colors, black for light colors
        if player == Player.WHITE:
            border_color = Colors.BLACK
        else:
            border_color = Colors.WHITE
        
        pygame.draw.circle(self.screen, color, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, border_color, (center_x, center_y), radius, 2)
    
    def _highlight_last_move(self, row: int, col: int):
        """Highlight the last move"""
        center_x = self.BOARD_OFFSET_X + col * self.CELL_SIZE + self.CELL_SIZE // 2
        center_y = self.BOARD_OFFSET_Y + row * self.CELL_SIZE + self.CELL_SIZE // 2
        radius = self.CELL_SIZE // 2 - 1
        
        pygame.draw.circle(self.screen, Colors.RED, (center_x, center_y), radius, 3)
    
    def _draw_game_info(self):
        """Draw game information panel with enhanced visibility and proper text wrapping"""
        info_x = 520  # Adjusted for new board position
        info_y = 120  # Moved up to align with new board position
        panel_width = 240  # Slightly reduced width to ensure fit
        panel_padding = 15
        text_margin = 5
        max_text_width = panel_width - (2 * panel_padding) - 20  # Account for padding and scrollbar
        
        # Create semi-transparent background panel for better readability
        # Adjust height based on number of players and debug panel
        num_players = len(self.game.players) if hasattr(self.game, 'players') else 2
        base_height = 80  # Base height for title and separator
        player_section_height = num_players * 30  # Increased line height for better readability
        moves_section_height = 50  # Moves and mode info
        panel_height = base_height + player_section_height + moves_section_height
        
        # Add extra space if no debug panel in AI games
        if self.game_mode == GameMode.AI_GAME and not self.ai_debug_enabled:
            panel_height += 20
        elif self.game_mode == GameMode.AI_GAME and self.ai_debug_enabled:
            panel_height -= 20  # Less space if debug panel is shown
        if self.is_network_game:
            panel_height += 10
        
        # Ensure minimum height
        panel_height = max(panel_height, 200)
        
        # Create panel surface with rounded corners
        info_panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        
        # Draw rounded rectangle for panel
        pygame.draw.rect(info_panel, (20, 20, 30, 230), (0, 0, panel_width, panel_height), border_radius=8)
        pygame.draw.rect(info_panel, Colors.ACCENT, (0, 0, panel_width, panel_height), 3, border_radius=8)
        
        self.screen.blit(info_panel, (info_x - panel_padding, info_y - panel_padding))
        
        # Helper function to render wrapped text
        def render_text_with_wrap(text, font, color, x, y, max_width):
            words = text.split(' ')
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_width = font.size(test_line)[0]
                
                if test_width <= max_width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for i, line in enumerate(lines):
                text_surface = font.render(line, True, color)
                text_shadow = font.render(line, True, (0, 0, 0))
                self.screen.blit(text_shadow, (x + 1, y + (i * (font.get_height() + 2)) + 1))
                self.screen.blit(text_surface, (x, y + (i * (font.get_height() + 2))))
            
            return len(lines) * (font.get_height() + 2)
        
        # Current player with name (highlighted)
        current_player_name = self.player_names.get(self.game.current_player, "Unknown")
        current_text = f"Current Player: {current_player_name}"
        
        # Render current player text with wrapping
        y_offset = render_text_with_wrap(
            current_text, 
            self.font_info, 
            Colors.WHITE, 
            info_x, 
            info_y, 
            max_text_width
        )
        
        # Add separator line after current player
        separator_y = info_y + y_offset + 5
        pygame.draw.line(self.screen, Colors.ACCENT, 
                        (info_x - 10, separator_y),
                        (info_x + panel_width - 25, separator_y), 2)
        
        # Show all players in the game (supports 2-5 players)
        player_y = separator_y + 10
        line_height = 30  # Increased line height
        
        # Get all players in the game
        if hasattr(self.game, 'players') and self.game.players:
            all_players = self.game.players
        else:
            # Fallback for 2-player games
            all_players = [Player.BLACK, Player.WHITE]
        
        # Player symbols/colors mapping
        player_symbols = {
            Player.BLACK: "●",
            Player.WHITE: "○",
            Player.RED: "◆",
            Player.BLUE: "■",
            Player.GREEN: "▲"
        }
        
        # Show all players with current player highlighting
        for i, player in enumerate(all_players):
            player_name = self.player_names.get(player, f"Player {i+1}")
            symbol = player_symbols.get(player, "●")
            
            # Highlight current player with green color
            if self.game.current_player == player:
                player_color = Colors.SUCCESS  # Green for current player
                player_text = f"{symbol} {player_name} ←"
            else:
                player_color = Colors.WHITE
                player_text = f"{symbol} {player_name}"
            
            # Add "(YOU)" indicator ONLY for network games (not AI games)
            if self.is_network_game and hasattr(self, 'network_game_info'):
                your_role = self.network_game_info.get('your_role', 'black')
                if (your_role == 'black' and player == Player.BLACK) or \
                   (your_role == 'white' and player == Player.WHITE):
                    player_text += " (YOU)"
            
            # Draw player info with wrapping
            lines_used = render_text_with_wrap(
                player_text,
                self.font_small,  # Slightly smaller font for player info
                player_color,
                info_x,
                player_y,
                max_text_width
            )
            
            player_y += max(line_height, lines_used)  # Ensure minimum line height
        
        # Move count - positioned after all players
        move_y = player_y + 10  # Add spacing after players
        move_text = f"Moves: {len(self.game.move_history)}"
        move_shadow = self.font_info.render(move_text, True, (0, 0, 0))
        self.screen.blit(move_shadow, (info_x + 1, move_y + 1))
        move_surface = self.font_info.render(move_text, True, Colors.WHITE)
        self.screen.blit(move_surface, (info_x, move_y))
        
        # Game mode - positioned after move count
        mode_y = move_y + 28
        mode_text = f"Mode: {self.game_mode.value.replace('_', ' ').title()}"
        mode_shadow = self.font_info.render(mode_text, True, (0, 0, 0))
        self.screen.blit(mode_shadow, (info_x + 1, mode_y + 1))
        mode_surface = self.font_info.render(mode_text, True, Colors.WHITE)
        self.screen.blit(mode_surface, (info_x, mode_y))
        
        # AI info - only show if debug panel is not enabled
        if self.game_mode == GameMode.AI_GAME and self.ai_player and not self.ai_debug_enabled:
            ai_y = info_y + 160
            ai_text = f"AI Difficulty: {self.ai_difficulty.title()}"
            ai_shadow = self.font_info.render(ai_text, True, (0, 0, 0))
            self.screen.blit(ai_shadow, (info_x + 1, ai_y + 1))
            ai_surface = self.font_info.render(ai_text, True, Colors.WHITE)
            self.screen.blit(ai_surface, (info_x, ai_y))
            
            # Show thinking animation
            if self.ai_thinking:
                thinking_time = time.time() - self.thinking_start_time
                dots = "." * (int(thinking_time * 2) % 4)
                thinking_text = f"AI Thinking{dots}"
                
                # Add a subtle pulsing effect
                pulse = abs(math.sin(thinking_time * 3)) * 0.3 + 0.7
                thinking_color = (int(100 * pulse), int(200 * pulse), int(255 * pulse))
                thinking_shadow = self.font_info.render(thinking_text, True, (0, 0, 0))
                self.screen.blit(thinking_shadow, (info_x + 1, ai_y + 30))
                thinking_surface = self.font_info.render(thinking_text, True, thinking_color)
                self.screen.blit(thinking_surface, (info_x, ai_y + 29))
            else:
                stats = self.ai_player.get_statistics()
                if stats["nodes_evaluated"] > 0:
                    stats_text = f"AI Nodes: {stats['nodes_evaluated']}"
                    stats_shadow = self.font_info.render(stats_text, True, (0, 0, 0))
                    self.screen.blit(stats_shadow, (info_x + 1, ai_y + 30))
                    stats_surface = self.font_info.render(stats_text, True, Colors.WHITE)
                    self.screen.blit(stats_surface, (info_x, ai_y + 29))
        
        # Network info
        if self.is_network_game:
            if self.waiting_for_network:
                network_text = "Waiting for opponent..."
                color = Colors.ERROR
            else:
                network_text = "Network Game Active"
                color = Colors.SUCCESS
            
            network_shadow = self.font_info.render(network_text, True, (0, 0, 0))
            self.screen.blit(network_shadow, (info_x + 1, info_y + 215))
            network_surface = self.font_info.render(network_text, True, color)
            self.screen.blit(network_surface, (info_x, info_y + 214))
    
    def _draw_ai_debug_panel(self):
        """Draw AI debug information panel with real-time thinking display"""
        panel_x = 520
        panel_y = 340  # Moved up slightly to avoid overlap
        panel_width = 260
        panel_height = 300  # Increased height for real-time moves
        
        # Background panel with padding
        panel_padding = 15
        debug_panel = pygame.Surface((panel_width, panel_height))
        debug_panel.set_alpha(240)
        debug_panel.fill((10, 10, 20))  # Very dark background
        self.screen.blit(debug_panel, (panel_x - panel_padding, panel_y - panel_padding))
        
        # Border
        border_rect = pygame.Rect(panel_x - panel_padding, panel_y - panel_padding, 
                                 panel_width, panel_height)
        pygame.draw.rect(self.screen, Colors.ACCENT, border_rect, 3)
        
        # Title with larger font
        title_text = "AI Debug Info (Press D)"
        title_shadow = self.font_info.render(title_text, True, (0, 0, 0))
        self.screen.blit(title_shadow, (panel_x + 1, panel_y + 1))
        title = self.font_info.render(title_text, True, Colors.ACCENT)
        self.screen.blit(title, (panel_x, panel_y))
        
        y_offset = panel_y + 30  # More spacing
        line_height = 20  # Line height for better readability
        
        # Use larger font for better readability
        debug_font = self.font_small  # Use smaller font to fit more info
        
        # Get real-time stats if AI is thinking
        real_time_stats = None
        if self.ai_thinking and self.ai_player:
            real_time_stats = self.ai_player.get_real_time_stats()
        
        # Show real-time thinking info if available
        if real_time_stats and real_time_stats.get("is_thinking"):
            # Current depth
            depth_text = f"Depth: {real_time_stats.get('current_depth', 0)}"
            depth_shadow = debug_font.render(depth_text, True, (0, 0, 0))
            self.screen.blit(depth_shadow, (panel_x + 1, y_offset + 1))
            depth_surf = debug_font.render(depth_text, True, Colors.WHITE)
            self.screen.blit(depth_surf, (panel_x, y_offset))
            y_offset += line_height
            
            # Nodes evaluated so far
            nodes_text = f"Nodes: {real_time_stats.get('nodes_evaluated', 0)}"
            nodes_shadow = debug_font.render(nodes_text, True, (0, 0, 0))
            self.screen.blit(nodes_shadow, (panel_x + 1, y_offset + 1))
            nodes_surf = debug_font.render(nodes_text, True, Colors.WHITE)
            self.screen.blit(nodes_surf, (panel_x, y_offset))
            y_offset += line_height
            
            # Best move so far
            best_move = real_time_stats.get("best_move_so_far")
            best_score = real_time_stats.get("best_score_so_far", float('-inf'))
            if best_move is not None:
                best_text = f"Best: ({best_move[0]},{best_move[1]})={best_score:.0f}"
                best_shadow = debug_font.render(best_text, True, (0, 0, 0))
                self.screen.blit(best_shadow, (panel_x + 1, y_offset + 1))
                best_surf = debug_font.render(best_text, True, Colors.SUCCESS)
                self.screen.blit(best_surf, (panel_x, y_offset))
                y_offset += line_height + 5
            
            # Current moves being evaluated
            current_moves = real_time_stats.get("current_moves", [])
            if current_moves:
                evaluating_text = "Evaluating Moves:"
                eval_shadow = debug_font.render(evaluating_text, True, (0, 0, 0))
                self.screen.blit(eval_shadow, (panel_x + 1, y_offset + 1))
                eval_surf = debug_font.render(evaluating_text, True, Colors.ACCENT)
                self.screen.blit(eval_surf, (panel_x, y_offset))
                y_offset += line_height
                
                # Show top moves being evaluated (up to 5)
                for i, move_info in enumerate(current_moves[:5]):
                    move = move_info.get("move")
                    status = move_info.get("status", "completed")
                    score = move_info.get("score")
                    
                    if status == "evaluating":
                        move_text = f"  → ({move[0]},{move[1]}) ..."
                        move_color = Colors.WARNING
                    else:
                        if score is not None:
                            move_text = f"  {i+1}. ({move[0]},{move[1]})={score:.0f}"
                            move_color = Colors.SUCCESS if i == 0 else Colors.WHITE
                        else:
                            move_text = f"  {i+1}. ({move[0]},{move[1]})"
                            move_color = Colors.WHITE
                    
                    move_shadow = debug_font.render(move_text, True, (0, 0, 0))
                    self.screen.blit(move_shadow, (panel_x + 1, y_offset + 1))
                    move_surf = debug_font.render(move_text, True, move_color)
                    self.screen.blit(move_surf, (panel_x, y_offset))
                    y_offset += line_height - 2
        
        # Show final stats if available (after thinking is done)
        elif self.ai_debug_stats:
            # Nodes evaluated
            nodes_text = f"Nodes: {self.ai_debug_stats['nodes_evaluated']}"
            nodes_shadow = debug_font.render(nodes_text, True, (0, 0, 0))
            self.screen.blit(nodes_shadow, (panel_x + 1, y_offset + 1))
            nodes_surf = debug_font.render(nodes_text, True, Colors.WHITE)
            self.screen.blit(nodes_surf, (panel_x, y_offset))
            y_offset += line_height
            
            # Pruning count
            pruning_text = f"Prunings: {self.ai_debug_stats['pruning_count']}"
            pruning_shadow = debug_font.render(pruning_text, True, (0, 0, 0))
            self.screen.blit(pruning_shadow, (panel_x + 1, y_offset + 1))
            pruning_surf = debug_font.render(pruning_text, True, Colors.SUCCESS)
            self.screen.blit(pruning_surf, (panel_x, y_offset))
            y_offset += line_height
            
            # Pruning efficiency
            efficiency = self.ai_debug_stats.get('pruning_efficiency', 0)
            eff_text = f"Efficiency: {efficiency:.1f}%"
            eff_shadow = debug_font.render(eff_text, True, (0, 0, 0))
            self.screen.blit(eff_shadow, (panel_x + 1, y_offset + 1))
            eff_color = Colors.SUCCESS if efficiency > 20 else Colors.WARNING
            eff_surf = debug_font.render(eff_text, True, eff_color)
            self.screen.blit(eff_surf, (panel_x, y_offset))
            y_offset += line_height
            
            # Max depth
            depth_text = f"Max Depth: {self.ai_debug_stats.get('max_depth_reached', 0)}"
            depth_shadow = debug_font.render(depth_text, True, (0, 0, 0))
            self.screen.blit(depth_shadow, (panel_x + 1, y_offset + 1))
            depth_surf = debug_font.render(depth_text, True, Colors.WHITE)
            self.screen.blit(depth_surf, (panel_x, y_offset))
            y_offset += line_height
            
            # Search time
            time_text = f"Time: {self.ai_debug_stats.get('search_time', 0):.3f}s"
            time_shadow = debug_font.render(time_text, True, (0, 0, 0))
            self.screen.blit(time_shadow, (panel_x + 1, y_offset + 1))
            time_surf = debug_font.render(time_text, True, Colors.WHITE)
            self.screen.blit(time_surf, (panel_x, y_offset))
            y_offset += line_height
            
            # Nodes per second
            nps = self.ai_debug_stats.get('nodes_per_second', 0)
            nps_text = f"Nodes/s: {nps:.0f}"
            nps_shadow = debug_font.render(nps_text, True, (0, 0, 0))
            self.screen.blit(nps_shadow, (panel_x + 1, y_offset + 1))
            nps_surf = debug_font.render(nps_text, True, Colors.WHITE)
            self.screen.blit(nps_surf, (panel_x, y_offset))
            y_offset += line_height + 5
            
            # Top move evaluations with scores
            move_evals = self.ai_debug_stats.get('move_evaluations', [])
            if move_evals:
                sorted_moves = sorted(move_evals, key=lambda x: x['score'], reverse=True)
                top_moves_text = "Final Top Moves:"
                top_shadow = debug_font.render(top_moves_text, True, (0, 0, 0))
                self.screen.blit(top_shadow, (panel_x + 1, y_offset + 1))
                top_surf = debug_font.render(top_moves_text, True, Colors.ACCENT)
                self.screen.blit(top_surf, (panel_x, y_offset))
                y_offset += line_height
                
                # Show top 5 moves with scores
                for i, eval_info in enumerate(sorted_moves[:5]):
                    move = eval_info['move']
                    score = eval_info['score']
                    move_text = f"{i+1}. ({move[0]},{move[1]}) Score: {score:.0f}"
                    move_shadow = debug_font.render(move_text, True, (0, 0, 0))
                    self.screen.blit(move_shadow, (panel_x + 1, y_offset + 1))
                    move_color = Colors.SUCCESS if i == 0 else Colors.WHITE
                    move_surf = debug_font.render(move_text, True, move_color)
                    self.screen.blit(move_surf, (panel_x, y_offset))
                    y_offset += line_height - 2
    
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
            print(f"🚫 Cannot make move: current_player={self.game.current_player.name}, my_player={self.my_player.name if self.my_player else 'None'}")
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
            
            # Play turn sound
            self._play_sound("play_turn")
            
            # Check if game ended (winner)
            if self.game.game_state != GameState.PLAYING:
                if self.game.game_state in [GameState.BLACK_WINS, GameState.WHITE_WINS]:
                    self._play_sound("winner")
            
            # Send move over network if needed
            if self.is_network_game and self.network_manager:
                player_id = self.game.move_history[-1].player.value
                success = self.network_manager.send_game_move(row, col, player_id)
                if not success:
                    print("Failed to send move over network")
    
    def _handle_network_move(self, row: int, col: int, timer_state: Dict[str, Any] = None):
        """Handle a move received from the network"""
        try:
            if self.game.is_valid_move(row, col):
                if self.game.make_move(row, col):
                    self.last_move_pos = (row, col)
                    
                    # Sync timer with server's timer state (if provided)
                    if timer_state:
                        server_turn_start = timer_state.get("turn_start_time")
                        self.move_time_limit = timer_state.get("move_time_limit", 30)
                        if server_turn_start:
                            # Calculate time since server set the timer
                            time_since_server_reset = time.time() - server_turn_start
                            self.turn_start_time = time.time()
                            self.elapsed_before_pause = time_since_server_reset
                        else:
                            self.turn_start_time = time.time()
                            self.elapsed_before_pause = 0
                    else:
                        # Fallback: reset timer locally (old behavior)
                        self.turn_start_time = time.time()
                        self.elapsed_before_pause = 0
                    
                    # Play turn sound
                    self._play_sound("play_turn")
                    
                    # Check if game ended (winner)
                    if self.game.game_state != GameState.PLAYING:
                        if self.game.game_state in [GameState.BLACK_WINS, GameState.WHITE_WINS]:
                            self._play_sound("winner")
                    
                    print(f"Network move applied: ({row}, {col})")
                else:
                    print(f"Failed to apply network move: ({row}, {col})")
            else:
                print(f"Invalid network move received: ({row}, {col})")
        except Exception as e:
            print(f"Error handling network move: {e}")
    
    def _start_new_game(self):
        """Start a new game"""
        # Reset all timers and pause info
        self.turn_start_time = None
        self.elapsed_before_pause = 0
        self.paused = False
        self.pause_sent = False
        self.pause_start_time = None
        # Reset pause allowances for both players
        self.pause_allowance = {Player.BLACK: 2, Player.WHITE: 2}
        # Clean up any running AI threads
        self.ai_thinking = False
        self.ai_move_result = None
        if self.ai_thread and self.ai_thread.is_alive():
            # Thread will finish naturally since it's daemon
            pass
        
        # Initialize game with correct number of players
        if self.game_mode == GameMode.AI_GAME:
            self.game = GomokuGame(num_players=self.num_ai_players)
        else:
            self.game.reset_game()
        self.last_move_pos = None
        
        # Set player names and AI players based on game mode
        if self.game_mode == GameMode.AI_GAME:
            # Create AI players for all non-human players
            self.ai_players = {}
            self.player_names = {
                Player.BLACK: "You"
            }
            
            # Create AI for each non-human player
            for i, player in enumerate(self.game.players[1:], 1):  # Skip BLACK (human)
                self.ai_players[player] = AIPlayer(player, self.ai_difficulty)
                player_color = player.name.title()
                self.player_names[player] = f"AI {i} ({self.ai_difficulty.title()})"
            
            # For backward compatibility, keep ai_player for single AI games
            if self.num_ai_players == 2:
                self.ai_player = self.ai_players.get(Player.WHITE)
            else:
                self.ai_player = None  # Use ai_players dict instead
            
            # Initialize pause allowances for all players
            self.pause_allowance = {player: 2 for player in self.game.players}
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
        
        # Play board start sound and start background music (looping)
        self._play_sound("board_start")
        self._play_background_music()  # This will loop indefinitely
    
    
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
            
            # Play board start sound and start background music when resuming
            self._play_sound("board_start")
            self._play_background_music()
            
            print("Game loaded successfully!")
            
        except Exception as e:
            print(f"Error loading game: {e}")
    
    def _resign_game(self):
        """Resign the current game (local + network safe)"""
        if self.is_network_game and self.network_manager:
            print(f"🏳️ {self.player_name} is resigning...")
            self.network_manager.send_message("player_resign", {
                "player": self.player_names[self.my_player]
            })
            return  # wait for ack

        # Local fallback
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
                """Handle disconnection from server"""
                print("Disconnected from lobby")
                
                # Handle different states appropriately
                if self.ui_state in [UIState.LOBBY_BROWSER, UIState.ROOM_CREATE, UIState.ROOM_WAITING]:
                    self.ui_state = UIState.MAIN_MENU
                elif self.ui_state in [UIState.GAMEPLAY, UIState.PAUSE_MENU]:
                    # If in gameplay, this means the connection was lost
                    # The opponent disconnect handler should have been triggered
                    # If not, show a generic disconnect message
                    if self.ui_state != UIState.OPPONENT_DISCONNECTED and self.ui_state != UIState.CONNECTION_LOST:
                        self.disconnect_reason = "Connection to server lost"
                        self.ui_state = UIState.MAIN_MENU
            
            def handle_room_list(data):
                self.current_room_list = data.get("rooms", [])
                print(f"Received room list: {len(self.current_room_list)} rooms")
            
            def handle_room_info(data):
                if data.get("success"):
                    self.room_info = data.get("room_info")
                    if self.room_info:
                        self.room_id = self.room_info.get("room_id")
                        message = data.get("message", "")
                        print(f"Joined/Created room: {self.room_info}")
                        print(f"Room info message: {message}")
                        
                        # Check if we became host (e.g., after opponent left)
                        if "You are now the host!" in message or "You are the host" in message:
                            print(f"👑 You became/are the host of the room!")
                            # If we're in gameplay or game over, this means opponent left
                            # We should go back to waiting room
                            if self.ui_state in [UIState.GAMEPLAY, UIState.GAME_OVER, UIState.PAUSE_MENU]:
                                self.game.reset_game()
                                self.ui_state = UIState.ROOM_WAITING
                                self._stop_background_music()
                                print(f"📋 Opponent left during game - returned to waiting room as host")

                        # Store reconnect info
                        self.reconnect_info = {
                            "player_name": self.player_name,
                            "room_id": self.room_id
                        }
                        print(f"Reconnection info stored: {self.reconnect_info}")

                        # Only set to ROOM_WAITING if we're not already in a game state
                        if self.ui_state not in [UIState.GAMEPLAY, UIState.PAUSE_MENU, UIState.GAME_OVER]:
                            self.ui_state = UIState.ROOM_WAITING
                    
            def handle_player_pause(data):
                sender = data.get("player", "Unknown")
                remaining_turn = data.get("remaining_turn", None)
                pauses_remaining = data.get("pauses_remaining", None)
                pause_timestamp = data.get("pause_timestamp", None)
                print(f"🔶 Received pause signal from {sender}")

                # Freeze game on both sides
                self.paused = True
                self.ui_state = UIState.PAUSE_MENU
                
                # Synchronize pause start time with the initiator's timestamp
                if pause_timestamp is not None:
                    self.pause_start_time = pause_timestamp
                    print(f"Synchronized pause start time with initiator")
                else:
                    self.pause_start_time = time.time()  # Fallback to local time
                
                # Record who paused — determine opponent
                if self.my_player == Player.BLACK:
                    self.pause_initiator = Player.WHITE
                else:
                    self.pause_initiator = Player.BLACK

                # Synchronize pause count from the pauser
                if pauses_remaining is not None:
                    self.pause_allowance[self.pause_initiator] = pauses_remaining
                    print(f"Synchronized pause count for {self.pause_initiator.name}: {pauses_remaining} remaining")

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
                    timer_state = data.get('timer_state')
                    self._handle_network_move(data['row'], data['col'], timer_state)
            
            def handle_timer_sync(data):
                """Handle timer synchronization from server"""
                timer_state = data.get('timer_state')
                if timer_state:
                    server_turn_start = timer_state.get("turn_start_time")
                    self.move_time_limit = timer_state.get("move_time_limit", 30)
                    if server_turn_start:
                        time_since_server_reset = time.time() - server_turn_start
                        self.turn_start_time = time.time()
                        self.elapsed_before_pause = time_since_server_reset
                    else:
                        self.turn_start_time = time.time()
                        self.elapsed_before_pause = 0
            
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
            
            def handle_player_resign(data):
                """Triggered when opponent resigns"""
                resigned_player = data.get("player", "Unknown")
                print(f"🏳️ Opponent {resigned_player} resigned.")

                # End the game correctly
                if self.my_player == Player.BLACK:
                    winner = Player.BLACK if self.game.current_player == Player.BLACK else Player.WHITE
                else:
                    winner = Player.WHITE if self.game.current_player == Player.WHITE else Player.BLACK

                # Opponent resigned → you are the winner
                self.game.winner = self.my_player
                self.game.game_state = (
                    GameState.BLACK_WINS if self.my_player == Player.BLACK else GameState.WHITE_WINS
                )
                self.ui_state = UIState.GAME_OVER
                print(f"🎉 You win! Opponent {resigned_player} has resigned.")

            def handle_resign_ack(data):
                """Triggered when server confirms your resignation"""
                msg = data.get("message", "You have resigned.")
                print(f"✅ Server acknowledged resignation: {msg}")

                # You lose
                self.ui_state = UIState.GAME_OVER
                self.game.game_state = (
                    GameState.WHITE_WINS if self.my_player == Player.BLACK else GameState.BLACK_WINS
                )
                self.game.winner = (
                    Player.WHITE if self.my_player == Player.BLACK else Player.BLACK
                )
                
            def handle_reconnect_success(data):
                print("🔁 Reconnected successfully!")
                self.room_id = data.get("room_id")

                board = data.get("board", [])
                moves = data.get("moves", [])
                current_player = data.get("current_player", 1)
                players = data.get("players", {})
                game_state_str = data.get("game_state", "playing")
                your_role = data.get("your_role", "black")
                your_name = data.get("your_name", "You")
                timer_state = data.get("timer_state", {})

                try:
                    # --- � Clear old game state completely ---
                    self.game.board = [[Player.EMPTY for _ in range(15)] for _ in range(15)]
                    self.game.move_history.clear()
                    
                    # --- �🧠 Rebuild game board from server state ---
                    if board and isinstance(board[0], list):
                        for r in range(len(board)):
                            for c in range(len(board[r])):
                                cell = board[r][c]
                                self.game.board[r][c] = Player(cell) if cell in [0, 1, 2] else Player.EMPTY

                    # --- 🧩 Rebuild move history ---
                    from gomoku_game import Move
                    for mv in moves:
                        if isinstance(mv, dict):
                            row, col = mv.get("row"), mv.get("col")
                            player_name = mv.get("player")
                            # Determine player ID by name lookup
                            if players and player_name == players.get("black"):
                                player = Player.BLACK
                            else:
                                player = Player.WHITE
                            self.game.move_history.append(Move(row, col, player))
                        elif isinstance(mv, (list, tuple)) and len(mv) >= 3:
                            self.game.move_history.append(Move(mv[0], mv[1], Player(mv[2])))

                    # --- 🎯 Restore last move marker ---
                    if self.game.move_history:
                        last_move = self.game.move_history[-1]
                        self.last_move_pos = (last_move.row, last_move.col)

                    # --- 🎮 Restore game state ---
                    self.game.current_player = Player(current_player)
                    print(f"🔧 CLIENT: Restored current_player={self.game.current_player.name} (value={current_player})")
                    self.game.game_state = GameState(game_state_str) if isinstance(game_state_str, str) else game_state_str
                    
                    # CRITICAL: Sync timer with server's timer state
                    if timer_state:
                        server_turn_start = timer_state.get("turn_start_time")
                        self.move_time_limit = timer_state.get("move_time_limit", 30)
                        self.elapsed_before_pause = timer_state.get("elapsed_before_pause", 0)
                        
                        if server_turn_start:
                            # Calculate time since server set the timer
                            time_since_server_reset = time.time() - server_turn_start
                            self.turn_start_time = time.time()  # Start our timer now
                            self.elapsed_before_pause = time_since_server_reset  # Account for network delay
                            print(f"🔧 DEBUG: Synced timer from server - started {time_since_server_reset:.2f}s ago, effective remaining: {self.move_time_limit - time_since_server_reset:.1f}s")
                        else:
                            self.turn_start_time = time.time()
                            print(f"🔧 DEBUG: Server sent no turn_start_time, starting fresh")
                    else:
                        # Fallback: fresh timer
                        self.elapsed_before_pause = 0
                        self.turn_start_time = time.time()
                        self.move_time_limit = 30
                        print(f"🔧 DEBUG: No timer_state from server, using fresh 30s timer")
                    
                    # Restore player role
                    self.my_player = Player.BLACK if your_role == "black" else Player.WHITE
                    print(f"🔧 DEBUG: my_player set to {self.my_player.name} (role: {your_role})")
                    
                    # Restore player name (for UI display)
                    self.player_name = your_name
                    
                    # Restore player names from server data
                    if players:
                        self.player_names = {
                            Player.BLACK: players.get("black", "Player 1"),
                            Player.WHITE: players.get("white", "Player 2")
                        }
                        print(f"🔧 DEBUG: Restored player names: {self.player_names}")
                        print(f"🔧 DEBUG: You are {self.player_name} ({your_role})")
                    
                    # **CRITICAL**: Mark as network game to enable turn validation
                    self.is_network_game = True
                    
                    # Restore winner if game is over
                    if self.game.game_state in [GameState.BLACK_WINS, GameState.WHITE_WINS]:
                        self.game.winner = self.game.current_player
                    
                    # --- 🎮 Restore UI state ---
                    if self.game.game_state == GameState.PLAYING:
                        self.ui_state = UIState.GAMEPLAY
                        self.paused = False
                        # Timer already reset above - don't need to check again
                        # Restart background music if it was playing
                        if not pygame.mixer.music.get_busy():
                            self._play_background_music()
                        print(f"🔧 DEBUG: UI state set to GAMEPLAY, game unpaused, timer running")
                    else:
                        # Game is over, show game over screen
                        self.ui_state = UIState.GAME_OVER
                        self.paused = False
                        self.turn_start_time = None
                        self.elapsed_before_pause = 0

                    # --- 🖼️ Force board redraw ---
                    self._draw_board()
                    pygame.display.flip()

                    print(f"✅ Restored {len(moves)} moves and board ({sum(cell != 0 for row in board for cell in row)} stones), turn: {self.game.current_player.name}, state: {self.game.game_state.value}")

                except Exception as e:
                    print(f"⚠️ Error restoring reconnect state: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback: reset to waiting room
                    self.ui_state = UIState.ROOM_WAITING

            self.network_manager.set_connection_callback("connect", handle_connect)
            self.network_manager.set_connection_callback("disconnect", handle_disconnect)
            self.network_manager.set_message_handler("room_list", handle_room_list)
            self.network_manager.set_message_handler("room_info", handle_room_info)
            self.network_manager.set_message_handler("game_started", handle_game_start)
            self.network_manager.set_message_handler("game_move", handle_game_move)
            self.network_manager.set_message_handler("timer_sync", handle_timer_sync)
            self.network_manager.set_message_handler("new_game_request", handle_new_game_request)
            self.network_manager.set_message_handler("new_game_response", handle_new_game_response)
            self.network_manager.set_message_handler("player_pause", handle_player_pause)
            self.network_manager.set_message_handler("player_resume", handle_player_resume)
            self.network_manager.set_message_handler("player_resign", handle_player_resign)
            self.network_manager.set_message_handler("resign_ack", handle_resign_ack)
            self.network_manager.set_message_handler("reconnect_success", handle_reconnect_success)
            
            def handle_reconnect_failed(data):
                """Handle failed reconnection"""
                reason = data.get("reason", "unknown")
                message = data.get("message", "Failed to reconnect to your game")
                print(f"❌ Reconnection failed: {message}")
                
                self.disconnect_reason = message
                self.ui_state = UIState.MAIN_MENU
                
            def handle_player_disconnected(data):
                """Handle opponent disconnection"""
                player_name = data.get("player_name", "Opponent")
                disconnect_time = data.get("disconnect_time", time.time())
                timeout_seconds = data.get("timeout_seconds", 120)
                message = data.get("message", f"{player_name} has disconnected")
                
                print(f"⚠️ {message}")
                print(f"Waiting {timeout_seconds} seconds for reconnection...")
                
                self.opponent_disconnect_time = disconnect_time
                self.opponent_disconnect_timeout = timeout_seconds
                self.disconnect_reason = message
                self.ui_state = UIState.OPPONENT_DISCONNECTED
                
                # Pause the game and freeze timer
                self.paused = True
                # Freeze the timer by saving elapsed time and clearing turn_start_time
                if self.turn_start_time:
                    elapsed = time.time() - self.turn_start_time
                    self.elapsed_before_pause += elapsed
                    self.turn_start_time = None
                
            def handle_player_reconnected(data):
                """Handle opponent reconnection"""
                player_name = data.get("player", "Opponent")
                player_role = data.get("player_role", "")
                current_player = data.get("current_player")
                board = data.get("board")
                moves = data.get("moves")
                timer_state = data.get("timer_state", {})
                
                print(f"✅ {player_name} has reconnected!")
                print(f"🔧 DEBUG: Syncing timer from server - was paused={self.paused}, ui_state={self.ui_state}")
                
                # Sync game state if provided by server
                if current_player is not None:
                    self.game.current_player = Player(current_player)
                    print(f"🔧 CLIENT: Synchronized current_player to {self.game.current_player.name} (value={current_player})")
                
                if board and moves is not None:
                    # Rebuild board state from server
                    for r in range(min(len(board), 15)):
                        for c in range(min(len(board[r]), 15)):
                            cell = board[r][c]
                            self.game.board[r][c] = Player(cell) if cell in [0, 1, 2] else Player.EMPTY
                    print(f"🔧 DEBUG: Synchronized board - {sum(cell != 0 for row in board for cell in row)} stones")
                
                # Resume the game
                self.opponent_disconnect_time = None
                
                if self.ui_state == UIState.OPPONENT_DISCONNECTED:
                    self.ui_state = UIState.GAMEPLAY
                    print(f"🔧 DEBUG: UI state changed to GAMEPLAY")
                    
                # CRITICAL: Use server's timer state for synchronization
                if timer_state:
                    server_turn_start = timer_state.get("turn_start_time")
                    self.elapsed_before_pause = timer_state.get("elapsed_before_pause", 0)
                    self.move_time_limit = timer_state.get("move_time_limit", 30)
                    # Calculate time since server set the timer
                    if server_turn_start:
                        # Adjust for network delay - server set timer at server_turn_start, we received it now
                        time_since_server_reset = time.time() - server_turn_start
                        self.turn_start_time = time.time()  # Start our timer now
                        self.elapsed_before_pause = time_since_server_reset  # Account for delay
                        print(f"🔧 DEBUG: Synced timer from server - started {time_since_server_reset:.2f}s ago, effective remaining: {self.move_time_limit - time_since_server_reset:.1f}s")
                    else:
                        self.turn_start_time = time.time()
                        print(f"🔧 DEBUG: Server sent no turn_start_time, starting fresh timer")
                else:
                    # Fallback: reset timer locally
                    self.elapsed_before_pause = 0
                    self.turn_start_time = time.time()
                    print(f"🔧 DEBUG: No timer_state from server, using local reset")
                
                self.paused = False  # Unpause
                print(f"🔧 DEBUG: Game unpaused, timer running")
                        
            def handle_game_ended_disconnect(data):
                """Handle game ending due to disconnect (graceful termination)"""
                reason = data.get("reason", "opponent_disconnected")
                disconnected_player = data.get("disconnected_player", "Opponent")
                winner = data.get("winner", self.player_name)
                message = data.get("message", "Game ended due to disconnection")
                no_rematch = data.get("no_rematch", False)
                
                print(f"🏆 {message}")
                
                # Set game state to win (you win by forfeit)
                if self.my_player == Player.BLACK:
                    self.game.game_state = GameState.BLACK_WINS
                    self.game.winner = Player.BLACK
                else:
                    self.game.game_state = GameState.WHITE_WINS
                    self.game.winner = Player.WHITE
                
                # Store that this was a disconnect win (no rematch allowed)
                self.disconnect_reason = message
                self.is_disconnect_win = no_rematch
                self.ui_state = UIState.GAME_OVER
                
                # Play winner sound
                self._play_sound("winner")
            
            def handle_player_left_room(data):
                """Handle when opponent leaves the room"""
                player_name = data.get("player_name", "Unknown")
                print(f"🚪 {player_name} left the room")
                
                # If we're in gameplay or game over, move back to waiting room
                if self.ui_state in [UIState.GAMEPLAY, UIState.GAME_OVER]:
                    # Reset game state
                    self.game.reset_game()
                    self.ui_state = UIState.ROOM_WAITING
                    # Stop background music
                    self._stop_background_music()
                    print(f"📋 Moved back to waiting room (you are now the host)")
            
            self.network_manager.set_message_handler("reconnect_failed", handle_reconnect_failed)
            self.network_manager.set_message_handler("player_disconnected", handle_player_disconnected)
            self.network_manager.set_message_handler("player_reconnected", handle_player_reconnected)
            self.network_manager.set_message_handler("game_ended_disconnect", handle_game_ended_disconnect)
            self.network_manager.set_message_handler("player_left_room", handle_player_left_room)
            
            # Set connection callbacks
            self.network_manager.set_connection_callback("connect", handle_connect)
            self.network_manager.set_connection_callback("disconnect", handle_disconnect)
            self.network_manager.set_connection_callback("connection_lost", lambda: (
                print("🔌 Connection lost!"),
                setattr(self, "disconnect_reason", "Connection to server lost. Attempting to reconnect..."),
                setattr(self, "ui_state", UIState.CONNECTION_LOST)
            ))
            self.network_manager.set_connection_callback("reconnecting", lambda attempt, max_attempts: (
                setattr(self, "reconnection_attempt", attempt),
                setattr(self, "max_reconnection_attempts", max_attempts),
                print(f"🔄 Reconnection attempt {attempt}/{max_attempts}...")
            ))
            self.network_manager.set_connection_callback("reconnect_success", lambda: (
                print("✅ Successfully reconnected to server!"),
                setattr(self, "reconnection_attempt", 0)
            ))
            self.network_manager.set_connection_callback("reconnect_failed", lambda: (
                print("❌ Failed to reconnect to server"),
                setattr(self, "disconnect_reason", "Failed to reconnect to server after multiple attempts"),
                setattr(self, "ui_state", UIState.MAIN_MENU)
            ))
            
            # Get server configuration
            server_config = self.server_config_manager.get_current_config()
            if server_config:
                host, port = server_config.host, server_config.port
                print(f"Connecting to {server_config.name}: {host}:{port}")
                
                if self.network_manager.connect(host, port):
                    print("Connecting to lobby...")
                    # Attempt to resume old game if info exists
                    if self.reconnect_info:
                        print(f"Attempting to reconnect to previous room: {self.reconnect_info}")
                        self.network_manager.send_message("player_reconnect", self.reconnect_info)
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
    
    def _start_ai_thinking(self, ai_player: AIPlayer = None):
        """Start AI thinking in a separate thread"""
        # Use provided AI player or fallback to self.ai_player
        if ai_player is None:
            ai_player = self.ai_player
        
        if self.ai_thinking or not ai_player:
            return
        
        self.ai_thinking = True
        self.ai_move_result = None
        self.thinking_start_time = time.time()
        
        def ai_worker():
            try:
                # Create a copy of the game state for the AI thread
                game_copy = GomokuGame(num_players=self.game.num_players)
                game_copy.board = [row[:] for row in self.game.board]
                game_copy.current_player = self.game.current_player
                game_copy.player_index = self.game.player_index
                game_copy.players = self.game.players[:]
                game_copy.move_history = self.game.move_history[:]
                game_copy.game_state = self.game.game_state
                
                # Get AI move
                move = ai_player.get_move(game_copy)
                self.ai_move_result = move
            except Exception as e:
                print(f"AI thinking error: {e}")
                import traceback
                traceback.print_exc()
                self.ai_move_result = None
        
        self.ai_thread = threading.Thread(target=ai_worker, daemon=True)
        self.ai_thread.start()
        print(f"AI ({self.game.current_player.name}) started thinking... (difficulty: {self.ai_difficulty})")
    
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
