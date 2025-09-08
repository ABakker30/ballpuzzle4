"""Precomputation of piece orientations and placement candidates."""

from typing import List, Dict, Tuple, Set
from .lattice_fcc import Int3, fcc_rotations, apply_rot
from .bitset import bitset_from_indices, all_bits_mask

try:
    from ....pieces.sphere_orientations import get_piece_orientations
except ImportError:
    def get_piece_orientations(piece_id: str):
        return [[[0, 0, 0]]]  # Fallback


def get_static_orientations(piece_id: str) -> List[List[Int3]]:
    """
    Get static orientations for a piece from 4-sphere data.
    
    Args:
        piece_id: Piece identifier (A-Y)
        
    Returns:
        List of pre-computed oriented piece shapes (relative coordinates)
    """
    try:
        orientations = get_piece_orientations(piece_id)
        return [[(x, y, z) for x, y, z in orientation] for orientation in orientations]
    except KeyError:
        # Fallback for pieces not in data
        return [[(0, 0, 0)]]  # Single orientation at origin


def build_placement_data(container_cells: List[Int3], 
                        pieces_data: Dict[str, List[Int3]]) -> Tuple[
    List[int],  # candidates (bitsets)
    List[List[int]],  # covers_by_cell
    List[Tuple[str, int, int]],  # candidate_meta
    int,  # all_mask
    Dict[Int3, int],  # index_of_cell
    List[Int3],  # cells_by_index
    List[int]  # piece_cell_counts
]:
    """
    Build all placement data structures for efficient solving.
    
    Args:
        container_cells: List of container cell coordinates
        pieces_data: Dict mapping piece_id to list of cell coordinates
        
    Returns:
        Tuple of precomputed data structures
    """
    # Build dense cell indexing
    cells_by_index = list(container_cells)
    index_of_cell = {cell: i for i, cell in enumerate(cells_by_index)}
    num_cells = len(container_cells)
    
    # Initialize data structures
    candidates = []  # List of bitsets
    covers_by_cell = [[] for _ in range(num_cells)]
    candidate_meta = []  # (piece_id, orient_idx, anchor_cell_idx)
    piece_cell_counts = []
    
    candidate_idx = 0
    
    # Process each piece
    for piece_id, piece_cells in pieces_data.items():
        piece_cell_counts.append(len(piece_cells))
        
        # Get static orientations from legacy data
        orientations = get_static_orientations(piece_id)
        
        # For each orientation
        for orient_idx, oriented_cells in enumerate(orientations):
            
            # Try placing at each container cell as anchor
            for anchor_idx, anchor_cell in enumerate(cells_by_index):
                
                # Translate oriented piece to this anchor position
                if not oriented_cells:
                    continue
                    
                # Try placing piece with each of its cells at the anchor position
                for ref_idx, ref_cell in enumerate(oriented_cells):
                    translation = (
                        anchor_cell[0] - ref_cell[0],
                        anchor_cell[1] - ref_cell[1], 
                        anchor_cell[2] - ref_cell[2]
                    )
                    
                    # Translate all piece cells
                    placed_cells = []
                    valid_placement = True
                    
                    for px, py, pz in oriented_cells:
                        placed_cell = (
                            px + translation[0],
                            py + translation[1],
                            pz + translation[2]
                        )
                        
                        # Check if placed cell is in container
                        if placed_cell not in index_of_cell:
                            valid_placement = False
                            break
                        
                        placed_cells.append(placed_cell)
                    
                    if not valid_placement:
                        continue
                    
                    # Convert to bitset
                    cell_indices = [index_of_cell[cell] for cell in placed_cells]
                    candidate_bitset = bitset_from_indices(cell_indices, num_cells)
                    
                    # Store candidate
                    candidates.append(candidate_bitset)
                    candidate_meta.append((piece_id, orient_idx, anchor_idx))
                    
                    # Update covers_by_cell
                    for cell_idx in cell_indices:
                        covers_by_cell[cell_idx].append(candidate_idx)
                    
                    candidate_idx += 1
    
    # Create all_mask (all container cells set)
    all_mask = all_bits_mask(num_cells)
    
    return (candidates, covers_by_cell, candidate_meta, all_mask, 
            index_of_cell, cells_by_index, piece_cell_counts)


def validate_container_piece_fit(container_cells: List[Int3], 
                               pieces_data: Dict[str, List[Int3]],
                               inventory: Dict[str, int]) -> bool:
    """
    Validate that pieces can theoretically fit in container.
    
    Args:
        container_cells: Container cell coordinates
        pieces_data: Piece definitions
        inventory: Piece counts
        
    Returns:
        True if total piece cells equals container cells
    """
    container_size = len(container_cells)
    
    total_piece_cells = 0
    for piece_id, count in inventory.items():
        if piece_id in pieces_data:
            piece_size = len(pieces_data[piece_id])
            total_piece_cells += piece_size * count
    
    return total_piece_cells == container_size
