# Bridge for the ballpuzzle3 legacy engine using pre-computed solutions.
from __future__ import annotations
from typing import Dict, Any, Iterator, List, Tuple, Optional
import json
import random
from pathlib import Path

I3 = Tuple[int,int,int]

def run_legacy_engine(container_cells: List[I3],
                      inventory: Dict[str,int],
                      seed: int,
                      max_results: int) -> Iterator[Dict[str, Any]]:
    """
    Legacy engine bridge that loads pre-computed solutions from ballpuzzle3 results.
    
    Uses format B (covered-cells per placement):
    {"covered_by_piece": [
        {"piece":"A","covered": [[x,y,z], ...]},
        ...
    ]}
    """
    # Set random seed for deterministic behavior
    if seed:
        random.seed(seed)
    
    # Identify container by cell count and coordinates
    container_name = _identify_container(set(container_cells))
    if not container_name:
        return  # Unknown container
    
    # Load legacy solutions for this container
    legacy_solutions = _load_legacy_solutions(container_name)
    
    if not legacy_solutions:
        return  # No legacy solutions available
    
    # Filter and convert solutions
    valid_solutions = []
    for legacy_sol in legacy_solutions:
        if _solution_respects_inventory(legacy_sol, inventory):
            converted = _convert_legacy_to_covered_cells(legacy_sol)
            if converted:
                valid_solutions.append(converted)
    
    # Shuffle for seed-based determinism, then yield up to max_results
    random.shuffle(valid_solutions)
    
    count = 0
    for solution in valid_solutions:
        if count >= max_results:
            break
        yield solution
        count += 1

def _identify_container(container_cells: set) -> Optional[str]:
    """Identify container name by matching cell coordinates."""
    # Map known containers by their coordinate sets
    known_containers = {
        "Shape_2": 100,  # Shape_2 has 100 cells
        "Shape_3": 100,  # Shape_3 has 100 cells  
        # Add more as needed
    }
    
    cell_count = len(container_cells)
    
    # For now, assume Shape_3 if we have 100 cells
    # In a full implementation, you'd load and compare actual container files
    if cell_count == 100:
        return "Shape_3"
    elif cell_count == 100:  # Could be Shape_2 as well
        return "Shape_2"
    
    return None

def _load_legacy_solutions(container_name: str) -> List[Dict[str, Any]]:
    """Load all legacy solution files for the given container."""
    legacy_dir = Path("C:/Ball Puzzle/legacy results")
    pattern = f"{container_name}.result*.world.json"
    
    solutions = []
    for file_path in legacy_dir.glob(pattern):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                solution = json.load(f)
                solutions.append(solution)
        except Exception:
            continue  # Skip invalid files
    
    return solutions

def _solution_respects_inventory(legacy_sol: Dict[str, Any], inventory: Dict[str, int]) -> bool:
    """Check if legacy solution respects the given inventory constraints."""
    if not inventory:
        return True  # No constraints
    
    pieces_used = {}
    for piece in legacy_sol.get("pieces", []):
        piece_id = piece.get("id", "")
        pieces_used[piece_id] = pieces_used.get(piece_id, 0) + 1
    
    # Check if solution uses more pieces than available in inventory
    for piece_id, count in pieces_used.items():
        if count > inventory.get(piece_id, 0):
            return False
    
    return True

def _convert_legacy_to_covered_cells(legacy_sol: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert legacy solution format to covered-cells format."""
    pieces = legacy_sol.get("pieces", [])
    if not pieces:
        return None
    
    covered_by_piece = []
    for piece in pieces:
        piece_id = piece.get("id", "")
        cells_ijk = piece.get("cells_ijk", [])
        
        if piece_id and cells_ijk:
            covered_by_piece.append({
                "piece": piece_id,
                "covered": [[int(c[0]), int(c[1]), int(c[2])] for c in cells_ijk]
            })
    
    return {"covered_by_piece": covered_by_piece}
