#!/usr/bin/env python3
"""Debug piece combination generation for duplicate inventories."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from itertools import combinations as iter_combinations

def debug_generate_piece_combinations_chunked(container_size: int, available_pieces: dict, max_combinations: int = 1000):
    """Debug version of the DFS piece combination generation function."""
    print(f"DEBUG: Container size = {container_size}")
    print(f"DEBUG: Available pieces = {available_pieces}")
    
    pieces_needed = container_size // 4
    print(f"DEBUG: Pieces needed = {pieces_needed}")
    
    if container_size % 4 != 0:
        print("DEBUG: Container size not divisible by 4, returning empty list")
        return []
    
    # For large containers, use single combination approach
    if pieces_needed > 10:
        print("DEBUG: Large container (>10 pieces), using greedy approach")
        total_available = sum(available_pieces.values())
        print(f"DEBUG: Total available pieces = {total_available}")
        
        if total_available < pieces_needed:
            print("DEBUG: Not enough pieces available")
            return []
        
        combo = {}
        pieces_assigned = 0
        for piece in sorted(available_pieces.keys()):
            if pieces_assigned >= pieces_needed:
                break
            count = min(available_pieces[piece], pieces_needed - pieces_assigned)
            if count > 0:
                combo[piece] = count
                pieces_assigned += count
                print(f"DEBUG: Assigned {count} of piece {piece}, total assigned = {pieces_assigned}")
        
        result = [combo] if pieces_assigned == pieces_needed else []
        print(f"DEBUG: Large container result = {result}")
        return result
    
    # For smaller containers, use greedy approach prioritizing known working combinations
    print("DEBUG: Small container (<=10 pieces), using combination approach")
    combinations = []
    
    # Prioritize known working combinations first
    working_combos = [
        {'A': 2, 'E': 1, 'T': 1},
        {'A': 1, 'E': 1, 'T': 2},
        {'E': 2, 'T': 2},
    ]
    
    print("DEBUG: Checking working combinations...")
    for combo in working_combos:
        print(f"DEBUG: Checking combo {combo}")
        if sum(combo.values()) == pieces_needed:
            print(f"DEBUG: Combo sum matches pieces needed ({pieces_needed})")
            valid = True
            for piece, count_needed in combo.items():
                available_count = available_pieces.get(piece, 0)
                print(f"DEBUG: Piece {piece}: need {count_needed}, have {available_count}")
                if available_count < count_needed:
                    valid = False
                    print(f"DEBUG: Not enough {piece} pieces")
                    break
            if valid:
                combinations.append(combo)
                print(f"DEBUG: Added working combo: {combo}")
        else:
            print(f"DEBUG: Combo sum {sum(combo.values())} != pieces needed {pieces_needed}")
    
    # Add other combinations using itertools
    print("DEBUG: Generating additional combinations with itertools...")
    piece_names = list(available_pieces.keys())
    print(f"DEBUG: Piece names = {piece_names}")
    
    if len(piece_names) >= pieces_needed:
        print(f"DEBUG: Enough piece types ({len(piece_names)}) for combinations")
        count = 0
        for combo in iter_combinations(piece_names, pieces_needed):
            count += 1
            if count > max_combinations:
                print(f"DEBUG: Hit max combinations limit ({max_combinations})")
                break
            
            piece_count = {piece: 1 for piece in combo}
            print(f"DEBUG: Generated combo: {piece_count}")
            if piece_count not in combinations:
                combinations.append(piece_count)
                print(f"DEBUG: Added new combo: {piece_count}")
            else:
                print(f"DEBUG: Combo already exists, skipping")
    else:
        print(f"DEBUG: Not enough piece types ({len(piece_names)}) for {pieces_needed} pieces")
    
    print(f"DEBUG: Final combinations = {combinations}")
    return combinations

def test_inventories():
    """Test both standard and duplicate inventories."""
    
    print("=" * 60)
    print("TESTING STANDARD INVENTORY (A=1,B=1,...,J=1)")
    print("=" * 60)
    
    standard_inventory = {chr(ord('A') + i): 1 for i in range(10)}  # A=1,B=1,...,J=1
    standard_combos = debug_generate_piece_combinations_chunked(40, standard_inventory)
    print(f"Standard inventory result: {len(standard_combos)} combinations")
    
    print("\n" + "=" * 60)
    print("TESTING DUPLICATE INVENTORY (A=3,E=3,T=2,Y=2)")
    print("=" * 60)
    
    duplicate_inventory = {'A': 3, 'E': 3, 'T': 2, 'Y': 2}
    duplicate_combos = debug_generate_piece_combinations_chunked(40, duplicate_inventory)
    print(f"Duplicate inventory result: {len(duplicate_combos)} combinations")

if __name__ == "__main__":
    test_inventories()
