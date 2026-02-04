"""
Incremental Number Game
A strategic turn-based game where players race to reach the target number.
"""

import time
import random
import threading
import sys


def timed_input(prompt, timeout):
    """
    Get user input with a timeout.
    Returns (input_value, timed_out) tuple.
    """
    result = [None]
    timed_out = [False]
    
    def get_input():
        try:
            result[0] = input(prompt)
        except:
            pass
    
    input_thread = threading.Thread(target=get_input, daemon=True)
    input_thread.start()
    input_thread.join(timeout)
    
    if input_thread.is_alive():
        timed_out[0] = True
        print(f"\n⏰ TIME'S UP! Auto-selecting move +1")
        return None, True
    
    return result[0], False


def get_safe_numbers(target):
    """
    Calculate safe positions based on the target number.
    Safe numbers are those from which a player can force a win.
    Pattern: Safe numbers are those where (target - current) % 3 == 0
    """
    safe = []
    for i in range(target + 1):
        if (target - i) % 3 == 0:
            safe.append(i)
    return safe


def is_safe_position(current, target):
    """Check if current position is a safe position."""
    return (target - current) % 3 == 0


def minimax(current, target, energy_p1, energy_p2, is_maximizing, difficulty, depth=0, max_depth=10, memo=None):
    """
    Minimax algorithm for optimal move selection with memoization.
    
    Args:
        current: Current position
        target: Target number
        energy_p1: Player 1's energy
        energy_p2: Player 2's energy
        is_maximizing: True if maximizing player (current AI), False if minimizing (opponent)
        difficulty: Game difficulty
        depth: Current search depth
        max_depth: Maximum search depth to prevent infinite recursion
        memo: Memoization dictionary for caching results
        
    Returns:
        (score, best_move) where score is the evaluation and best_move is the optimal move
    """
    # Initialize memoization dictionary
    if memo is None:
        memo = {}
    
    # Create state key for memoization
    state_key = (current, energy_p1, energy_p2, is_maximizing, depth)
    if state_key in memo:
        return memo[state_key]
    
    # Base cases
    if current >= target:
        # Game over - the player who just moved (opposite of current turn) won
        # If is_maximizing=True, opponent (minimizer) just moved and won
        # If is_maximizing=False, we (maximizer) just moved and won
        result = (-1000 + depth, None) if is_maximizing else (1000 - depth, None)
        memo[state_key] = result
        return result
    
    if depth >= max_depth:
        # Depth limit reached - evaluate position heuristically
        distance = target - current
        # Prefer being closer to target and having energy
        score = -distance
        if is_maximizing:
            score += energy_p1 * 2
        else:
            score += energy_p2 * 2
        result = (score, None)
        memo[state_key] = result
        return result
    
    # Get available moves
    moves = [1, 2]
    current_energy = energy_p1 if is_maximizing else energy_p2
    max_energy = 3
    
    # Add energy-powered moves based on difficulty (hard mode only)
    if difficulty == 'hard':
        if current_energy >= 2 and current < target - 4:
            moves.append(3)  # Spend 2 energy for +3
        if current_energy >= 3 and current < target - 5:
            moves.append(4)  # Spend 3 energy for +4
    
    if is_maximizing:
        # Maximizing player - find best move
        max_score = float('-inf')
        best_move = moves[0]
        
        for move in moves:
            if current + move > target:
                continue
                
            # Calculate new energy states
            new_energy_p1 = energy_p1
            new_energy_p2 = energy_p2
            
            if difficulty == 'hard':
                if move == 3:
                    new_energy_p1 = max(0, energy_p1 - 2)  # Spent 2 energy
                elif move == 4:
                    new_energy_p1 = max(0, energy_p1 - 3)  # Spent 3 energy
                elif move == 2:
                    new_energy_p1 = min(energy_p1 + 1, max_energy)
            
            # Recursive call for opponent's turn
            score, _ = minimax(current + move, target, new_energy_p1, new_energy_p2, 
                              False, difficulty, depth + 1, max_depth, memo)
            
            if score > max_score:
                max_score = score
                best_move = move
        
        result = (max_score, best_move)
        memo[state_key] = result
        return result
    else:
        # Minimizing player - opponent tries to minimize our score
        min_score = float('inf')
        best_move = moves[0]
        
        for move in moves:
            if current + move > target:
                continue
                
            # Calculate new energy states
            new_energy_p1 = energy_p1
            new_energy_p2 = energy_p2
            
            if difficulty == 'hard':
                if move == 3:
                    new_energy_p2 = max(0, energy_p2 - 2)  # Opponent spent 2 energy
                elif move == 4:
                    new_energy_p2 = max(0, energy_p2 - 3)  # Opponent spent 3 energy
                elif move == 2:
                    new_energy_p2 = min(energy_p2 + 1, max_energy)
            
            # Recursive call for our turn
            score, _ = minimax(current + move, target, new_energy_p1, new_energy_p2, 
                              True, difficulty, depth + 1, max_depth, memo)
            
            if score < min_score:
                min_score = score
                best_move = move
        
        result = (min_score, best_move)
        memo[state_key] = result
        return result


