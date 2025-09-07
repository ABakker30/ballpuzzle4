"""Utility functions for solver operations."""

from typing import Tuple, List, Optional, Dict

I3 = Tuple[int, int, int]

def first_empty_cell(occ, cells_sorted: List[I3]) -> Optional[I3]:
    """Find the first empty cell in sorted order.
    
    Args:
        occ: OccMask object with mask and order attributes
        cells_sorted: List of cells in sorted order
        
    Returns:
        First empty cell, or None if all occupied
    """
    for cell in cells_sorted:
        if cell in occ.order:
            cell_idx = occ.order[cell]
            if ((occ.mask >> cell_idx) & 1) == 0:
                return cell
    return None

def index_map(cells_sorted: List[I3]) -> Dict[I3, int]:
    """Create mapping from cell coordinates to bit indices.
    
    Args:
        cells_sorted: List of cells in sorted order
        
    Returns:
        Dictionary mapping cell to its bit index
    """
    return {cell: i for i, cell in enumerate(cells_sorted)}
