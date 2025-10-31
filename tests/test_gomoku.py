import pytest

from A4.src.gomoku import Gomoku


def test_horizontal_win():
    g = Gomoku(size=9, win_len=5)
    row = 4
    # place 4 moves for player 1 and player 2 interleaved; ensure player1 gets 5th
    for c in range(4):
        assert g.place(row, c) is True  # p1, p2, p1, p2 alternation will be handled
        # After each placement, next player toggles
    # Ensure placing until win for current player
    # Determine whose turn it is
    # Force current player to 1 and set pieces for testing
    g.reset()
    for c in range(5):
        g.current_player = 1
        assert g.place(row, c)
        if c < 4:
            # force opponent to skip by making them place somewhere else
            g.current_player = 2
            g.place(0, 0) if g.board[0][0] == 0 else None
    assert g.winner == 1


def test_vertical_win():
    g = Gomoku(size=9, win_len=4)
    col = 3
    for r in range(4):
        g.current_player = 1
        assert g.place(r, col)
        if r < 3:
            g.current_player = 2
            g.place(0, 0) if g.board[0][0] == 0 else None
    assert g.winner == 1


def test_diagonal_win():
    g = Gomoku(size=9, win_len=4)
    coords = [(1, 1), (2, 2), (3, 3), (4, 4)]
    for i, (r, c) in enumerate(coords):
        g.current_player = 1
        assert g.place(r, c)
        if i < len(coords) - 1:
            g.current_player = 2
            g.place(0, 0) if g.board[0][0] == 0 else None
    assert g.winner == 1


def test_invalid_placement():
    g = Gomoku(size=5, win_len=3)
    assert g.place(0, 0) is True
    assert g.place(0, 0) is False  # occupied
    assert g.place(10, 10) is False  # out of bounds
