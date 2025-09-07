"""Face-centered cubic (FCC) lattice coordinate system implementation."""

from typing import List, Tuple, Set
import numpy as np


class FCCLattice:
    """Face-centered cubic lattice coordinate system.
    
    Provides methods for working with FCC lattice coordinates,
    including neighbor calculations, distance metrics, and
    coordinate transformations.
    """
    
    def __init__(self, scale: float = 1.0):
        """Initialize FCC lattice with given scale factor.
        
        Args:
            scale: Scaling factor for lattice spacing
        """
        self.scale = scale
        self._basis_vectors = np.array([
            [0.5, 0.5, 0.0],
            [0.5, 0.0, 0.5],
            [0.0, 0.5, 0.5]
        ]) * scale
    
    def to_cartesian(self, fcc_coord: Tuple[int, int, int]) -> np.ndarray:
        """Convert FCC coordinates to Cartesian coordinates.
        
        Args:
            fcc_coord: FCC lattice coordinates (a, b, c)
            
        Returns:
            Cartesian coordinates as numpy array
        """
        a, b, c = fcc_coord
        return a * self._basis_vectors[0] + b * self._basis_vectors[1] + c * self._basis_vectors[2]
    
    def get_neighbors(self, coord: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
        """Get all nearest neighbors in FCC lattice.
        
        Args:
            coord: FCC coordinate
            
        Returns:
            List of neighboring FCC coordinates
        """
        a, b, c = coord
        neighbors = [
            (a + 1, b, c), (a - 1, b, c),
            (a, b + 1, c), (a, b - 1, c),
            (a, b, c + 1), (a, b, c - 1),
            (a + 1, b + 1, c), (a + 1, b - 1, c),
            (a - 1, b + 1, c), (a - 1, b - 1, c),
            (a + 1, b, c + 1), (a + 1, b, c - 1),
            (a - 1, b, c + 1), (a - 1, b, c - 1),
            (a, b + 1, c + 1), (a, b + 1, c - 1),
            (a, b - 1, c + 1), (a, b - 1, c - 1)
        ]
        return neighbors
    
    def distance(self, coord1: Tuple[int, int, int], coord2: Tuple[int, int, int]) -> float:
        """Calculate Euclidean distance between two FCC coordinates.
        
        Args:
            coord1: First FCC coordinate
            coord2: Second FCC coordinate
            
        Returns:
            Euclidean distance
        """
        cart1 = self.to_cartesian(coord1)
        cart2 = self.to_cartesian(coord2)
        return np.linalg.norm(cart1 - cart2)
    
    def is_valid_coord(self, coord: Tuple[int, int, int]) -> bool:
        """Check if coordinate is valid in FCC lattice.
        
        Args:
            coord: FCC coordinate to validate
            
        Returns:
            True if coordinate is valid
        """
        # In FCC, all integer coordinates are valid
        return all(isinstance(x, int) for x in coord)
    
    def get_bounding_box(self, coords: Set[Tuple[int, int, int]]) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """Get bounding box for a set of coordinates.
        
        Args:
            coords: Set of FCC coordinates
            
        Returns:
            Tuple of (min_coord, max_coord)
        """
        if not coords:
            return ((0, 0, 0), (0, 0, 0))
        
        coords_array = np.array(list(coords))
        min_coord = tuple(coords_array.min(axis=0))
        max_coord = tuple(coords_array.max(axis=0))
        
        return (min_coord, max_coord)
