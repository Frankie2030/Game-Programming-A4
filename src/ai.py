from typing import Tuple, Optional, List
import numpy as np
from .gomoku import GomokuGame, Player, GameState
import random
import math
import time

class Node:
    def __init__(self, game_state: GomokuGame, parent=None, move: Optional[Tuple[int, int]] = None):
        self.game_state = game_state
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = game_state.get_legal_moves()

class MCTS:
    def __init__(self, exploration_weight: float = 1.4, time_limit: float = 1.0):
        self.exploration_weight = exploration_weight
        self.time_limit = time_limit

    def get_move(self, game: GomokuGame) -> Optional[Tuple[int, int]]:
        if game.game_state != GameState.ONGOING:
            return None

        root = Node(game)
        end_time = time.time() + self.time_limit

        while time.time() < end_time:
            node = self._select(root)
            winner = self._simulate(node.game_state)
            self._backpropagate(node, winner)

        if not root.children:
            return random.choice(game.get_legal_moves())

        return max(root.children, key=lambda c: c.visits).move

    def _select(self, node: Node) -> Node:
        while node.game_state.game_state == GameState.ONGOING:
            if node.untried_moves:
                return self._expand(node)
            else:
                node = self._uct_select(node)
        return node

    def _expand(self, node: Node) -> Node:
        move = random.choice(node.untried_moves)
        node.untried_moves.remove(move)
        
        new_game = GomokuGame(node.game_state.size)
        new_game.board = np.copy(node.game_state.board)
        new_game.current_player = node.game_state.current_player
        new_game.make_move(move[0], move[1])
        
        child = Node(new_game, parent=node, move=move)
        node.children.append(child)
        return child

    def _simulate(self, game: GomokuGame) -> Optional[Player]:
        sim_game = GomokuGame(game.size)
        sim_game.board = np.copy(game.board)
        sim_game.current_player = game.current_player

        while sim_game.game_state == GameState.ONGOING:
            moves = sim_game.get_legal_moves()
            if not moves:
                break
            move = random.choice(moves)
            sim_game.make_move(move[0], move[1])

        return sim_game.get_winner()

    def _backpropagate(self, node: Node, winner: Optional[Player]) -> None:
        while node:
            node.visits += 1
            if winner:
                if node.game_state.current_player != winner:
                    node.wins += 1
            node = node.parent

    def _uct_select(self, node: Node) -> Node:
        return max(node.children, key=lambda c: self._uct_value(c))

    def _uct_value(self, node: Node) -> float:
        if node.visits == 0:
            return float('inf')
        return (node.wins / node.visits +
                self.exploration_weight * math.sqrt(math.log(node.parent.visits) / node.visits))


class RandomAI:
    def get_move(self, game: GomokuGame) -> Optional[Tuple[int, int]]:
        legal_moves = game.get_legal_moves()
        return random.choice(legal_moves) if legal_moves else None


class MinimaxAI:
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth

    def get_move(self, game: GomokuGame) -> Optional[Tuple[int, int]]:
        legal_moves = game.get_legal_moves()
        if not legal_moves:
            return None

        best_score = float('-inf')
        best_move = legal_moves[0]

        for move in legal_moves:
            new_game = GomokuGame(game.size)
            new_game.board = np.copy(game.board)
            new_game.current_player = game.current_player
            new_game.make_move(move[0], move[1])
            
            score = self._minimax(new_game, self.max_depth - 1, False, float('-inf'), float('inf'))
            
            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def _minimax(self, game: GomokuGame, depth: int, is_maximizing: bool, alpha: float, beta: float) -> float:
        if depth == 0 or game.game_state != GameState.ONGOING:
            return self._evaluate(game)

        legal_moves = game.get_legal_moves()
        if not legal_moves:
            return 0

        if is_maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                new_game = GomokuGame(game.size)
                new_game.board = np.copy(game.board)
                new_game.current_player = game.current_player
                new_game.make_move(move[0], move[1])
                
                eval = self._minimax(new_game, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                new_game = GomokuGame(game.size)
                new_game.board = np.copy(game.board)
                new_game.current_player = game.current_player
                new_game.make_move(move[0], move[1])
                
                eval = self._minimax(new_game, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate(self, game: GomokuGame) -> float:
        if game.game_state == GameState.BLACK_WIN:
            return 1000 if game.current_player == Player.WHITE else -1000
        elif game.game_state == GameState.WHITE_WIN:
            return 1000 if game.current_player == Player.BLACK else -1000
        elif game.game_state == GameState.DRAW:
            return 0
        
        # Simple heuristic based on number of three-in-a-row sequences
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for i in range(game.size):
            for j in range(game.size):
                if game.board[i][j] != Player.EMPTY.value:
                    for dr, dc in directions:
                        count = 0
                        r, c = i, j
                        while (0 <= r < game.size and 0 <= c < game.size and 
                               game.board[r][c] == game.board[i][j]):
                            count += 1
                            r, c = r + dr, c + dc
                        if count >= 3:
                            score += (1 if game.board[i][j] == Player.BLACK.value else -1)
        
        return score
