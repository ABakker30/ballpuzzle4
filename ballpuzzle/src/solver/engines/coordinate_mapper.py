"""Coordinate mapping system for DLX engine optimization."""

from typing import Dict, List, Tuple, Set
from collections import defaultdict

I3 = Tuple[int, int, int]

class CoordinateMapper:
    """Maps FCC coordinates and piece placements to integer indices for fast lookups."""
    
    def __init__(self):
        # Coordinate mappings
        self.coord_to_int: Dict[I3, int] = {}
        self.int_to_coord: Dict[int, I3] = {}
        self.next_coord_id = 0
        
        # Row (placement) mappings
        self.row_to_int: Dict[str, int] = {}
        self.int_to_row: Dict[int, str] = {}
        self.next_row_id = 0
        
        # Reverse lookup for debugging
        self.int_to_placement_info: Dict[int, Dict] = {}
    
    def map_coordinate(self, coord: I3) -> int:
        """Map a coordinate to an integer ID."""
        if coord not in self.coord_to_int:
            coord_id = self.next_coord_id
            self.coord_to_int[coord] = coord_id
            self.int_to_coord[coord_id] = coord
            self.next_coord_id += 1
        return self.coord_to_int[coord]
    
    def map_coordinates(self, coords: List[I3]) -> List[int]:
        """Map a list of coordinates to integer IDs."""
        return [self.map_coordinate(coord) for coord in coords]
    
    def get_coordinate(self, coord_id: int) -> I3:
        """Get coordinate from integer ID."""
        return self.int_to_coord[coord_id]
    
    def map_row(self, row_key: str, piece_id: str = None, orientation_idx: int = None, 
                position: I3 = None, coordinates: List[I3] = None) -> int:
        """Map a row identifier to an integer ID with metadata."""
        if row_key not in self.row_to_int:
            row_id = self.next_row_id
            self.row_to_int[row_key] = row_id
            self.int_to_row[row_id] = row_key
            
            # Store placement info for debugging
            self.int_to_placement_info[row_id] = {
                "piece_id": piece_id,
                "orientation_idx": orientation_idx,
                "position": position,
                "coordinates": coordinates,
                "row_key": row_key
            }
            
            self.next_row_id += 1
        return self.row_to_int[row_key]
    
    def get_row_key(self, row_id: int) -> str:
        """Get row key from integer ID."""
        return self.int_to_row[row_id]
    
    def get_placement_info(self, row_id: int) -> Dict:
        """Get placement metadata from row ID."""
        return self.int_to_placement_info.get(row_id, {})
    
    def get_stats(self) -> Dict:
        """Get mapping statistics."""
        return {
            "coordinates_mapped": len(self.coord_to_int),
            "rows_mapped": len(self.row_to_int),
            "memory_saved_estimate": (len(self.coord_to_int) * 20 + len(self.row_to_int) * 50)  # Rough estimate
        }
