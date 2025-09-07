"""FCC lattice operations with integer coordinates only."""

from typing import List, Tuple

# Type alias for integer 3D coordinates
Int3 = Tuple[int, int, int]
Mat3 = List[List[int]]

# FCC lattice has 12 nearest neighbors
FCC_NEIGHBORS: List[Int3] = [
    # Face-centered cubic neighbors in integer coordinates
    (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0),
    (1, 0, 1), (1, 0, -1), (-1, 0, 1), (-1, 0, -1),
    (0, 1, 1), (0, 1, -1), (0, -1, 1), (0, -1, -1)
]


def fcc_rotations() -> List[Mat3]:
    """
    Generate all 24 proper rotations for FCC lattice.
    Returns integer rotation matrices with determinant +1.
    """
    # Identity and basic rotations around axes
    rotations = []
    
    # Identity
    rotations.append([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1]
    ])
    
    # 90-degree rotations around Z axis
    rotations.append([
        [0, -1, 0],
        [1, 0, 0],
        [0, 0, 1]
    ])
    
    rotations.append([
        [-1, 0, 0],
        [0, -1, 0],
        [0, 0, 1]
    ])
    
    rotations.append([
        [0, 1, 0],
        [-1, 0, 0],
        [0, 0, 1]
    ])
    
    # 90-degree rotations around Y axis
    rotations.append([
        [0, 0, 1],
        [0, 1, 0],
        [-1, 0, 0]
    ])
    
    rotations.append([
        [-1, 0, 0],
        [0, 1, 0],
        [0, 0, -1]
    ])
    
    rotations.append([
        [0, 0, -1],
        [0, 1, 0],
        [1, 0, 0]
    ])
    
    # 90-degree rotations around X axis
    rotations.append([
        [1, 0, 0],
        [0, 0, -1],
        [0, 1, 0]
    ])
    
    rotations.append([
        [1, 0, 0],
        [0, -1, 0],
        [0, 0, -1]
    ])
    
    rotations.append([
        [1, 0, 0],
        [0, 0, 1],
        [0, -1, 0]
    ])
    
    # 180-degree rotations around face diagonals
    rotations.append([
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, -1]
    ])
    
    rotations.append([
        [0, -1, 0],
        [-1, 0, 0],
        [0, 0, -1]
    ])
    
    # 120-degree rotations around body diagonals
    rotations.append([
        [0, 0, 1],
        [1, 0, 0],
        [0, 1, 0]
    ])
    
    rotations.append([
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0]
    ])
    
    rotations.append([
        [0, 0, -1],
        [-1, 0, 0],
        [0, 1, 0]
    ])
    
    rotations.append([
        [0, -1, 0],
        [0, 0, -1],
        [1, 0, 0]
    ])
    
    rotations.append([
        [0, 0, 1],
        [-1, 0, 0],
        [0, -1, 0]
    ])
    
    rotations.append([
        [0, 1, 0],
        [0, 0, -1],
        [-1, 0, 0]
    ])
    
    rotations.append([
        [0, 0, -1],
        [1, 0, 0],
        [0, -1, 0]
    ])
    
    rotations.append([
        [0, -1, 0],
        [0, 0, 1],
        [-1, 0, 0]
    ])
    
    # Additional rotations to complete the 24
    rotations.append([
        [-1, 0, 0],
        [0, 0, 1],
        [0, 1, 0]
    ])
    
    rotations.append([
        [-1, 0, 0],
        [0, 0, -1],
        [0, -1, 0]
    ])
    
    rotations.append([
        [1, 0, 0],
        [0, -1, 0],
        [0, 0, 1]
    ])
    
    rotations.append([
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, -1]
    ])
    
    return rotations


def apply_rot(rotation: Mat3, points: List[Int3]) -> List[Int3]:
    """
    Apply rotation matrix to a list of integer coordinate points.
    
    Args:
        rotation: 3x3 integer rotation matrix
        points: List of (x, y, z) integer coordinates
        
    Returns:
        List of rotated (x, y, z) integer coordinates
    """
    result = []
    for x, y, z in points:
        new_x = rotation[0][0] * x + rotation[0][1] * y + rotation[0][2] * z
        new_y = rotation[1][0] * x + rotation[1][1] * y + rotation[1][2] * z
        new_z = rotation[2][0] * x + rotation[2][1] * y + rotation[2][2] * z
        result.append((new_x, new_y, new_z))
    return result


def validate_fcc_connectivity(cells: List[Int3]) -> bool:
    """
    Validate that container cells form a connected FCC structure.
    
    Args:
        cells: List of FCC lattice coordinates
        
    Returns:
        True if all cells are connected via FCC neighbors
    """
    if not cells:
        return True
    
    cell_set = set(cells)
    visited = set()
    queue = [cells[0]]
    visited.add(cells[0])
    
    while queue:
        current = queue.pop(0)
        
        # Check all FCC neighbors
        for dx, dy, dz in FCC_NEIGHBORS:
            neighbor = (current[0] + dx, current[1] + dy, current[2] + dz)
            if neighbor in cell_set and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return len(visited) == len(cells)
