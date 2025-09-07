"""Canonical coordinate transformations and representations."""

from typing import Tuple, List, Set, Iterable
import numpy as np
import hashlib
from .lattice_fcc import FCCLattice

I3 = Tuple[int,int,int]

def canonicalize(cells: Iterable[I3]) -> List[I3]:
    cells = list(cells)
    if not cells: return []
    minx = min(x for x,_,_ in cells)
    miny = min(y for _,y,_ in cells)
    minz = min(z for *_,z in cells)
    shifted = [(x-minx, y-miny, z-minz) for (x,y,z) in cells]
    return sorted(shifted)  # lexicographic (x,y,z)

def canonical_id_text(cells: Iterable[I3]) -> str:
    """Stable, human-readable canonical ID text: 'x,y,z_x,y,z_...'"""
    canon = canonicalize(cells)
    return "_".join(f"{x},{y},{z}" for (x,y,z) in canon)

def cid_sha256(cells: Iterable[I3]) -> str:
    canon = canonicalize(cells)
    payload = ",".join(f"{x}:{y}:{z}" for x,y,z in canon).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

# --- NEW: rotation-invariant canonicalization ---
def canonicalize_rot(cells: Iterable[I3]) -> List[I3]:
    """Translation + rotation invariant representative using FCC 24-rot canon."""
    from .symmetry_fcc import canonical_atom_tuple
    cells = list(cells)
    if not cells: return []
    # shift-to-origin first (stable) then minimize over rotations
    shifted = canonicalize(cells)             # translation invariance
    canon_rot = canonical_atom_tuple(shifted) # rotation invariance (M4)
    # shift canon_rot to positive so text is stable
    minx = min(x for x,_,_ in canon_rot)
    miny = min(y for _,y,_ in canon_rot)
    minz = min(z for *_,z in canon_rot)
    normalized = [(x-minx, y-miny, z-minz) for (x,y,z) in canon_rot]
    return sorted(normalized)

def canonical_id_text_rot(cells: Iterable[I3]) -> str:
    canon = canonicalize_rot(cells)
    return "_".join(f"{x},{y},{z}" for (x,y,z) in canon)

