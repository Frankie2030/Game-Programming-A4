import pytest
from ..src.ai import RandomAI, MinimaxAI, MCTS
from ..src.gomoku import GomokuGame, Player, GameState

def test_random_ai_makes_valid_moves():
    game = GomokuGame(size=9)
    ai = RandomAI()
    
    # Test multiple moves to ensure randomness and validity
    for _ in range(10):
        move = ai.get_move(game)
        assert game.is_valid_move(move[0], move[1])
        game.make_move(move[0], move[1])
        if game.game_state != GameState.ONGOING:
            break

def test_minimax_ai_blocks_winning_moves():
    game = GomokuGame(size=9)
    ai = MinimaxAI(max_depth=3)
    
    # Set up a board where opponent (BLACK) is about to win
    # _ _ _ _ _
    # _ B B B _
    # _ _ _ _ _
    game.board[1][1:4] = Player.BLACK.value
    game.current_player = Player.WHITE
    
    # AI (WHITE) should block by placing at either (1,0) or (1,4)
    move = ai.get_move(game)
    assert move in [(1,0), (1,4)]

def test_mcts_basic_functionality():
    game = GomokuGame(size=9)
    ai = MCTS(time_limit=0.1)  # Short time limit for testing
    
    # Test that MCTS makes valid moves
    move = ai.get_move(game)
    assert game.is_valid_move(move[0], move[1])
    
    # Test that MCTS responds to winning threats
    # Set up a board where opponent is about to win
    game.board[1][1:4] = Player.BLACK.value
    game.current_player = Player.WHITE
    
    move = ai.get_move(game)
    assert move in [(1,0), (1,4)]  # Should block the winning move

def test_ai_comparison():
    # Test that harder AIs perform better against random AI
    random_ai = RandomAI()
    minimax_ai = MinimaxAI(max_depth=3)
    mcts_ai = MCTS(time_limit=0.5)
    
    wins = {
        'random': 0,
        'minimax': 0,
        'mcts': 0
    }
    
    # Play 5 games each
    for _ in range(5):
        # Minimax vs Random
        game = GomokuGame(size=9)
        while game.game_state == GameState.ONGOING:
            current_ai = minimax_ai if game.current_player == Player.BLACK else random_ai
            move = current_ai.get_move(game)
            game.make_move(move[0], move[1])
        
        if game.game_state == GameState.BLACK_WIN:
            wins['minimax'] += 1
        elif game.game_state == GameState.WHITE_WIN:
            wins['random'] += 1
            
        # MCTS vs Random
        game = GomokuGame(size=9)
        while game.game_state == GameState.ONGOING:
            current_ai = mcts_ai if game.current_player == Player.BLACK else random_ai
            move = current_ai.get_move(game)
            game.make_move(move[0], move[1])
        
        if game.game_state == GameState.BLACK_WIN:
            wins['mcts'] += 1
        elif game.game_state == GameState.WHITE_WIN:
            wins['random'] += 1
    
    # Stronger AIs should win more often
    assert wins['minimax'] > wins['random']
    assert wins['mcts'] > wins['random']
