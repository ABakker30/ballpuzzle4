#!/usr/bin/env python3
"""
Generate pieces.json from authoritative Python sources.
This replaces the hand-maintained pieces_fcc_AtoY.json with data from sphere_orientations.py
"""

import json
import sys
from pathlib import Path

# Add the ballpuzzle src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pieces.library_fcc_v1 import load_fcc_A_to_Y

def main():
    """Generate pieces.json from authoritative sphere_orientations.py"""
    
    # Load verified piece definitions
    pieces = load_fcc_A_to_Y()
    
    # Convert to JSON format (use first orientation for each piece)
    pieces_json = {}
    for name, piece_def in pieces.items():
        if piece_def.orientations:
            # Use the first orientation as the canonical one for UI display
            first_orientation = piece_def.orientations[0]
            pieces_json[name] = [list(coord) for coord in first_orientation]
    
    # Write to public directory for UI access
    output_path = Path(__file__).parent / "public" / "pieces.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(pieces_json, f, indent=2)
    
    print(f"Generated {output_path} with {len(pieces_json)} pieces")
    print("Pieces:", sorted(pieces_json.keys()))

if __name__ == "__main__":
    main()