def cid_sha256_rot(cells: Iterable[I3], lattice: str = "fcc") -> str:
    """Rotation-invariant CID (if tests require). Includes lattice tag to avoid cross-lattice collisions."""
    canon = canonicalize_rot(cells)
    payload = (lattice + "|" + ",".join(f"{x}:{y}:{z}" for x,y,z in canon)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class CanonicalCoordinate:
    """Canonical coordinate representation for symmetry breaking.
    
    Provides methods to convert coordinates to canonical form
    to eliminate symmetric duplicates during solving.
    """
    
    def __init__(self, lattice: FCCLattice):
        """Initialize with FCC lattice reference.
        
        Args:
            lattice: FCC lattice instance
        """
        self.lattice = lattice
    
    def to_canonical(self, coords: Set[Tuple[int, int, int]]) -> Set[Tuple[int, int, int]]:
        """Convert set of coordinates to canonical form.
        
        Args:
            coords: Set of FCC coordinates
            
        Returns:
            Canonicalized coordinate set
        """
        if not coords:
            return set()
        
        # Translate to origin (minimum coordinate becomes (0,0,0))
        coords_list = list(coords)
        min_coord = tuple(np.array(coords_list).min(axis=0))
        translated = {
            (x - min_coord[0], y - min_coord[1], z - min_coord[2])
            for x, y, z in coords
        }
        
        # Apply all 24 rotational symmetries and choose lexicographically smallest
        canonical = self._apply_rotational_symmetries(translated)
        
        return canonical
    
    def _apply_rotational_symmetries(self, coords: Set[Tuple[int, int, int]]) -> Set[Tuple[int, int, int]]:
        """Apply all 24 rotational symmetries and return canonical form.
        
        Args:
            coords: Set of coordinates
            
        Returns:
            Canonical coordinate set
        """
        # Generate all 24 rotation matrices for cubic symmetry
        rotations = self._generate_rotation_matrices()
        
        canonical_candidates = []
        
        for rotation in rotations:
            rotated_coords = set()
            for coord in coords:
                # Apply rotation matrix
                coord_array = np.array(coord)
                rotated = rotation @ coord_array
                # Round to nearest integer (should be exact for proper rotations)
                rotated_int = tuple(np.round(rotated).astype(int))
                rotated_coords.add(rotated_int)
            
            # Translate back to origin
            if rotated_coords:
                min_coord = tuple(np.array(list(rotated_coords)).min(axis=0))
                translated = {
                    (x - min_coord[0], y - min_coord[1], z - min_coord[2])
                    for x, y, z in rotated_coords
                }
                canonical_candidates.append(sorted(translated))
        
        # Return lexicographically smallest
        canonical_list = min(canonical_candidates)
        return set(canonical_list)
    
    def _generate_rotation_matrices(self) -> List[np.ndarray]:
        """Generate all 24 rotation matrices for cubic symmetry.
        
        Returns:
            List of 3x3 rotation matrices
        """
        # Identity and basic rotations
        rotations = []
        
        # Identity
        rotations.append(np.eye(3, dtype=int))
        
        # 90-degree rotations around each axis
        # X-axis rotations
        rotations.append(np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]]))
        rotations.append(np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]]))
        rotations.append(np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]]))
        
        # Y-axis rotations
        rotations.append(np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]))
        rotations.append(np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]]))
        rotations.append(np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]]))
        
        # Z-axis rotations
        rotations.append(np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]]))
        rotations.append(np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]]))
        rotations.append(np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]]))
        
        # Face diagonal rotations (120-degree rotations)
        rotations.append(np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]]))
        rotations.append(np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]]))
        
        # Additional rotations to complete the 24
        rotations.append(np.array([[0, -1, 0], [0, 0, -1], [1, 0, 0]]))
        rotations.append(np.array([[0, 0, -1], [1, 0, 0], [0, -1, 0]]))
        rotations.append(np.array([[0, 1, 0], [0, 0, -1], [-1, 0, 0]]))
        rotations.append(np.array([[0, 0, 1], [-1, 0, 0], [0, -1, 0]]))
        
        # 180-degree rotations around face diagonals
        rotations.append(np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]]))
        rotations.append(np.array([[0, 0, -1], [0, -1, 0], [-1, 0, 0]]))
        rotations.append(np.array([[0, -1, 0], [-1, 0, 0], [0, 0, -1]]))
        
        # More 180-degree rotations
        rotations.append(np.array([[-1, 0, 0], [0, 0, -1], [0, -1, 0]]))
        rotations.append(np.array([[0, 0, 1], [0, -1, 0], [1, 0, 0]]))
        rotations.append(np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]]))
        
        # Final rotations to complete 24
        rotations.append(np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0]]))
        rotations.append(np.array([[0, -1, 0], [0, 0, 1], [-1, 0, 0]]))
        rotations.append(np.array([[0, 1, 0], [0, 0, 1], [1, 0, 0]]))
        rotations.append(np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]]))
        
        return rotations[:24]  # Ensure exactly 24 rotations
    
    def get_canonical_id(self, coords: Set[Tuple[int, int, int]]) -> str:
        """Generate a canonical string ID for a coordinate set.
        
        Args:
            coords: Set of coordinates
            
        Returns:
            Canonical string identifier
        """
        return canonical_id_text_rot(coords)


def cid_sha256(cells: List[Tuple[int, int, int]]) -> str:
    """Compute canonical container ID (SHA256) from cell coordinates.
    
    Args:
        cells: List of FCC lattice coordinates
        
    Returns:
        SHA256 hash of canonical coordinate representation
    """
    # Sort coordinates for canonical representation
    sorted_cells = sorted(cells)
    # Create string representation
    coord_str = ",".join(f"{x},{y},{z}" for x, y, z in sorted_cells)
    # Compute SHA256 hash
    return hashlib.sha256(coord_str.encode('utf-8')).hexdigest()
