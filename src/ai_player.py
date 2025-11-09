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
        
        # Debug statistics
        self.pruning_count = 0  # Number of alpha-beta prunings
        self.max_depth_reached = 0  # Maximum depth reached in search
        self.nodes_by_depth = {}  # Count nodes at each depth
        self.move_evaluations = []  # Store move evaluations for debugging
        self.current_search_depth = 0  # Track current search depth
        
        # Real-time thinking state (updated during search for UI display)
        self.real_time_stats = {
            "current_moves": [],  # Moves currently being evaluated
            "best_move_so_far": None,
            "best_score_so_far": float('-inf'),
            "nodes_evaluated": 0,
            "current_depth": 0,
            "is_thinking": False
        }
        
        # Difficulty settings
        self.difficulty_settings = {
            "easy": {"max_depth": 3, "time_limit": 2.0, "use_smart_moves": False, "max_candidates": 25},
            "medium": {"max_depth": 5, "time_limit": 5.0, "use_smart_moves": True, "max_candidates": 45},
            "hard": {"max_depth": 7, "time_limit": 8.0, "use_smart_moves": True, "max_candidates": 55},
            "expert": {"max_depth": 9, "time_limit": 15.0, "use_smart_moves": True, "max_candidates": 70}
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
        self.pruning_count = 0
        self.max_depth_reached = 0
        self.nodes_by_depth = {}
        self.move_evaluations = []
        self.current_search_depth = 0
        
        # Reset real-time stats
        self.real_time_stats = {
            "current_moves": [],
            "best_move_so_far": None,
            "best_score_so_far": float('-inf'),
            "nodes_evaluated": 0,
            "current_depth": 0,
            "is_thinking": True
        }
        
        start_time = time.time()
        
        # Get candidate moves
        if settings["use_smart_moves"]:
            legal_moves = game.get_smart_moves(limit=settings["max_candidates"])
        else:
            legal_moves = game.get_legal_moves()
            if len(legal_moves) > settings["max_candidates"]:
                # For easy mode, randomly sample moves to make it weaker
                legal_moves = random.sample(legal_moves, min(settings["max_candidates"], len(legal_moves)))
        
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
            
            # Update real-time stats
            self.real_time_stats["current_depth"] = depth
            self.real_time_stats["nodes_evaluated"] = self.nodes_evaluated
            
            try:
                move, score = self._minimax_root(game, depth, legal_moves, 
                                               start_time, settings["time_limit"])
                if move:
                    best_move = move
                    # Update best move in real-time stats
                    if score > self.real_time_stats["best_score_so_far"]:
                        self.real_time_stats["best_move_so_far"] = move
                        self.real_time_stats["best_score_so_far"] = score
                    
                # If we found a winning move, stop searching
                if score >= 9000:
                    break
                    
            except TimeoutError:
                break
        
        self.search_time = time.time() - start_time
        self.real_time_stats["is_thinking"] = False
        return best_move
    
    def _minimax_root(self, game: GomokuGame, max_depth: int, 
                     legal_moves: List[Tuple[int, int]], 
                     start_time: float, time_limit: float) -> Tuple[Optional[Tuple[int, int]], int]:
        """Root level minimax search with defensive priority"""
        self.current_search_depth = max_depth
        best_move = None
        best_score = float('-inf')
        
        # CRITICAL: Check for immediate threats that MUST be blocked
        critical_blocks = self._find_critical_blocks(game, legal_moves)
        if critical_blocks:
            # If there are critical threats, prioritize checking these moves first
            priority_moves = critical_blocks
            other_moves = [m for m in legal_moves if m not in critical_blocks]
            ordered_legal_moves = priority_moves + other_moves
        else:
            ordered_legal_moves = legal_moves
        
        # Order moves for better pruning
        scored_moves = []
        for move in ordered_legal_moves:
            row, col = move
            game_copy = game.copy()
            game_copy.make_move(row, col)
            score = game_copy.evaluate_position(self.player)
            scored_moves.append((score, move))
        
        # Sort moves by score (best first for maximizing player)
        scored_moves.sort(reverse=True)
        
        alpha = float('-inf')
        beta = float('inf')
        
        # Track root-level move evaluations
        root_evaluations = []
        
        for move_idx, (_, (row, col)) in enumerate(scored_moves):
            if time.time() - start_time > time_limit:
                raise TimeoutError("Search time limit exceeded")
            
            # Update real-time stats - show current move being evaluated
            self.real_time_stats["current_moves"] = [
                {
                    "move": (row, col),
                    "status": "evaluating",
                    "score": None
                }
            ]
            
            game_copy = game.copy()
            game_copy.make_move(row, col)
            
            score = self._minimax(game_copy, max_depth - 1, alpha, beta, False, 
                                start_time, time_limit, current_depth=1)
            
            eval_info = {
                "move": (row, col),
                "score": score,
                "alpha": alpha,
                "beta": beta
            }
            root_evaluations.append(eval_info)
            
            # Update real-time stats with completed evaluation
            self.real_time_stats["current_moves"] = [
                {
                    "move": eval_info["move"],
                    "status": "completed",
                    "score": eval_info["score"]
                }
            ]
            
            # Update best move in real-time
            if score > best_score:
                best_score = score
                best_move = (row, col)
                self.real_time_stats["best_move_so_far"] = best_move
                self.real_time_stats["best_score_so_far"] = best_score
            
            alpha = max(alpha, score)
            if beta <= alpha:
                self.pruning_count += 1  # Track pruning at root level
                break  # Alpha-beta pruning
        
        # Store all completed evaluations for final display
        self.move_evaluations = root_evaluations
        # Update real-time stats with all evaluated moves (sorted)
        sorted_evals = sorted(root_evaluations, key=lambda x: x['score'], reverse=True)
        self.real_time_stats["current_moves"] = [
            {
                "move": eval_info["move"],
                "status": "completed",
                "score": eval_info["score"]
            }
            for eval_info in sorted_evals[:10]  # Show top 10 moves
        ]
        
        return best_move, best_score
    
    def _minimax(self, game: GomokuGame, depth: int, alpha: float, beta: float, 
                maximizing: bool, start_time: float, time_limit: float, 
                current_depth: int = 0) -> int:
        """
        Minimax algorithm with alpha-beta pruning.
        """
        self.nodes_evaluated += 1
        
        # Track depth statistics
        search_depth = self.current_search_depth - depth + current_depth
        self.max_depth_reached = max(self.max_depth_reached, search_depth)
        if search_depth not in self.nodes_by_depth:
            self.nodes_by_depth[search_depth] = 0
        self.nodes_by_depth[search_depth] += 1
        
        # Check time limit
        if time.time() - start_time > time_limit:
            raise TimeoutError("Search time limit exceeded")
        
        # Terminal conditions
        if depth == 0 or game.game_state != GameState.PLAYING:
            return game.evaluate_position(self.player)
        
        # Get legal moves
        legal_moves = game.get_smart_moves(limit=40) if depth > 2 else game.get_smart_moves(limit=30)
        
        if not legal_moves:
            return game.evaluate_position(self.player)
        
        if maximizing:
            max_eval = float('-inf')
            for row, col in legal_moves:
                game_copy = game.copy()
                game_copy.make_move(row, col)
                
                eval_score = self._minimax(game_copy, depth - 1, alpha, beta, False, 
                                         start_time, time_limit, current_depth + 1)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    self.pruning_count += 1  # Track pruning
                    break  # Alpha-beta pruning
            
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in legal_moves:
                game_copy = game.copy()
                game_copy.make_move(row, col)
                
                eval_score = self._minimax(game_copy, depth - 1, alpha, beta, True, 
                                         start_time, time_limit, current_depth + 1)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    self.pruning_count += 1  # Track pruning
                    break  # Alpha-beta pruning
            
            return min_eval
    
    def get_statistics(self) -> dict:
        """Get AI performance statistics"""
        return {
            "difficulty": self.difficulty,
            "nodes_evaluated": self.nodes_evaluated,
            "search_time": self.search_time,
            "nodes_per_second": self.nodes_evaluated / max(self.search_time, 0.001),
            "pruning_count": self.pruning_count,
            "max_depth_reached": self.max_depth_reached,
            "nodes_by_depth": self.nodes_by_depth.copy(),
            "move_evaluations": self.move_evaluations.copy(),
            "pruning_efficiency": (self.pruning_count / max(self.nodes_evaluated, 1)) * 100 if self.nodes_evaluated > 0 else 0
        }
    
    def get_real_time_stats(self) -> dict:
        """Get real-time thinking statistics for UI display"""
        return self.real_time_stats.copy()
    
    def _find_critical_blocks(self, game: GomokuGame, legal_moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Find moves that block immediate opponent threats.
        Prioritizes blocking 4-in-a-row and open 3-in-a-row (both ends open).
        Returns list of critical blocking moves that should be checked first.
        """
        blocking_fours = []      # HIGHEST PRIORITY: Block 4-in-a-row
        blocking_open_threes = []  # HIGH PRIORITY: Block open 3-in-a-row
        blocking_regular_threes = []  # MEDIUM PRIORITY: Block regular 3s
        
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # horizontal, vertical, diagonals
        
        # Check each legal move to see what opponent threats it blocks
        for move in legal_moves:
            row, col = move
            blocks_four = False
            blocks_open_three = False
            blocks_three = False
            
            # Check all directions from this position
            for dr, dc in directions:
                # Count opponent stones in this direction if we DON'T play here
                opponent_count = 0
                open_ends = 0
                
                # Check positive direction
                r, c = row + dr, col + dc
                consecutive = 0
                while (0 <= r < game.BOARD_SIZE and 0 <= c < game.BOARD_SIZE and consecutive < 5):
                    if game.board[r][c] == self.opponent:
                        consecutive += 1
                        opponent_count += 1
                    elif game.board[r][c] == Player.EMPTY:
                        open_ends += 1
                        break
                    else:
                        break
                    r += dr
                    c += dc
                
                # Check negative direction
                r, c = row - dr, col - dc
                consecutive = 0
                while (0 <= r < game.BOARD_SIZE and 0 <= c < game.BOARD_SIZE and consecutive < 5):
                    if game.board[r][c] == self.opponent:
                        consecutive += 1
                        opponent_count += 1
                    elif game.board[r][c] == Player.EMPTY:
                        open_ends += 1
                        break
                    else:
                        break
                    r -= dr
                    c -= dc
                
                # Classify the threat
                if opponent_count >= 4:
                    # CRITICAL: Opponent has 4-in-a-row, MUST BLOCK!
                    blocks_four = True
                    break  # This is critical, no need to check other directions
                elif opponent_count == 3 and open_ends == 2:
                    # DANGEROUS: Opponent has open three (both ends open)
                    # This will become open four next turn!
                    blocks_open_three = True
                elif opponent_count == 3 and open_ends >= 1:
                    # MODERATE: Opponent has three with at least one end open
                    blocks_three = True
            
            # Categorize the blocking move by priority
            if blocks_four:
                blocking_fours.append(move)
            elif blocks_open_three:
                blocking_open_threes.append(move)
            elif blocks_three:
                blocking_regular_threes.append(move)
        
        # Return in priority order: 4s first, then open 3s, then regular 3s
        critical_moves = blocking_fours + blocking_open_threes + blocking_regular_threes
        
        if blocking_fours:
            print(f"🚨 CRITICAL: Found {len(blocking_fours)} moves blocking 4-in-a-row!")
        if blocking_open_threes:
            print(f"⚠️  HIGH PRIORITY: Found {len(blocking_open_threes)} moves blocking open 3-in-a-row!")
        
        # SECONDARY CHECK: Also check if opponent could win by playing at any position
        winning_threats = []
        for move in legal_moves:
            if move in critical_moves:
                continue  # Already identified
            
            row, col = move
            # Simulate opponent playing there
            game_copy = game.copy()
            game_copy.current_player = self.opponent
            game_copy.make_move(row, col)
            
            # If opponent would win immediately, this MUST be blocked
            if game_copy.game_state != GameState.PLAYING:
                winning_threats.append(move)
                print(f"🚨 WINNING THREAT: Opponent could win at ({row}, {col})!")
        
        # Winning threats have absolute highest priority
        return winning_threats + critical_moves


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

