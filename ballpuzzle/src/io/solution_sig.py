"""Canonical solution signature for deduplication under container symmetry."""

import hashlib
from typing import Set, List, Tuple
from ..coords.symmetry_fcc import canonical_atom_tuple

I3 = Tuple[int, int, int]

def canonical_state_signature(cells: Set[I3], symGroup: List[Tuple[Tuple[I3,I3,I3], ...]]) -> str:
    """
    Compute canonical signature for a final occupied state under container symmetry.
    
    Args:
        cells: Set of occupied FCC lattice coordinates
        symGroup: Container symmetry group (list of rotation matrices)
        
    Returns:
        Canonical state signature as SHA256 hex string
    """
    # Get canonical representation of the occupied atom set
    canonical_atoms = canonical_atom_tuple(cells)
    
    # Convert to string representation for hashing
    canonical_str = str(canonical_atoms)
    
    # Compute SHA256 hash
    hash_obj = hashlib.sha256(canonical_str.encode('utf-8'))
    return hash_obj.hexdigest()

def extract_occupied_cells_from_placements(placements: List[dict]) -> Set[I3]:
    """
    Extract all occupied FCC coordinates from placement data.
    
    Args:
        placements: List of placement dictionaries with 'coordinates' field
        
    Returns:
        Set of all occupied FCC lattice coordinates
    """
    occupied = set()
    for placement in placements:
        coords = placement.get('coordinates', [])
        for coord in coords:
            occupied.add(tuple(map(int, coord)))
    return occupied
