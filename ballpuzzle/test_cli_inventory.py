#!/usr/bin/env python3
"""
Test CLI inventory handling and DFS engine with 1 of each piece A-Y.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.solver.registry import get_engine
from src.io.container import load_container

def test_default_inventory():
    """Test with default CLI inventory: 1 of each piece A-Y."""
    print("=== Testing Default CLI Inventory (1 of each A-Y) ===")
    
    # Replicate CLI default inventory
    default_inventory = {chr(ord('A') + i): 1 for i in range(25)}
    print(f"Default inventory: {len(default_inventory)} pieces")
    print(f"First few: {dict(list(default_inventory.items())[:5])}")
    print(f"Total pieces: {sum(default_inventory.values())}")
    
    # Load 40-cell container
    container = load_container("data/containers/v1/40 cell.fcc.json")
    container_size = len(container['cells'])
    pieces_needed = container_size // 4
    
    print(f"\nContainer: {container_size} cells, needs {pieces_needed} pieces")
    print(f"Available pieces: {sum(default_inventory.values())}")
    print(f"Enough pieces: {sum(default_inventory.values()) >= pieces_needed}")
    
    # Test piece combination generation with this inventory
    print(f"\nTesting piece combination generation...")
    
    if container_size % 4 != 0:
        print("ERROR: Container size not divisible by 4")
        return
    
    # Check which path the DFS engine will take
    if pieces_needed > 10:
        print("Will use large container logic (pieces_needed > 10)")
    else:
        print("Will use small container enumeration logic (pieces_needed <= 10)")
        
        # Test if we can generate any combinations
        from itertools import combinations_with_replacement
        
        piece_names = list(default_inventory.keys())
        max_combinations = 1000  # Smaller limit for testing
        
        combinations = []
        count = 0
        
        print(f"Generating combinations with {len(piece_names)} piece types...")
        
        for combo in combinations_with_replacement(piece_names, pieces_needed):
            count += 1
            if count > max_combinations * 10:  # Safety limit
                break
                
            # Count pieces in this combination
            piece_count = {}
            for piece in combo:
                piece_count[piece] = piece_count.get(piece, 0) + 1
            
            # Check if we have enough inventory (1 of each)
            valid = True
            for piece, count_needed in piece_count.items():
                if default_inventory.get(piece, 0) < count_needed:
                    valid = False
                    break
            
            if valid:
                combinations.append(piece_count)
                if len(combinations) >= max_combinations:
                    break
        
        print(f"Generated {len(combinations)} valid combinations")
        
        if len(combinations) > 0:
            print("First few combinations:")
            for i, combo in enumerate(combinations[:3]):
                total_pieces = sum(combo.values())
                print(f"  {i+1}: {combo} (total: {total_pieces})")
        else:
            print("ERROR: No valid combinations found!")
            print("This explains why DFS engine completes immediately with 0 nodes")

def main():
    test_default_inventory()

if __name__ == "__main__":
    main()
