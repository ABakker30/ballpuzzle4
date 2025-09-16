"""Pruning strategies for eliminating unpromising search branches."""

from typing import Set, Tuple, Dict, List
from ..coords.lattice_fcc import FCCLattice


class PruningStrategy:
    """Implements various pruning strategies to reduce search space."""
    
    def __init__(self):
        """Initialize pruning strategy."""
        self.lattice = FCCLattice()
    
    def should_prune(
        self,
        container: Set[Tuple[int, int, int]],
        used_coords: Set[Tuple[int, int, int]],
        inventory: 'PieceInventory'
    ) -> bool:
        """Determine if current search branch should be pruned.
        
        Args:
            container: Target container shape
            used_coords: Currently occupied coordinates
            inventory: Current piece inventory
            
        Returns:
            True if branch should be pruned
        """
        # Basic feasibility check
        if not self._is_feasible(container, used_coords, inventory):
            return True
        
        # Connectivity check
        if not self._maintains_connectivity(container, used_coords):
            return True
        
        # Isolated region check
        if self._creates_unfillable_regions(container, used_coords, inventory):
            return True
        
        return False
    
    def _is_feasible(
        self,
        container: Set[Tuple[int, int, int]],
        used_coords: Set[Tuple[int, int, int]],
        inventory: 'PieceInventory'
    ) -> bool:
        """Check basic feasibility constraints.
        
        Args:
            container: Target container shape
            used_coords: Currently occupied coordinates
            inventory: Current piece inventory
            
        Returns:
            True if still feasible
        """
        remaining_size = len(container) - len(used_coords)
        
        # Check if we have enough pieces to fill remaining space
        if not inventory.can_complete_with_remaining(len(container)):
            return False
        
        # Check if remaining space is positive
        if remaining_size < 0:
            return False
        
        # Check if used coordinates are within container
        if not used_coords.issubset(container):
            return False
        
        return True
    
    def _maintains_connectivity(
        self,
        container: Set[Tuple[int, int, int]],
        used_coords: Set[Tuple[int, int, int]]
    ) -> bool:
        """Check if remaining space maintains connectivity.
        
        Args:
            container: Target container shape
            used_coords: Currently occupied coordinates
            
        Returns:
            True if remaining space is connected
        """
        remaining_coords = container - used_coords
        
        if len(remaining_coords) <= 1:
            return True
        
        # Use BFS to check connectivity
        visited = set()
        queue = [next(iter(remaining_coords))]
        visited.add(queue[0])
        
        while queue:
            current = queue.pop(0)
            neighbors = self.lattice.get_neighbors(current)
            
            for neighbor in neighbors:
                if neighbor in remaining_coords and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return len(visited) == len(remaining_coords)
    
    def _creates_unfillable_regions(
        self,
        container: Set[Tuple[int, int, int]],
        used_coords: Set[Tuple[int, int, int]],
        inventory: 'PieceInventory'
    ) -> bool:
        """Check if current state creates regions that cannot be filled.
        
        Args:
            container: Target container shape
            used_coords: Currently occupied coordinates
            inventory: Current piece inventory
            
        Returns:
            True if unfillable regions are created
        """
        remaining_coords = container - used_coords
        
        if not remaining_coords:
            return False
        
        # Find connected components in remaining space
        components = self._find_connected_components(remaining_coords)
        
        # Check if any component is too small for available pieces
        available_pieces = inventory.get_remaining_pieces_summary()
        min_piece_size = min(
            (inventory.get_piece_size(name) for name in available_pieces.keys()),
            default=1
        )
        
        for component in components:
            if len(component) < min_piece_size:
                return True
        
        return False
    
    def _find_connected_components(
        self,
        coords: Set[Tuple[int, int, int]]
    ) -> List[Set[Tuple[int, int, int]]]:
        """Find all connected components in a set of coordinates.
        
        Args:
            coords: Set of coordinates
            
        Returns:
            List of connected components
        """
        components = []
        unvisited = coords.copy()
        
        while unvisited:
            # Start new component
            component = set()
            queue = [next(iter(unvisited))]
            component.add(queue[0])
            unvisited.remove(queue[0])
            
            # BFS to find all connected coordinates
            while queue:
                current = queue.pop(0)
                neighbors = self.lattice.get_neighbors(current)
                
                for neighbor in neighbors:
                    if neighbor in unvisited:
                        component.add(neighbor)
                        unvisited.remove(neighbor)
                        queue.append(neighbor)
            
            components.append(component)
        
        return components