def ai_move(current, target, energy_ai=0, energy_opponent=0, difficulty='easy'):
    """
    AI makes an optimal move based on game theory.
    
    Args:
        current: Current position
        target: Target number
        energy_ai: AI's current energy (for medium/hard modes)
        energy_opponent: Opponent's energy (for medium/hard modes)
        difficulty: Game difficulty level
    """
    # Calculate the distance to target
    distance = target - current
    
    # Check if we can win this turn with any available move
    max_move = 2  # Default for easy/medium
    if difficulty == 'hard':
        if energy_ai >= 3 and current < target - 5:
            max_move = 4
        elif energy_ai >= 2 and current < target - 4:
            max_move = 3
    elif difficulty == 'medium' and energy_ai >= 2 and current < target - 4:
        max_move = 3
    
    # If we can win with any available move
    if distance <= max_move:
        return min(distance, max_move)
    
    # For hard mode only: use minimax algorithm
    if difficulty == 'hard':
        score, best_move = minimax(current, target, energy_ai, energy_opponent, 
                                   True, difficulty, depth=0, max_depth=8)
        if best_move is not None:
            return best_move
    
    # For easy/medium modes: use safe number strategy
    # Medium mode: Check if using break move (+3) would land on a safe position
    if difficulty == 'medium' and energy_ai >= 2 and current < target - 4:
        if is_safe_position(current + 3, target):
            return 3  # Use break move
    
    # Try to land on a safe position (where (target - position) % 3 == 0)
    for move in [1, 2]:
        new_position = current + move
        if is_safe_position(new_position, target):
            return move
    
    # If we can't land on a safe position, prefer adding 2 to advance faster
    return 2 if distance > 2 else 1


