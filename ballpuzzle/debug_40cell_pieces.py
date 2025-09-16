#!/usr/bin/env python3
"""
Debug 40-cell container piece combination generation.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.io.container import load_container

def main():
    print("Loading 40-cell container...")
    container = load_container("data/containers/v1/40 cell.fcc.json")
    
    print(f"Container cells: {len(container['cells'])}")
    print(f"Pieces needed: {len(container['cells']) // 4}")
    print(f"Container size divisible by 4: {len(container['cells']) % 4 == 0}")
    
    # Test piece combination logic
    container_size = len(container['cells'])
    pieces_needed = container_size // 4
    
    available_pieces = {"A": 25, "B": 25, "C": 25, "D": 25, "E": 25}
    total_available = sum(available_pieces.values())
    
    print(f"Pieces needed: {pieces_needed}")
    print(f"Total pieces available: {total_available}")
    print(f"Enough pieces available: {total_available >= pieces_needed}")
    
    # Check if pieces_needed > 10 condition
    print(f"Pieces needed > 10: {pieces_needed > 10}")
    
    if pieces_needed > 10:
        print("Using large container logic...")
        # Simulate the large container combination generation
        combo = {}
        pieces_assigned = 0
        piece_names = list(available_pieces.keys())
        
        for piece in piece_names:
            if pieces_assigned >= pieces_needed:
                break
            count = min(available_pieces[piece], pieces_needed - pieces_assigned)
            if count > 0:
                combo[piece] = count
                pieces_assigned += count
                print(f"  Assigned {count} of piece {piece}, total assigned: {pieces_assigned}")
        
        print(f"Final combination: {combo}")
        print(f"Total pieces in combination: {sum(combo.values())}")
    else:
        print("Would use small container enumeration logic")

if __name__ == "__main__":
    main()
