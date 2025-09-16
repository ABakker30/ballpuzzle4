#!/usr/bin/env python3
"""Convert All 4-Sphere Pieces.txt to JSON format for ballpuzzle4."""

import re
import json
import sys
from pathlib import Path

def main(input_path: str, output_path: str):
    """Read All 4-Sphere Pieces.txt and write pieces_fcc_AtoY.json."""
    
    # Read the input file
    with open(input_path, "r", encoding="utf-8") as f:
        txt = f.read()
    
    # Split by class headers
    blocks = re.split(r"Class\s+\d+:", txt)[1:]  # Skip first empty split
    
    pieces = {}
    
    for block in blocks:
        # Find piece name (A-Y)
        name_match = re.search(r"\b([A-Y])\b", block)
        if not name_match:
            continue
        name = name_match.group(1)
        
        # Find first TRUE line with coordinates
        true_match = re.search(r"<([^>]+)>\s+TRUE\s+\d+", block)
        if not true_match:
            continue
        
        # Extract coordinates from parentheses
        coord_text = true_match.group(1)
        coord_matches = re.findall(r"\(([^)]+)\)", coord_text)
        
        atoms = []
        for coord_str in coord_matches:
            # Extract numbers from coordinate string
            numbers = re.findall(r"-?\d+", coord_str)
            if len(numbers) >= 3:
                atoms.append([int(numbers[0]), int(numbers[1]), int(numbers[2])])
        
        # Only keep pieces with exactly 4 atoms (4-sphere pieces)
        if len(atoms) == 4:
            pieces[name] = atoms
    
    # Write output JSON
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pieces, f, ensure_ascii=False, indent=2)
    
    print(f"Converted {len(pieces)} pieces: {sorted(pieces.keys())}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_all_4sphere_pieces.py <input.txt> <output.json>")
        sys.exit(1)
    
    main(sys.argv[1], sys.argv[2])
