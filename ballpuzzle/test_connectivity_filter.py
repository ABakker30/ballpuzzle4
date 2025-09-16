#!/usr/bin/env python3
"""
Test DLX vs DFS orientation handling.
"""

from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
from src.pieces.sphere_orientations import get_piece_orientations
from src.solver.engines.engine_c.lattice_fcc import validate_fcc_connectivity

def test_orientation_sources():
    """Compare orientations from library vs sphere_orientations."""
    pieces_dict = load_fcc_A_to_Y()
    
    for piece_name in ['T', 'A', 'E', 'Y']:
        print(f"\n=== {piece_name} piece ===")
        
        # Library orientations
        piece_def = pieces_dict.get(piece_name)
        if piece_def:
            lib_total = len(piece_def.orientations)
            lib_connected = sum(1 for ori in piece_def.orientations if ori and validate_fcc_connectivity(list(ori)))
            print(f"Library: {lib_total} total, {lib_connected} connected")
        
        # Sphere orientations
        try:
            sphere_oris = get_piece_orientations(piece_name)
            sphere_total = len(sphere_oris)
            sphere_connected = sum(1 for ori in sphere_oris if ori and validate_fcc_connectivity([tuple(cell) for cell in ori]))
            print(f"Sphere:  {sphere_total} total, {sphere_connected} connected")
            
            # Show first few orientations
            print(f"First 3 sphere orientations:")
            for i, ori in enumerate(sphere_oris[:3]):
                if ori:
                    connected = validate_fcc_connectivity([tuple(cell) for cell in ori])
                    print(f"  {i}: {ori} -> {'Connected' if connected else 'Disconnected'}")
        except KeyError:
            print(f"Sphere:  KeyError - piece not found")

if __name__ == "__main__":
    test_orientation_sources()
