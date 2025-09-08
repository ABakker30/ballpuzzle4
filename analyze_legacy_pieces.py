#!/usr/bin/env python3
"""
Analyze legacy piece data to understand orientation discrepancies.
Compare legacy piece orientations with our current FCC analysis.
"""

import json
import os
from collections import defaultdict
from pathlib import Path

def load_legacy_result(filepath):
    """Load a legacy result file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def extract_piece_orientations(legacy_data):
    """Extract piece orientations from legacy data."""
    piece_orientations = {}
    
    for piece in legacy_data['pieces']:
        piece_id = piece['id']
        cells_ijk = piece['cells_ijk']
        
        # Convert to tuple for hashing
        orientation = tuple(tuple(cell) for cell in cells_ijk)
        piece_orientations[piece_id] = orientation
    
    return piece_orientations

def normalize_piece_coordinates(cells_ijk):
    """Normalize piece coordinates by translating to origin."""
    if not cells_ijk:
        return cells_ijk
    
    # Find minimum coordinates
    min_i = min(cell[0] for cell in cells_ijk)
    min_j = min(cell[1] for cell in cells_ijk)
    min_k = min(cell[2] for cell in cells_ijk)
    
    # Translate to origin
    normalized = []
    for cell in cells_ijk:
        normalized.append((cell[0] - min_i, cell[1] - min_j, cell[2] - min_k))
    
    # Sort for canonical form
    return tuple(sorted(normalized))

def analyze_legacy_orientations():
    """Analyze orientations across all legacy result files."""
    legacy_dir = Path("C:/Ball Puzzle/legacy results")
    
    # Track unique orientations per piece across all results
    piece_orientations = defaultdict(set)
    piece_counts = defaultdict(int)
    
    # Process all legacy result files
    for result_file in legacy_dir.glob("*.json"):
        print(f"Processing {result_file.name}...")
        
        try:
            legacy_data = load_legacy_result(result_file)
            orientations = extract_piece_orientations(legacy_data)
            
            for piece_id, orientation in orientations.items():
                # Normalize the orientation
                normalized = normalize_piece_coordinates(orientation)
                piece_orientations[piece_id].add(normalized)
                piece_counts[piece_id] += 1
                
        except Exception as e:
            print(f"Error processing {result_file}: {e}")
            continue
    
    return piece_orientations, piece_counts

def compare_with_current_analysis():
    """Compare legacy orientations with our current FCC analysis."""
    
    # Load our current analysis results
    current_analysis_file = "C:/Ball Puzzle/ballpuzzle/analyze_pieces.py"
    
    print("=== LEGACY PIECE ORIENTATION ANALYSIS ===\n")
    
    piece_orientations, piece_counts = analyze_legacy_orientations()
    
    print(f"Found {len(piece_orientations)} unique pieces in legacy data")
    print(f"Processed {sum(piece_counts.values())} total piece placements\n")
    
    # Analyze each piece
    total_unique_orientations = 0
    
    for piece_id in sorted(piece_orientations.keys()):
        unique_orientations = len(piece_orientations[piece_id])
        total_placements = piece_counts[piece_id]
        
        print(f"Piece {piece_id}:")
        print(f"  Unique orientations: {unique_orientations}")
        print(f"  Total placements: {total_placements}")
        
        # Show a sample orientation
        sample_orientation = next(iter(piece_orientations[piece_id]))
        print(f"  Sample orientation: {sample_orientation}")
        print()
        
        total_unique_orientations += unique_orientations
    
    print(f"=== SUMMARY ===")
    print(f"Total unique orientations across all pieces: {total_unique_orientations}")
    print(f"Average orientations per piece: {total_unique_orientations / len(piece_orientations):.1f}")
    
    # Compare with expected FCC orientations (24 max per piece)
    print(f"\n=== COMPARISON WITH FCC THEORY ===")
    print(f"Expected max orientations per piece (FCC): 24")
    
    pieces_with_max_orientations = sum(1 for orientations in piece_orientations.values() 
                                     if len(orientations) == 24)
    pieces_with_fewer_orientations = len(piece_orientations) - pieces_with_max_orientations
    
    print(f"Pieces with 24 orientations: {pieces_with_max_orientations}")
    print(f"Pieces with fewer orientations: {pieces_with_fewer_orientations}")
    
    # Show pieces with fewer than 24 orientations
    if pieces_with_fewer_orientations > 0:
        print(f"\nPieces with symmetry (fewer than 24 orientations):")
        for piece_id in sorted(piece_orientations.keys()):
            unique_count = len(piece_orientations[piece_id])
            if unique_count < 24:
                print(f"  {piece_id}: {unique_count} orientations")

def analyze_specific_piece_shapes():
    """Analyze the actual shapes of pieces to understand symmetry."""
    piece_orientations, _ = analyze_legacy_orientations()
    
    print(f"\n=== PIECE SHAPE ANALYSIS ===")
    
    for piece_id in sorted(piece_orientations.keys())[:5]:  # Analyze first 5 pieces
        orientations = piece_orientations[piece_id]
        print(f"\nPiece {piece_id} ({len(orientations)} orientations):")
        
        # Show all orientations for this piece
        for i, orientation in enumerate(sorted(orientations)):
            print(f"  Orientation {i+1}: {orientation}")

if __name__ == "__main__":
    compare_with_current_analysis()
    analyze_specific_piece_shapes()
