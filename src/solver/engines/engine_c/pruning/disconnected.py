"""Disconnected void detection using flood-fill on empty cells."""

from typing import List
from ..lattice_fcc import FCC_NEIGHBORS, Int3
from ..bitset import bitset_to_indices


def is_disconnected(empty_bitset: int, cells_by_index: List[Int3], 
                   index_of_cell: dict) -> bool:
    """
    Check if empty cells form disconnected regions using flood-fill.
    
    Args:
        empty_bitset: Bitset of currently empty cells
        cells_by_index: Mapping from cell index to coordinates
        index_of_cell: Mapping from coordinates to cell index
        
    Returns:
        True if empty cells are disconnected (prunable state)
    """
    if empty_bitset == 0:
        return False  # No empty cells, not disconnected
    
    empty_indices = bitset_to_indices(empty_bitset)
    if len(empty_indices) <= 1:
        return False  # Single empty cell or none, cannot be disconnected
    
    # Start flood-fill from first empty cell
    visited = set()
    queue = [empty_indices[0]]
    visited.add(empty_indices[0])
    
    while queue:
        current_idx = queue.pop(0)
        current_coords = cells_by_index[current_idx]
        
        # Check all FCC neighbors
        for dx, dy, dz in FCC_NEIGHBORS:
            neighbor_coords = (
                current_coords[0] + dx,
                current_coords[1] + dy, 
                current_coords[2] + dz
            )
            
            # If neighbor exists in container and is empty and unvisited
            if neighbor_coords in index_of_cell:
                neighbor_idx = index_of_cell[neighbor_coords]
                if (neighbor_idx in empty_indices and 
                    neighbor_idx not in visited):
                    visited.add(neighbor_idx)
                    queue.append(neighbor_idx)
    
    # If we didn't visit all empty cells, they're disconnected
    return len(visited) < len(empty_indices)


def count_connected_components(empty_bitset: int, cells_by_index: List[Int3],
                             index_of_cell: dict) -> int:
    """
    Count number of connected components in empty cells.
    
    Args:
        empty_bitset: Bitset of currently empty cells
        cells_by_index: Mapping from cell index to coordinates
        index_of_cell: Mapping from coordinates to cell index
        
    Returns:
        Number of connected components
    """
    if empty_bitset == 0:
        return 0
    
    empty_indices = set(bitset_to_indices(empty_bitset))
    visited = set()
    components = 0
    
    for start_idx in empty_indices:
        if start_idx in visited:
            continue
            
        # Start new component
        components += 1
        queue = [start_idx]
        visited.add(start_idx)
        
        while queue:
            current_idx = queue.pop(0)
            current_coords = cells_by_index[current_idx]
            
            # Check all FCC neighbors
            for dx, dy, dz in FCC_NEIGHBORS:
                neighbor_coords = (
                    current_coords[0] + dx,
                    current_coords[1] + dy,
                    current_coords[2] + dz
                )
                
                if neighbor_coords in index_of_cell:
                    neighbor_idx = index_of_cell[neighbor_coords]
                    if (neighbor_idx in empty_indices and 
                        neighbor_idx not in visited):
                        visited.add(neighbor_idx)
                        queue.append(neighbor_idx)
    
    return components
