"""
Gomoku Game Core Logic
Implements the complete Gomoku game rules and board management.
"""

import copy
from typing import List, Tuple, Optional, Set
from enum import Enum


class Player(Enum):
    """Player types in the game"""
    EMPTY = 0
    BLACK = 1  # First player (X)
    WHITE = 2  # Second player (O)
    RED = 3    # Third player (for 3+ player games)
    BLUE = 4   # Fourth player (for 4+ player games)
    GREEN = 5  # Fifth player (for 5 player games)
    
    @classmethod
    def get_player_by_index(cls, index: int):
        """Get player by index (0=EMPTY, 1=BLACK, 2=WHITE, etc.)"""
        players = [cls.EMPTY, cls.BLACK, cls.WHITE, cls.RED, cls.BLUE, cls.GREEN]
        if 0 <= index < len(players):
            return players[index]
        return cls.EMPTY
    
    @classmethod
    def get_all_players(cls, count: int):
        """Get list of players for a game with count players"""
        all_players = [cls.BLACK, cls.WHITE, cls.RED, cls.BLUE, cls.GREEN]
        return all_players[:count]


class GameState(Enum):
    """Game state enumeration"""
    PLAYING = "playing"
    BLACK_WINS = "black_wins"
    WHITE_WINS = "white_wins"
    DRAW = "draw"


class Move:
    """Represents a move in the game"""
    def __init__(self, row: int, col: int, player: Player):
        self.row = row
        self.col = col
        self.player = player
    
    def __eq__(self, other):
        return (self.row == other.row and 
                self.col == other.col and 
                self.player == other.player)
    
    def __str__(self):
        return f"Move({self.row}, {self.col}, {self.player.name})"


