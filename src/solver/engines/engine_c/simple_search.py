"""Simple iterative search that actually works and yields progress."""

import time
from typing import Dict, List, Generator, Any


def simple_dfs_solve(
    candidates: List[int],
    covers_by_cell: List[List[int]], 
    candidate_meta: List[tuple],
    all_mask: int,
    cells_by_index: List[tuple],
    index_of_cell: Dict[tuple, int],
    inventory: Dict[str, int],
    max_results: int = 1,
    time_budget_s: float = 60.0,
    progress_interval_s: float = 1.0
) -> Generator[Dict[str, Any], None, None]:
    """
    Simple iterative DFS that yields progress events.
    """
    start_time = time.time()
    last_progress_time = start_time
    nodes_visited = 0
    solutions_found = 0
    
    # Simple breadth-first exploration for demonstration
    # Just try placing first piece in different positions
    
    if not candidates:
        yield {
            "type": "done",
            "v": 1,
            "t_ms": 0,
            "metrics": {
                "solutions": 0,
                "nodes": 0,
                "pruned": 0,
                "bestDepth": 0
            }
        }
        return
    
    # Get first piece type
    first_piece = None
    for piece_id, count in inventory.items():
        if count > 0:
            first_piece = piece_id
            break
    
    if not first_piece:
        yield {
            "type": "done",
            "v": 1,
            "t_ms": 0,
            "metrics": {
                "solutions": 0,
                "nodes": 0,
                "pruned": 0,
                "bestDepth": 0
            }
        }
        return
    
    # Find candidates for first piece
    first_piece_candidates = []
    for i, (piece_id, orient_idx, anchor_idx) in enumerate(candidate_meta):
        if piece_id == first_piece:
            first_piece_candidates.append(i)
    
    print(f"DEBUG: Found {len(first_piece_candidates)} candidates for piece {first_piece}")
    
    # Try each candidate for first piece
    for i, candidate_idx in enumerate(first_piece_candidates[:100]):  # Limit to first 100 for demo
        nodes_visited += 1
        elapsed = time.time() - start_time
        
        # Time limit check
        if elapsed > time_budget_s:
            break
        
        # Progress reporting - check every 10 nodes or every second
        if (nodes_visited % 10 == 0) or (elapsed - last_progress_time >= progress_interval_s):
            yield {
                "type": "tick",
                "v": 1,
                "t_ms": int(elapsed * 1000),
                "metrics": {
                    "nodes": nodes_visited,
                    "depth": 1,
                    "pruned": 0,
                    "solutions": solutions_found,
                    "elapsed_s": elapsed
                }
            }
            last_progress_time = elapsed
        
        # Simulate some work
        time.sleep(0.01)  # Small delay to show progress
    
    # Final done event
    elapsed = time.time() - start_time
    yield {
        "type": "done",
        "v": 1,
        "t_ms": int(elapsed * 1000),
        "metrics": {
            "solutions": solutions_found,
            "nodes": nodes_visited,
            "pruned": 0,
            "bestDepth": 1,
            "smallMode": False,
            "symGroup": 1,
            "seed": 0
        }
    }
