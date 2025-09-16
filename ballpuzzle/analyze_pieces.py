#!/usr/bin/env python3
"""Analyze piece types and their orientations."""

from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
from src.coords.symmetry_fcc import ROTATIONS_24

def main():
    print("=== Piece Analysis: A-Y Pieces ===")
    
    pieces = load_fcc_A_to_Y()
    
    print(f"Total pieces available: {len(pieces)}")
    print(f"Piece IDs: {', '.join(sorted(pieces.keys()))}")
    
    print("\nDetailed piece analysis:")
    print("-" * 60)
    
    total_orientations = 0
    
    for piece_id in sorted(pieces.keys()):
        piece_def = pieces[piece_id]
        
        # Get base atoms
        if hasattr(piece_def, 'atoms'):
            base_atoms = list(piece_def.atoms)
        elif isinstance(piece_def, dict) and "cells" in piece_def:
            base_atoms = [tuple(cell) for cell in piece_def["cells"]]
        else:
            base_atoms = []
        
        # Count unique orientations by applying all 24 FCC rotations
        unique_orientations = set()
        
        for rot_matrix in ROTATIONS_24:
            # Apply rotation to all atoms
            rotated_atoms = []
            for atom in base_atoms:
                x, y, z = atom
                # Apply 3x3 rotation matrix
                new_x = rot_matrix[0][0] * x + rot_matrix[0][1] * y + rot_matrix[0][2] * z
                new_y = rot_matrix[1][0] * x + rot_matrix[1][1] * y + rot_matrix[1][2] * z
                new_z = rot_matrix[2][0] * x + rot_matrix[2][1] * y + rot_matrix[2][2] * z
                rotated_atoms.append((new_x, new_y, new_z))
            
            # Normalize to canonical form (translate so min coord is at origin)
            if rotated_atoms:
                min_x = min(atom[0] for atom in rotated_atoms)
                min_y = min(atom[1] for atom in rotated_atoms)
                min_z = min(atom[2] for atom in rotated_atoms)
                
                canonical = tuple(sorted([
                    (atom[0] - min_x, atom[1] - min_y, atom[2] - min_z)
                    for atom in rotated_atoms
                ]))
                
                unique_orientations.add(canonical)
        
        num_orientations = len(unique_orientations)
        total_orientations += num_orientations
        
        print(f"Piece {piece_id}: {len(base_atoms):2d} atoms, {num_orientations:2d} orientations")
        print(f"         Base shape: {base_atoms}")
    
    print("-" * 60)
    print(f"Total orientations across all pieces: {total_orientations}")
    print(f"Average orientations per piece: {total_orientations / len(pieces):.1f}")
    
    # Estimate candidate count
    container_size = 100  # Shape_3 has 100 cells
    estimated_candidates = 0
    
    for piece_id in sorted(pieces.keys()):
        piece_def = pieces[piece_id]
        if hasattr(piece_def, 'atoms'):
            base_atoms = list(piece_def.atoms)
        elif isinstance(piece_def, dict) and "cells" in piece_def:
            base_atoms = [tuple(cell) for cell in piece_def["cells"]]
        else:
            base_atoms = []
        
        # Count unique orientations
        unique_orientations = set()
        for rot_matrix in ROTATIONS_24:
            rotated_atoms = []
            for atom in base_atoms:
                x, y, z = atom
                new_x = rot_matrix[0][0] * x + rot_matrix[0][1] * y + rot_matrix[0][2] * z
                new_y = rot_matrix[1][0] * x + rot_matrix[1][1] * y + rot_matrix[1][2] * z
                new_z = rot_matrix[2][0] * x + rot_matrix[2][1] * y + rot_matrix[2][2] * z
                rotated_atoms.append((new_x, new_y, new_z))
            
            if rotated_atoms:
                min_x = min(atom[0] for atom in rotated_atoms)
                min_y = min(atom[1] for atom in rotated_atoms)
                min_z = min(atom[2] for atom in rotated_atoms)
                
                canonical = tuple(sorted([
                    (atom[0] - min_x, atom[1] - min_y, atom[2] - min_z)
                    for atom in rotated_atoms
                ]))
                
                unique_orientations.add(canonical)
        
        num_orientations = len(unique_orientations)
        
        # Rough estimate: each orientation can be placed at multiple anchor positions
        # For a 4-atom piece in a 100-cell container, roughly 97 positions per orientation
        piece_size = len(base_atoms)
        approx_positions = max(1, container_size - piece_size * 10)  # Rough estimate
        piece_candidates = num_orientations * approx_positions
        estimated_candidates += piece_candidates
        
        print(f"Piece {piece_id}: ~{piece_candidates:4d} candidates ({num_orientations} orientations × ~{approx_positions} positions)")
    
    print(f"\nEstimated total candidates for 25 pieces: ~{estimated_candidates:,}")

if __name__ == '__main__':
    main()
