#!/usr/bin/env python3
"""
Debug piece combination generation for 40-cell container.
"""

import sys
from pathlib import Path
from itertools import combinations_with_replacement

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def generate_piece_combinations_debug(container_size: int, available_pieces: dict, max_combinations: int = 10000):
    """Debug version of piece combination generation."""
    pieces_needed = container_size // 4
    print(f"Container size: {container_size}")
    print(f"Pieces needed: {pieces_needed}")
    print(f"Container size % 4: {container_size % 4}")
    
    if container_size % 4 != 0:
        print("ERROR: Container size not divisible by 4")
        return []
    
    # Check the condition that determines which path to take
    if pieces_needed > 10:
        print("Using large container logic (pieces_needed > 10)")
        # Large container logic
        total_available = sum(available_pieces.values())
        if total_available < pieces_needed:
            print("ERROR: Not enough pieces available")
            return []
        
        combinations = []
        piece_names = list(available_pieces.keys())
        
        combo = {}
        pieces_assigned = 0
        for piece in piece_names:
            if pieces_assigned >= pieces_needed:
                break
            count = min(available_pieces[piece], pieces_needed - pieces_assigned)
            if count > 0:
                combo[piece] = count
                pieces_assigned += count
        
        if pieces_assigned == pieces_needed:
            combinations.append(combo)
        
        print(f"Generated {len(combinations)} combinations")
        return combinations
    else:
        print("Using small container enumeration logic (pieces_needed <= 10)")
        
        combinations = []
        piece_names = list(available_pieces.keys())
        print(f"Piece names: {piece_names}")
        
        # Count total possible combinations
        print("Generating combinations with replacement...")
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
                if available_pieces.get(piece, 0) < count_needed:
                    valid = False
                    break
            
            if valid:
                valid_count += 1
                combinations.append(piece_count)
                if len(combinations) >= max_combinations:
                    print(f"Hit max_combinations limit at {len(combinations)}")
                    break
            
            # Progress reporting
            if count % 10000 == 0:
                print(f"  Processed {count} combinations, found {valid_count} valid")
        
        print(f"Total iterations: {count}")
        print(f"Valid combinations found: {valid_count}")
        print(f"Returned combinations: {len(combinations)}")
        
        if len(combinations) > 0:
            print("First few combinations:")
            for i, combo in enumerate(combinations[:5]):
                print(f"  {i+1}: {combo}")
        
        return combinations

def main():
    print("=== Debugging 40-cell piece combination generation ===")
    
    container_size = 40
    available_pieces = {"A": 10, "B": 10, "C": 10, "D": 10, "E": 10}
    
    combinations = generate_piece_combinations_debug(container_size, available_pieces, max_combinations=1000)
    
    print(f"\nFinal result: {len(combinations)} combinations generated")

if __name__ == "__main__":
    main()
