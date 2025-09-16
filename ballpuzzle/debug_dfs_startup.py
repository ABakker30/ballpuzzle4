#!/usr/bin/env python3
"""
Debug DFS engine startup to see why it's not exploring nodes.
"""

from src.solver.engines.dfs_engine import DFSEngine
from src.io.container import load_container
from src.pieces.inventory import PieceBag
from src.pieces.library_fcc_v1 import load_fcc_A_to_Y
from src.solver.engine_api import EngineOptions

def debug_dfs_startup():
    """Debug DFS engine startup."""
    
    # Load container
    container = load_container("data/containers/v1/40 cell.fcc.json")
    print(f"Container loaded: {len(container['cells'])} cells")
    
    # Create inventory - test with subset first
    inventory = PieceBag({'A': 3, 'E': 3, 'T': 2, 'Y': 2})
    print(f"Inventory: A={inventory.get_count('A')}, E={inventory.get_count('E')}, T={inventory.get_count('T')}, Y={inventory.get_count('Y')}")
    
    # Load pieces
    pieces = load_fcc_A_to_Y()
    print(f"Pieces loaded: {len(pieces)} piece types")
    
    # Create engine
    engine = DFSEngine()
    options = EngineOptions(max_results=1, time_limit=5)
    
    print("Starting DFS engine...")
    
    # Try to get first event
    try:
        events = list(engine.solve(container, inventory, pieces, options))
        print(f"Events generated: {len(events)}")
        for i, event in enumerate(events):
            print(f"Event {i}: {event.get('type', 'unknown')} - {event.get('metrics', {})}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_dfs_startup()
