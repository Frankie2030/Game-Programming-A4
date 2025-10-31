"""Gomoku rule engine (engine-agnostic)

Board coordinates use (row, col) with 0-based indices.
Player markers are 1 and 2. Empty == 0.
"""
from typing import List, Optional, Tuple


class Gomoku:
    def __init__(self, size: int = 15, win_len: int = 5):
        assert size >= win_len >= 3
        self.size = size
        self.win_len = win_len
        self.board: List[List[int]] = [[0] * size for _ in range(size)]
        self.current_player = 1
        self.winner: Optional[int] = None

    def reset(self) -> None:
        self.board = [[0] * self.size for _ in range(self.size)]
        self.current_player = 1
        self.winner = None

    def place(self, row: int, col: int) -> bool:
        """Place a stone for current player. Return True if placed, False if invalid."""
        if self.winner is not None:
            return False
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        if self.board[row][col] != 0:
            return False
        self.board[row][col] = self.current_player
        if self._check_win_from(row, col):
            self.winner = self.current_player
        else:
            self.current_player = 1 if self.current_player == 2 else 2
        return True

    def _check_win_from(self, row: int, col: int) -> bool:
        player = self.board[row][col]
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            # forward
            r, c = row + dr, col + dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # backward
            r, c = row - dr, col - dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= self.win_len:
                return True
        return False

    def get_available_moves(self) -> List[Tuple[int, int]]:
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == 0:
                    moves.append((r, c))
        return moves

    def is_full(self) -> bool:
        return all(cell != 0 for row in self.board for cell in row)

    def __str__(self) -> str:
        rows = []
        for r in range(self.size):
            rows.append(' '.join(str(x) for x in self.board[r]))
        return '\n'.join(rows)
