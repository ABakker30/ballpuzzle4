#!/usr/bin/env python3
"""
Debug script to systematically identify DFS engine issues.
"""

import json
import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.solver.engines.dfs_engine import DFSEngine
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y

def debug_basic_setup():
    """Test basic engine instantiation and inventory processing."""
    print("=== DEBUG: Basic Setup ===")
    
    # Load container
    with open('data/containers/v1/40 cell.fcc.json', 'r') as f:
        container = json.load(f)
    
    # Test inventory processing
    inventory = {'pieces': {'A': 3, 'E': 3, 'T': 2, 'Y': 2}}
    
    print(f"Container cells: {len(container['cells'])}")
    print(f"Inventory: {inventory}")
    
    # Check piece library
    pieces_dict = load_fcc_A_to_Y()
    print(f"Available pieces: {list(pieces_dict.keys())}")
    for name in ['A', 'E', 'T', 'Y']:
        if name in pieces_dict:
            print(f"{name}: {len(pieces_dict[name].orientations)} orientations")
        else:
            print(f"{name}: NOT FOUND in piece library")
    
    return container, inventory

def debug_engine_initialization(container, inventory):
    """Test engine initialization and early processing."""
    print("\n=== DEBUG: Engine Initialization ===")
    
    engine = DFSEngine()
    
    # Try to get the first few events from the solver
    try:
        events = list(engine.solve(container, inventory, {"max_results": 1, "time_limit": 1}))
        print(f"Events generated: {len(events)}")
        for i, event in enumerate(events):
            print(f"Event {i}: {event['type']}")
            if event['type'] == 'done':
                metrics = event['metrics']
                print(f"  Solutions: {metrics['solutions_found']}")
                print(f"  Nodes: {metrics['nodes_explored']}")
                print(f"  Max depth: {metrics['max_depth_reached']}")
    except Exception as e:
        print(f"ERROR during solve: {e}")
        import traceback
        traceback.print_exc()

def debug_piece_orientations():
    """Debug piece orientation filtering."""
    print("\n=== DEBUG: Piece Orientations ===")
    
    from src.solver.engines.dfs_engine import _is_fcc_connected_4
    pieces_dict = load_fcc_A_to_Y()
    
    for name in ['A', 'E', 'T', 'Y']:
        pdef = pieces_dict[name]
        print(f"\n{name} piece:")
        print(f"  Total orientations: {len(pdef.orientations)}")
        
        connected_count = 0
        for i, ori in enumerate(pdef.orientations[:3]):  # Check first 3
            o = [tuple(map(int, c)) for c in ori]
            is_connected = _is_fcc_connected_4(o)
            if is_connected:
                connected_count += 1
            print(f"  Ori {i}: {ori} -> Connected: {is_connected}")
        
        # Count all connected
        all_connected = sum(1 for ori in pdef.orientations 
                           if _is_fcc_connected_4([tuple(map(int, c)) for c in ori]))
        print(f"  Total connected: {all_connected}/{len(pdef.orientations)}")

def debug_multiset_generation():
    """Debug multiset combination generation."""
    print("\n=== DEBUG: Multiset Generation ===")
    
    # Test the multiset generation function directly
    from src.solver.engines.dfs_engine import DFSEngine
    
    # Create a mock engine instance to access the internal function
    engine = DFSEngine()
    container_size = 40
    piece_counts = {'A': 3, 'E': 3, 'T': 2, 'Y': 2}
    
    print(f"Container size: {container_size}")
    print(f"Piece counts: {piece_counts}")
    print(f"Pieces needed: {container_size // 4}")
    
    # This would require accessing the internal function, which is complex
    # Let's just check the basic math
    total_pieces = sum(piece_counts.values())
    pieces_needed = container_size // 4
    print(f"Total available pieces: {total_pieces}")
    print(f"Pieces needed: {pieces_needed}")
    print(f"Exact match: {total_pieces == pieces_needed}")

if __name__ == "__main__":
    container, inventory = debug_basic_setup()
    debug_piece_orientations()
    debug_multiset_generation()
    debug_engine_initialization(container, inventory)
