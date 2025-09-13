#!/usr/bin/env python3
"""
Debug piece combination generation with correct logic for 1-of-each inventory.
"""

import sys
from pathlib import Path
from itertools import combinations

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_correct_combination_logic():
    """Test correct combination generation for 10 pieces from 25 types (1 each)."""
    print("=== Correct Combination Generation Test ===")
    
    # Default CLI inventory: 1 of each piece A-Y
    piece_names = [chr(ord('A') + i) for i in range(25)]
    pieces_needed = 10
    
    print(f"Available pieces: {piece_names}")
    print(f"Pieces needed: {pieces_needed}")
    print(f"Total piece types: {len(piece_names)}")
    
    # The correct approach: combinations (not combinations_with_replacement)
    # We need to choose 10 different pieces from 25 available types
    print(f"\nGenerating combinations of {pieces_needed} pieces from {len(piece_names)} types...")
    
    combinations_list = []
    count = 0
    
    # Use combinations (not combinations_with_replacement) since we have 1 of each
    for combo in combinations(piece_names, pieces_needed):
        count += 1
        # Each piece appears exactly once in the combination
        piece_count = {piece: 1 for piece in combo}
        combinations_list.append(piece_count)
        
        if count >= 10:  # Show first 10 for testing
            break
    
    print(f"Generated {len(combinations_list)} combinations (showing first 10)")
    
    for i, combo in enumerate(combinations_list):
        total_pieces = sum(combo.values())
        pieces_str = ','.join(sorted(combo.keys()))
        print(f"  {i+1}: {pieces_str} (total: {total_pieces})")
    
    # Calculate total possible combinations
    from math import comb
    total_possible = comb(25, 10)
    print(f"\nTotal possible combinations: {total_possible:,}")
    
    return len(combinations_list) > 0

def main():
    success = test_correct_combination_logic()
    if success:
        print("\n✓ Combination generation works correctly!")
        print("The DFS engine should use combinations() not combinations_with_replacement()")
    else:
        print("\n✗ Combination generation failed")

if __name__ == "__main__":
    main()