def play_game(target, starting=0, mode='pvp', difficulty='easy', target_range=None, reveal_threshold=None):
    """
    Main game loop.
    
    Args:
        target: The target number to reach
        starting: Starting number (default 0)
        mode: 'pvp' for player vs player, 'pva' for player vs AI
        difficulty: 'easy', 'medium', or 'hard'
        target_range: Tuple (min, max) for hard mode hidden target
        reveal_threshold: Number at which to reveal exact target in hard mode
    """
    current = starting
    current_player = 1
    
    # Energy tracking
    energy_p1 = 0
    energy_p2 = 0
    max_energy = 3 if difficulty == 'hard' else 2
    
    # Timer settings for hard mode - generate new timer per turn
    move_timer = random.randint(10, 15) if difficulty == 'hard' else None
    
    # Hidden target for hard mode
    target_revealed = (difficulty != 'hard')
    
    print(f"\n{'='*50}")
    print(f"INCREMENTAL NUMBER GAME")
    print(f"{'='*50}")
    if difficulty == 'hard' and not target_revealed:
        print(f"Target Range: {target_range[0]}-{target_range[1]}")
        print(f"Exact target will be revealed at {reveal_threshold}")
    else:
        print(f"Target Number: {target}")
    print(f"Starting Number: {starting}")
    print(f"Mode: {'Player vs Player' if mode == 'pvp' else 'Player vs AI'}")
    print(f"Difficulty: {difficulty.upper()}")
    print(f"{'='*50}\n")
    
    # Show difficulty-specific rules
    if difficulty == 'medium':
        print(f"⚡ MEDIUM MODE RULES:")
        print(f"   • Add +2 to gain +1 energy")
        print(f"   • At 2 energy: use BREAK MOVE to add +3")
        print(f"   • Break move resets energy to 0")
        print(f"   • Break move blocked if within {target - 4} of target")
        print(f"   • AI uses safe number strategy with break moves\n")
    elif difficulty == 'hard':
        print(f"🔥 HARD MODE RULES:")
        print(f"   • Add +2 to gain +1 energy (cap: 3)")
        print(f"   • Spend 2 energy → Add +3")
        print(f"   • Spend 3 energy → Add +4")
        print(f"   • Move timer: {move_timer} seconds per turn ⏱️")
        print(f"   • Target hidden until you reach {reveal_threshold}")
        print(f"   • AI uses MINIMAX algorithm (expert level!)\n")
    
    # Show safe positions for strategy (Easy and Medium modes)
    if difficulty in ['easy', 'medium']:
        safe_positions = get_safe_numbers(target)
        print(f"💡 Strategy Tip - Safe positions: {safe_positions}")
        print(f"   (Try to land on these numbers!)\n")
    else:
        print(f"💡 Strategy Tip: Think ahead! AI uses minimax to evaluate all possibilities.\n")
    
    while current < target:
        # Reveal target in hard mode if threshold reached
        if difficulty == 'hard' and not target_revealed and current >= reveal_threshold:
            target_revealed = True
            print(f"\n{'🎯'*25}")
            print(f"TARGET REVEALED: {target}!")
            print(f"{'🎯'*25}\n")
        
        # Display current game state
        print(f"{'─'*50}")
        print(f"Current Number: {current}")
        if target_revealed:
            print(f"Distance to target: {target - current}")
        else:
            print(f"Target Range: {target_range[0]}-{target_range[1]}")
        
        # Display energy
        if difficulty in ['medium', 'hard']:
            if mode == 'pvp':
                print(f"⚡ Energy - Player 1: {energy_p1}/{max_energy} | Player 2: {energy_p2}/{max_energy}")
            else:
                print(f"⚡ Energy - You: {energy_p1}/{max_energy} | AI: {energy_p2}/{max_energy}")
        
        # Get current player's energy
        current_energy = energy_p1 if current_player == 1 else energy_p2
        
        if mode == 'pva' and current_player == 2:
            # AI's turn
            if difficulty == 'hard':
                time.sleep(1)  # Simulate AI thinking time
            
            move = ai_move(current, target, current_energy, energy_p1, difficulty)
            
            if move == 3:
                print(f"🤖 AI (Player 2) spends 2 energy for +3! 💥")
                energy_p2 = max(0, energy_p2 - 2)
            elif move == 4:
                print(f"🤖 AI (Player 2) spends 3 energy for +4! ⚡💥")
                energy_p2 = max(0, energy_p2 - 3)
            else:
                print(f"🤖 AI (Player 2) adds: {move}")
                if difficulty in ['medium', 'hard'] and move == 2:
                    energy_p2 = min(energy_p2 + 1, max_energy)
        else:
            # Human player's turn
            player_name = f"Player {current_player}" if mode == 'pvp' else "You (Player 1)"
            
            # Check available special moves
            can_use_3 = (difficulty in ['medium', 'hard'] and 
                        current_energy >= 2 and 
                        current < target - 4)
            can_use_4 = (difficulty == 'hard' and 
                        current_energy >= 3 and 
                        current < target - 5)
            
            # Generate new timer for this turn in hard mode
            if difficulty == 'hard':
                move_timer = random.randint(10, 15)
            
            move = None  # Initialize move variable
            
            while True:
                try:
                    # Display options
                    if can_use_3 or can_use_4:
                        print(f"\n{player_name}, choose your move:")
                        print(f"  1 - Add +1")
                        print(f"  2 - Add +2 (gain +1 energy)")
                        if can_use_3:
                            print(f"  3 - Add +3 (spend 2 energy) 💥")
                        if can_use_4:
                            print(f"  4 - Add +4 (spend 3 energy) ⚡💥")
                        
                        if difficulty == 'hard':
                            print(f"\n⏱️  Time limit: {move_timer}s")
                            move_input, timeout = timed_input(f"Enter choice: ", move_timer)
                            if timeout:
                                move = 1
                                break
                        else:
                            move_input = input(f"Enter choice: ").strip()
                    else:
                        if difficulty == 'hard':
                            print(f"\n⏱️  Time limit: {move_timer}s")
                            move_input, timeout = timed_input(f"{player_name}, add 1 or 2: ", move_timer)
                            if timeout:
                                move = 1
                                break
                        else:
                            move_input = input(f"{player_name}, add 1 or 2: ").strip()
                    
                    move = int(move_input)
                    
                    # Validate move
                    if move == 4 and can_use_4:
                        if current + 4 <= target:
                            if current_player == 1:
                                energy_p1 = max(0, energy_p1 - 3)
                            else:
                                energy_p2 = max(0, energy_p2 - 3)
                            break
                        else:
                            print(f"❌ Invalid! Adding 4 would exceed the target.")
                    elif move == 3 and can_use_3:
                        if current + 3 <= target:
                            if current_player == 1:
                                energy_p1 = max(0, energy_p1 - 2)
                            else:
                                energy_p2 = max(0, energy_p2 - 2)
                            break
                        else:
                            print(f"❌ Invalid! Adding 3 would exceed the target.")
                    elif move in [1, 2]:
                        if current + move <= target:
                            # Regular move - update energy if move is +2 in medium/hard mode
                            if difficulty in ['medium', 'hard'] and move == 2:
                                if current_player == 1:
                                    energy_p1 = min(energy_p1 + 1, max_energy)
                                else:
                                    energy_p2 = min(energy_p2 + 1, max_energy)
                            break
                        else:
                            print(f"❌ Invalid! Adding {move} would exceed the target.")
                    else:
                        valid_options = "1 or 2"
                        if can_use_3:
                            valid_options += " or 3"
                        if can_use_4:
                            valid_options += " or 4"
                        print(f"❌ Invalid input! Please enter {valid_options}.")
                except ValueError:
                    print("❌ Invalid input! Please enter a number.")
                except KeyboardInterrupt:
                    print("\n\nGame interrupted. Goodbye!")
                    return None
        
        current += move
        
        # Display move result
        if move == 4:
            print(f"⚡💥 SUPER POWER MOVE! +4 → New Number: {current}")
        elif move == 3:
            print(f"💥 POWER MOVE! +3 → New Number: {current}")
        else:
            print(f"➡️  New Number: {current}")
        
        print()
        
        # Check if current player won
        if current == target:
            if mode == 'pva' and current_player == 2:
                print(f"{'='*50}")
                print(f"🤖 AI WINS! Better luck next time!")
                print(f"{'='*50}\n")
            else:
                player_name = f"Player {current_player}" if mode == 'pvp' else "You"
                print(f"{'='*50}")
                print(f"🎉 {player_name} WINS! 🎉")
                print(f"{'='*50}\n")
            return current_player
        
        # Switch players
        current_player = 2 if current_player == 1 else 1
    
    return None


