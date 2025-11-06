"""
AI Validator - Test and validate AI player correctness
"""

from gomoku_game import GomokuGame, Player, GameState
from ai_player import AIPlayer
import time


def validate_ai_move(game: GomokuGame, ai_player: AIPlayer, expected_valid: bool = True) -> dict:
    """
    Validate that AI makes a valid move.
    
    Args:
        game: Current game state
        ai_player: AI player instance
        expected_valid: Whether the move should be valid
    
    Returns:
        dict with validation results
    """
    if game.current_player != ai_player.player:
        return {
            "valid": False,
            "error": f"Not AI's turn. Current player: {game.current_player.name}, AI player: {ai_player.player.name}"
        }
    
    if game.game_state != GameState.PLAYING:
        return {
            "valid": False,
            "error": f"Game is not in PLAYING state: {game.game_state.value}"
        }
    
    # Get AI move
    start_time = time.time()
    move = ai_player.get_move(game)
    elapsed = time.time() - start_time
    
    if move is None:
        return {
            "valid": False,
            "error": "AI returned None (no move available)"
        }
    
    row, col = move
    
    # Validate move
    is_valid = game.is_valid_move(row, col)
    
    result = {
        "valid": is_valid == expected_valid,
        "move": (row, col),
        "is_valid_move": is_valid,
        "expected_valid": expected_valid,
        "time_taken": elapsed,
        "nodes_evaluated": ai_player.nodes_evaluated,
        "search_time": ai_player.search_time
    }
    
    if not is_valid:
        result["error"] = f"AI suggested invalid move: ({row}, {col})"
    
    return result


def test_ai_basic(game: GomokuGame, ai_player: AIPlayer) -> dict:
    """
    Run basic AI tests.
    
    Returns:
        dict with test results
    """
    results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    # Test 1: First move should be center
    game.reset_game()
    ai_player.player = Player.BLACK
    game.current_player = Player.BLACK
    
    move = ai_player.get_move(game)
    center = game.BOARD_SIZE // 2
    if move == (center, center):
        results["passed"] += 1
        results["tests"].append({"test": "First move is center", "passed": True})
    else:
        results["failed"] += 1
        results["tests"].append({
            "test": "First move is center",
            "passed": False,
            "expected": (center, center),
            "got": move
        })
    
    # Test 2: AI should make valid moves
    game.reset_game()
    ai_player.player = Player.BLACK
    game.current_player = Player.BLACK
    
    # Make a few moves
    game.make_move(7, 7)  # Human move
    game.make_move(7, 8)  # AI move (if it was AI's turn)
    
    # Now test AI move
    ai_player.player = Player.WHITE
    game.current_player = Player.WHITE
    
    validation = validate_ai_move(game, ai_player, expected_valid=True)
    if validation["valid"]:
        results["passed"] += 1
        results["tests"].append({"test": "AI makes valid moves", "passed": True})
    else:
        results["failed"] += 1
        results["tests"].append({
            "test": "AI makes valid moves",
            "passed": False,
            "error": validation.get("error", "Unknown error")
        })
    
    # Test 3: AI should not make moves when it's not its turn
    game.reset_game()
    ai_player.player = Player.WHITE
    game.current_player = Player.BLACK  # Not AI's turn
    
    try:
        move = ai_player.get_move(game)
        results["failed"] += 1
        results["tests"].append({
            "test": "AI doesn't move when not its turn",
            "passed": False,
            "error": "AI should raise ValueError when not its turn"
        })
    except ValueError:
        results["passed"] += 1
        results["tests"].append({
            "test": "AI doesn't move when not its turn",
            "passed": True
        })
    
    return results


def print_ai_validation_report(results: dict):
    """Print a formatted validation report"""
    print("\n" + "="*60)
    print("AI VALIDATION REPORT")
    print("="*60)
    print(f"Tests Passed: {results['passed']}")
    print(f"Tests Failed: {results['failed']}")
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print("\nTest Details:")
    print("-"*60)
    
    for i, test in enumerate(results["tests"], 1):
        status = "✅ PASSED" if test["passed"] else "❌ FAILED"
        print(f"{i}. {test['test']}: {status}")
        if not test["passed"]:
            if "error" in test:
                print(f"   Error: {test['error']}")
            if "expected" in test:
                print(f"   Expected: {test['expected']}")
            if "got" in test:
                print(f"   Got: {test['got']}")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    """Run AI validation tests"""
    print("Running AI validation tests...")
    
    game = GomokuGame()
    ai_player = AIPlayer(Player.BLACK, "medium")
    
    results = test_ai_basic(game, ai_player)
    print_ai_validation_report(results)

