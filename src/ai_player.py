"""
AI Player Implementation for Gomoku
Implements Minimax with Alpha-Beta pruning and multiple difficulty levels.
"""

import time
import random
from typing import Tuple, Optional, List
from gomoku_game import GomokuGame, Player, GameState


class AIPlayer:
    """
    AI Player with configurable difficulty levels using Minimax with Alpha-Beta pruning.
    """
    
    def __init__(self, player: Player, difficulty: str = "medium"):
        self.player = player
        self.opponent = Player.WHITE if player == Player.BLACK else Player.BLACK
        self.difficulty = difficulty
        self.nodes_evaluated = 0
        self.search_time = 0
        
        # Difficulty settings
        self.difficulty_settings = {
            "easy": {"max_depth": 2, "time_limit": 1.0, "use_smart_moves": False},
            "medium": {"max_depth": 4, "time_limit": 3.0, "use_smart_moves": True},
            "hard": {"max_depth": 6, "time_limit": 5.0, "use_smart_moves": True},
            "expert": {"max_depth": 8, "time_limit": 10.0, "use_smart_moves": True}
        }
        
        if difficulty not in self.difficulty_settings:
            raise ValueError(f"Invalid difficulty: {difficulty}. Must be one of {list(self.difficulty_settings.keys())}")
    
    def get_move(self, game: GomokuGame) -> Tuple[int, int]:
        """
        Get the best move for the current game state.
        Returns (row, col) tuple.
        """
        if game.current_player != self.player:
            raise ValueError("It's not this AI player's turn")
        
        settings = self.difficulty_settings[self.difficulty]
        
        # Handle first move specially
        if not game.move_history:
            center = game.BOARD_SIZE // 2
            return (center, center)
        
        # Reset statistics
        self.nodes_evaluated = 0
        start_time = time.time()
        
        # Get candidate moves
        if settings["use_smart_moves"]:
            legal_moves = game.get_smart_moves(limit=30)
        else:
            legal_moves = game.get_legal_moves()
            if len(legal_moves) > 20:
                # For easy mode, randomly sample moves to make it weaker
                legal_moves = random.sample(legal_moves, min(20, len(legal_moves)))
        
        if not legal_moves:
            return None
        
        # If only one move, return it
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        # Use iterative deepening for better time management
        best_move = legal_moves[0]
        
        for depth in range(1, settings["max_depth"] + 1):
            if time.time() - start_time > settings["time_limit"]:
                break
            
            try:
                move, score = self._minimax_root(game, depth, legal_moves, 
                                               start_time, settings["time_limit"])
                if move:
                    best_move = move
                    
                # If we found a winning move, stop searching
                if score >= 9000:
                    break
                    
            except TimeoutError:
                break
        
        self.search_time = time.time() - start_time
        return best_move
    
    def _minimax_root(self, game: GomokuGame, max_depth: int, 
                     legal_moves: List[Tuple[int, int]], 
                     start_time: float, time_limit: float) -> Tuple[Optional[Tuple[int, int]], int]:
        """Root level minimax search"""
        best_move = None
        best_score = float('-inf')
        
        # Order moves for better pruning
        scored_moves = []
        for move in legal_moves:
            row, col = move
            game_copy = game.copy()
            game_copy.make_move(row, col)
            score = game_copy.evaluate_position(self.player)
            scored_moves.append((score, move))
        
        # Sort moves by score (best first for maximizing player)
        scored_moves.sort(reverse=True)
        
        alpha = float('-inf')
        beta = float('inf')
        
        for _, (row, col) in scored_moves:
            if time.time() - start_time > time_limit:
                raise TimeoutError("Search time limit exceeded")
            
            game_copy = game.copy()
            game_copy.make_move(row, col)
            
            score = self._minimax(game_copy, max_depth - 1, alpha, beta, False, 
                                start_time, time_limit)
            
            if score > best_score:
                best_score = score
                best_move = (row, col)
            
            alpha = max(alpha, score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        
        return best_move, best_score
    
    def _minimax(self, game: GomokuGame, depth: int, alpha: float, beta: float, 
                maximizing: bool, start_time: float, time_limit: float) -> int:
        """
        Minimax algorithm with alpha-beta pruning.
        """
        self.nodes_evaluated += 1
        
        # Check time limit
        if time.time() - start_time > time_limit:
            raise TimeoutError("Search time limit exceeded")
        
        # Terminal conditions
        if depth == 0 or game.game_state != GameState.PLAYING:
            return game.evaluate_position(self.player)
        
        # Get legal moves
        legal_moves = game.get_smart_moves(limit=25) if depth > 1 else game.get_smart_moves(limit=15)
        
        if not legal_moves:
            return game.evaluate_position(self.player)
        
        if maximizing:
            max_eval = float('-inf')
            for row, col in legal_moves:
                game_copy = game.copy()
                game_copy.make_move(row, col)
                
                eval_score = self._minimax(game_copy, depth - 1, alpha, beta, False, 
                                         start_time, time_limit)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break  # Alpha-beta pruning
            
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in legal_moves:
                game_copy = game.copy()
                game_copy.make_move(row, col)
                
                eval_score = self._minimax(game_copy, depth - 1, alpha, beta, True, 
                                         start_time, time_limit)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break  # Alpha-beta pruning
            
            return min_eval
    
    def get_statistics(self) -> dict:
        """Get AI performance statistics"""
        return {
            "difficulty": self.difficulty,
            "nodes_evaluated": self.nodes_evaluated,
            "search_time": self.search_time,
            "nodes_per_second": self.nodes_evaluated / max(self.search_time, 0.001)
        }


class RandomAI:
    """Random AI player for baseline comparison"""
    
    def __init__(self, player: Player):
        self.player = player
    
    def get_move(self, game: GomokuGame) -> Tuple[int, int]:
        """Get a random legal move"""
        legal_moves = game.get_legal_moves()
        if not legal_moves:
            return None
        return random.choice(legal_moves)
    
    def get_statistics(self) -> dict:
        """Get AI statistics"""
        return {
            "difficulty": "random",
            "nodes_evaluated": 0,
            "search_time": 0,
            "nodes_per_second": 0
        }