def main():
    """Main function to run the game."""
    print("\n" + "="*50)
    print("  WELCOME TO INCREMENTAL NUMBER GAME!")
    print("="*50)
    
    while True:
        print("\n📋 GAME MENU")
        print("1. Player vs Player")
        print("2. Player vs AI")
        print("3. How to Play")
        print("4. Exit")
        
        choice = input("\nSelect an option (1-4): ").strip()
        
        if choice == '1':
            mode = 'pvp'
        elif choice == '2':
            mode = 'pva'
        elif choice == '3':
            print("\n" + "="*50)
            print("HOW TO PLAY")
            print("="*50)
            print("""
📖 Basic Rules:
- Players take turns adding 1 or 2 to the current number
- The game starts at 0 (or a chosen starting number)
- The first player to reach the target number WINS!

🎯 Strategy (Easy Mode):
- Safe positions are numbers where (target - current) % 3 == 0
- Try to land on safe positions to control the game
- Force your opponent onto unsafe positions

⚡ MEDIUM MODE (Energy System + Safe Numbers):
- Adding +2 gives you +1 energy (cap: 2)
- Spend 2 energy: Add +3 (power move!)
- AI uses safe number strategy with break moves
- Strategy: Build energy and plan power moves on safe positions

🔥 HARD MODE (Advanced Energy + Hidden Target):
- Adding +2 gives you +1 energy (cap: 3)
- Spend 2 energy → Add +3
- Spend 3 energy → Add +4 (super power!)
- Target hidden in range until revealed
- Move timer: 10-15 seconds per turn ⏱️
- AI uses MINIMAX algorithm (expert level!)
            """)
            continue
        elif choice == '4':
            print("\nThanks for playing! Goodbye! 👋\n")
            break
        else:
            print("❌ Invalid option! Please select 1-4.")
            continue
        
        # Select difficulty
        print("\n🎮 SELECT DIFFICULTY:")
        print("1. Easy (Classic safe number strategy)")
        print("2. Medium (Energy system + Power moves)")
        print("3. Hard (Advanced energy + Hidden target + Timer)")
        
        diff_choice = input("\nSelect difficulty (1-3): ").strip()
        
        if diff_choice == '1':
            difficulty = 'easy'
        elif diff_choice == '2':
            difficulty = 'medium'
        elif diff_choice == '3':
            difficulty = 'hard'
        else:
            print("❌ Invalid option! Defaulting to Easy.")
            difficulty = 'easy'
        
        # Get game settings
        try:
            if difficulty == 'hard':
                # Hard mode: use target range
                print("\n🔥 HARD MODE: Set target range")
                range_min = int(input("Enter minimum target (e.g., 20): ").strip())
                range_max = int(input("Enter maximum target (e.g., 30): ").strip())
                
                # Validate range
                if range_min <= 0 or range_max <= range_min:
                    print("❌ Invalid range! Max must be greater than min.")
                    continue
                
                if range_max - range_min < 5:
                    print("❌ Range too small! Range must be at least 5 (e.g., 20-25).")
                    continue
                
                # Generate random target within range
                target = random.randint(range_min, range_max)
                target_range = (range_min, range_max)
                
                # Calculate reveal threshold (e.g., 70% of range_min)
                reveal_threshold = max(1, int(range_min * 0.7))
                
                starting_input = input(f"Enter starting number (press Enter for 0): ").strip()
                starting = int(starting_input) if starting_input else 0
                
                if starting < 0 or starting >= reveal_threshold:
                    print(f"❌ Starting number must be between 0 and {reveal_threshold - 1}!")
                    continue
                
                # Ensure reveal happens before target can be reached
                if reveal_threshold >= range_min - 5:
                    reveal_threshold = max(1, range_min - 5)
                
                print(f"\n✅ Target set within range {range_min}-{range_max}")
                print(f"   Exact target will be revealed at {reveal_threshold}\n")
                
            else:
                # Easy/Medium mode: normal target
                target = int(input("\nEnter target number (e.g., 30): ").strip())
                if target <= 0:
                    print("❌ Target must be a positive number!")
                    continue
                
                starting_input = input("Enter starting number (press Enter for 0): ").strip()
                starting = int(starting_input) if starting_input else 0
                
                if starting < 0 or starting >= target:
                    print("❌ Starting number must be between 0 and target!")
                    continue
                
                target_range = None
                reveal_threshold = None
            
        except ValueError:
            print("❌ Invalid input! Please enter valid numbers.")
            continue
        
        # Play the game
        play_game(target, starting, mode, difficulty, target_range, reveal_threshold)
        
        # Ask if want to play again
        play_again = input("Play again? (y/n): ").strip().lower()
        if play_again != 'y':
            print("\nThanks for playing! Goodbye! 👋\n")
            break


if __name__ == "__main__":
    main()