class GomokuGame:
    """
    Complete Gomoku game implementation with standard rules.
    Board size: 15x15
    Win condition: 5 stones in a row (horizontal, vertical, diagonal)
    Supports 2-5 players
    """
    
    BOARD_SIZE = 15
    WIN_LENGTH = 5
    
    def __init__(self, num_players: int = 2):
        """
        Initialize game with specified number of players (2-5)
        """
        if num_players < 2 or num_players > 5:
            raise ValueError("Number of players must be between 2 and 5")
        
        self.num_players = num_players
        self.players = Player.get_all_players(num_players)
        self.player_index = 0  # Index into self.players list
        
        self.board = [[Player.EMPTY for _ in range(self.BOARD_SIZE)] 
                      for _ in range(self.BOARD_SIZE)]
        self.current_player = self.players[0]  # Start with first player
        self.move_history = []
        self.game_state = GameState.PLAYING
        self.winner = None
        
    def reset_game(self):
        """Reset the game to initial state"""
        self.board = [[Player.EMPTY for _ in range(self.BOARD_SIZE)] 
                      for _ in range(self.BOARD_SIZE)]
        self.player_index = 0
        self.current_player = self.players[0]
        self.move_history = []
        self.game_state = GameState.PLAYING
        self.winner = None
    
    def is_valid_move(self, row: int, col: int) -> bool:
        """Check if a move is valid"""
        if not (0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE):
            return False
        return self.board[row][col] == Player.EMPTY
    
    def make_move(self, row: int, col: int) -> bool:
        """
        Make a move on the board
        Returns True if move was successful, False otherwise
        """
        if not self.is_valid_move(row, col) or self.game_state != GameState.PLAYING:
            return False
        
        # Place the stone
        self.board[row][col] = self.current_player
        move = Move(row, col, self.current_player)
        self.move_history.append(move)
        
        # Check for win
        if self.check_win(row, col):
            self.winner = self.current_player
            # Set game state based on winner
            if self.current_player == Player.BLACK:
                self.game_state = GameState.BLACK_WINS
            elif self.current_player == Player.WHITE:
                self.game_state = GameState.WHITE_WINS
            else:
                # For 3+ player games, use BLACK_WINS as generic win state
                # The winner is stored in self.winner
                self.game_state = GameState.BLACK_WINS
        elif self.is_board_full():
            self.game_state = GameState.DRAW
        else:
            # Switch to next player in rotation
            self.player_index = (self.player_index + 1) % len(self.players)
            self.current_player = self.players[self.player_index]
        
        return True
    
    def undo_move(self) -> bool:
        """Undo the last move"""
        if not self.move_history:
            return False
        
        last_move = self.move_history.pop()
        self.board[last_move.row][last_move.col] = Player.EMPTY
        self.current_player = last_move.player
        self.game_state = GameState.PLAYING
        self.winner = None
        
        return True
    
    def check_win(self, row: int, col: int) -> bool:
        """Check if the last move resulted in a win"""
        player = self.board[row][col]
        if player == Player.EMPTY:
            return False
        
        # Check all four directions: horizontal, vertical, diagonal1, diagonal2
        directions = [
            (0, 1),   # horizontal
            (1, 0),   # vertical
            (1, 1),   # diagonal \
            (1, -1)   # diagonal /
        ]
        
        for dr, dc in directions:
            count = 1  # Count the placed stone
            
            # Check positive direction
            r, c = row + dr, col + dc
            while (0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and 
                   self.board[r][c] == player):
                count += 1
                r += dr
                c += dc
            
            # Check negative direction
            r, c = row - dr, col - dc
            while (0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and 
                   self.board[r][c] == player):
                count += 1
                r -= dr
                c -= dc
            
            if count >= self.WIN_LENGTH:
                return True
        
        return False
    
    def is_board_full(self) -> bool:
        """Check if the board is full"""
        for row in self.board:
            for cell in row:
                if cell == Player.EMPTY:
                    return False
        return True
    
    def get_legal_moves(self) -> List[Tuple[int, int]]:
        """Get all legal moves on the board"""
        moves = []
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                if self.board[row][col] == Player.EMPTY:
                    moves.append((row, col))
        return moves
    
    def get_smart_moves(self, limit: int = 50) -> List[Tuple[int, int]]:
        """
        Get a limited set of promising moves for AI evaluation.
        Returns moves near existing stones to improve AI performance.
        Prioritizes moves within 2 squares of existing stones for deeper search.
        """
        if not self.move_history:
            # First move - return center and nearby positions
            center = self.BOARD_SIZE // 2
            return [(center, center), (center-1, center), (center+1, center),
                    (center, center-1), (center, center+1)]
        
        candidate_moves = set()
        
        # Add moves within 2 squares of existing stones (for better tactical play)
        search_radius = 2
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                if self.board[row][col] != Player.EMPTY:
                    # Add all positions within search_radius
                    for dr in range(-search_radius, search_radius + 1):
                        for dc in range(-search_radius, search_radius + 1):
                            if dr == 0 and dc == 0:
                                continue
                            new_row, new_col = row + dr, col + dc
                            if (0 <= new_row < self.BOARD_SIZE and 
                                0 <= new_col < self.BOARD_SIZE and
                                self.board[new_row][new_col] == Player.EMPTY):
                                candidate_moves.add((new_row, new_col))
        
        # Sort moves by strategic value (closer to center is better early game)
        center = self.BOARD_SIZE // 2
        moves_with_score = []
        for move in candidate_moves:
            row, col = move
            # Calculate distance from center (Manhattan distance)
            center_distance = abs(row - center) + abs(col - center)
            # Calculate proximity to existing stones
            min_distance = self.BOARD_SIZE
            for r in range(self.BOARD_SIZE):
                for c in range(self.BOARD_SIZE):
                    if self.board[r][c] != Player.EMPTY:
                        dist = max(abs(row - r), abs(col - c))  # Chebyshev distance
                        min_distance = min(min_distance, dist)
            
            # Prefer moves close to existing stones and not too far from center
            score = -min_distance * 10 - center_distance
            moves_with_score.append((score, move))
        
        # Sort by score and return top candidates
        moves_with_score.sort(reverse=True)
        moves = [move for score, move in moves_with_score]
        
        return moves[:limit] if len(moves) > limit else moves
    
    def evaluate_position(self, player: Player) -> int:
        """
        Enhanced evaluation function with strong defensive capabilities.
        Returns a score where positive is good for the player.
        """
        if self.game_state == GameState.BLACK_WINS:
            return 100000 if player == Player.BLACK else -100000
        elif self.game_state == GameState.WHITE_WINS:
            return 100000 if player == Player.WHITE else -100000
        elif self.game_state == GameState.DRAW:
            return 0
        
        score = 0
        opponent = Player.WHITE if player == Player.BLACK else Player.BLACK
        
        # First, check for immediate threats that MUST be blocked
        player_score = 0
        opponent_score = 0
        
        # Evaluate all lines on the board (check existing patterns)
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # horizontal, vertical, diagonals
        
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                if self.board[row][col] != Player.EMPTY:
                    # Evaluate patterns starting from occupied positions
                    for dr, dc in directions:
                        # Only check in positive direction to avoid double counting
                        player_at_pos = self.board[row][col]
                        pattern_score = self._evaluate_pattern(row, col, dr, dc, player_at_pos)
                        if player_at_pos == player:
                            player_score += pattern_score
                        else:
                            opponent_score += pattern_score
                
                else:
                    # Evaluate potential of empty positions
                    player_potential = self._evaluate_position_potential(row, col, player)
                    opponent_potential = self._evaluate_position_potential(row, col, opponent)
                    
                    player_score += player_potential
                    opponent_score += opponent_potential
        
        # CRITICAL: Heavily weight opponent threats for defensive play
        # If opponent has a strong threat (open four, open three), prioritize blocking
        if opponent_score >= 12000:  # Opponent has open four (15000) or near-win
            # MUST block immediately - make defense absolutely critical
            score = -opponent_score * 2.5
            print(f"🚨 CRITICAL THREAT DETECTED! Opponent score: {opponent_score}")
        elif opponent_score >= 4000:  # Opponent has open three (5000) or four (8000)
            # Very high priority defense - open three WILL become open four!
            score = player_score - (opponent_score * 2.2)
            print(f"⚠️  HIGH THREAT: Open three or four detected! Opponent score: {opponent_score}")
        elif opponent_score >= 700:  # Opponent has three with one end open
            # High priority defense
            score = player_score - (opponent_score * 1.8)
        else:
            # Normal play - still defensive but balanced
            score = player_score - (opponent_score * 1.3)
        
        return int(score)
    
    
    def _evaluate_pattern(self, row: int, col: int, dr: int, dc: int, player: Player) -> int:
        """
        Evaluate a pattern starting from a given position.
        Returns score for the pattern found.
        """
        count = 1  # Count the starting stone
        open_ends = 0
        
        # Check positive direction
        r, c = row + dr, col + dc
        empty_after = False
        while (0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and count < 5):
            if self.board[r][c] == player:
                count += 1
            elif self.board[r][c] == Player.EMPTY:
                empty_after = True
                break
            else:
                break
            r += dr
            c += dc
        
        if empty_after:
            open_ends += 1
        
        # Check negative direction
        r, c = row - dr, col - dc
        empty_before = False
        while (0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and count < 5):
            if self.board[r][c] == player:
                count += 1
            elif self.board[r][c] == Player.EMPTY:
                empty_before = True
                break
            else:
                break
            r -= dr
            c -= dc
        
        if empty_before:
            open_ends += 1
        
        # Score based on pattern strength
        if count >= 5:
            return 50000  # Five in a row (win)
        elif count == 4:
            if open_ends == 2:
                return 15000  # Open four (unstoppable - absolutely critical!)
            elif open_ends == 1:
                return 8000   # Four with one end open (must block!)
            else:
                return 1000   # Four blocked both ends
        elif count == 3:
            if open_ends == 2:
                return 5000   # Open three (CRITICAL - will become open four!)
            elif open_ends == 1:
                return 800    # Three with one end open (important)
            else:
                return 100    # Three blocked both ends
        elif count == 2:
            if open_ends == 2:
                return 100    # Open two
            elif open_ends == 1:
                return 20     # Two with one end open
            else:
                return 5      # Two blocked both ends
        elif count == 1:
            if open_ends >= 1:
                return 2      # Single stone with potential
        
        return 0
    
    def _evaluate_position_potential(self, row: int, col: int, player: Player) -> int:
        """Evaluate the potential value of a position for a player"""
        if self.board[row][col] != Player.EMPTY:
            return 0
        
        total_score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            line_score = self._evaluate_line(row, col, dr, dc, player)
            total_score += line_score
        
        return total_score
    
    def _evaluate_line(self, row: int, col: int, dr: int, dc: int, player: Player) -> int:
        """Evaluate a line in a specific direction if we place a stone at (row, col)"""
        # Count consecutive stones and open ends in this direction
        count = 1  # Count the stone we're about to place
        open_ends = 0
        
        # Check positive direction
        r, c = row + dr, col + dc
        while (0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and count < 5):
            if self.board[r][c] == player:
                count += 1
            elif self.board[r][c] == Player.EMPTY:
                open_ends += 1
                break
            else:
                break
            r += dr
            c += dc
        
        # If we went off board or hit maximum, check if edge is open
        if count < 5 and 0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE:
            if self.board[r][c] == Player.EMPTY:
                open_ends += 1
        
        # Check negative direction
        r, c = row - dr, col - dc
        while (0 <= r < self.BOARD_SIZE and 0 <= c < self.BOARD_SIZE and count < 5):
            if self.board[r][c] == player:
                count += 1
            elif self.board[r][c] == Player.EMPTY:
                open_ends += 1
                break
            else:
                break
            r -= dr
            c -= dc
        
        # Score based on count and openness
        if count >= 5:
            return 100000  # Winning move
        elif count == 4:
            if open_ends >= 1:
                return 50000  # Four that can become five
            else:
                return 5000   # Four blocked
        elif count == 3:
            if open_ends == 2:
                return 5000   # Open three (very strong)
            elif open_ends == 1:
                return 1000   # Three with one end open
            else:
                return 200    # Blocked three
        elif count == 2:
            if open_ends == 2:
                return 500    # Open two
            elif open_ends == 1:
                return 100    # Two with one end
            else:
                return 20     # Blocked two
        elif count == 1:
            if open_ends >= 1:
                return 10     # Single potential
        
        return 5  # Base value for any position
    
    def copy(self):
        """Create a deep copy of the game state"""
        new_game = GomokuGame()
        new_game.board = copy.deepcopy(self.board)
        new_game.current_player = self.current_player
        new_game.move_history = copy.deepcopy(self.move_history)
        new_game.game_state = self.game_state
        new_game.winner = self.winner
        return new_game
    
    def get_board_string(self) -> str:
        """Get a string representation of the board for debugging"""
        result = "  "
        for i in range(self.BOARD_SIZE):
            result += f"{i:2d}"
        result += "\n"
        
        for i, row in enumerate(self.board):
            result += f"{i:2d}"
            for cell in row:
                if cell == Player.EMPTY:
                    result += " ."
                elif cell == Player.BLACK:
                    result += " X"
                else:
                    result += " O"
            result += "\n"
        
        return result

