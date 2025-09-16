#!/usr/bin/env python3
"""
Debug DFS engine execution flow to find where it's failing.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.io.container import load_container

def debug_piece_combinations():
    """Debug the piece combination generation step by step."""
    print("=== Debugging DFS Engine Flow ===")
    
    # Load container
    container = load_container("data/containers/v1/40 cell.fcc.json")
    container_size = len(container['cells'])
    print(f"Container size: {container_size} cells")
    
    # Setup piece inventory (A-Y)
    piece_counts = {}
    for i in range(25):
        piece_name = chr(ord('A') + i)
        piece_counts[piece_name] = 5
    
    print(f"Piece inventory: {len(piece_counts)} types, {sum(piece_counts.values())} total")
    
    # Replicate the combination generation logic
    pieces_needed = container_size // 4
    print(f"Pieces needed: {pieces_needed}")
    
    if container_size % 4 != 0:
        print("ERROR: Container size not divisible by 4")
        return
    
    # Check which path the engine takes
    if pieces_needed > 10:
        print("Taking large container path (pieces_needed > 10)")
    else:
        print("Taking small container path (pieces_needed <= 10)")
        
        # Generate combinations using the engine's logic
        from itertools import combinations_with_replacement
        
        combinations = []
        piece_names = list(piece_counts.keys())
        max_combinations = 10000
        
        print(f"Generating combinations with {len(piece_names)} piece types...")
        print(f"First few piece names: {piece_names[:10]}")
        
        count = 0
        valid_count = 0
        
        for combo in combinations_with_replacement(piece_names, pieces_needed):
            count += 1
            if count > max_combinations * 10:  # Safety limit
                print(f"Hit safety limit at {count} iterations")
                break
                
            # Count pieces in this combination
            piece_count = {}
            for piece in combo:
                piece_count[piece] = piece_count.get(piece, 0) + 1
            
            # Check if we have enough inventory
            valid = True
            for piece, count_needed in piece_count.items():
                if piece_counts.get(piece, 0) < count_needed:
                    valid = False
                    break
            
            if valid:
                valid_count += 1
                combinations.append(piece_count)
                if len(combinations) >= max_combinations:
                    break
            
            if count % 50000 == 0:
                print(f"  Progress: {count} iterations, {valid_count} valid combinations")
        
        print(f"Generated {len(combinations)} valid combinations")
        
        # Check the hardcoded working combinations
        working_combos = [
            {'A': 2, 'E': 1, 'T': 1},  # Known working
            {'A': 1, 'E': 1, 'T': 2},  # Variation
            {'E': 2, 'T': 2},          # Different combination
        ]
        
        print(f"Checking {len(working_combos)} hardcoded working combinations...")
        prioritized = []
        for combo in working_combos:
            if combo in combinations:
                print(f"  Found working combo: {combo}")
                combinations.remove(combo)
                prioritized.append(combo)
            else:
                print(f"  Missing working combo: {combo}")
        
        final_combinations = prioritized + combinations
        print(f"Final combinations count: {len(final_combinations)}")
        
        if len(final_combinations) == 0:
            print("ERROR: No valid combinations found!")
            return
        
        print("First few final combinations:")
        for i, combo in enumerate(final_combinations[:5]):
            print(f"  {i+1}: {combo}")
    
    print("\nCombination generation completed successfully")

if __name__ == "__main__":
    debug_piece_combinations()
