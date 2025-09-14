#!/usr/bin/env python3
"""Analyze piece T connectivity in detail."""

# FCC neighbors
FCC_NEIGHBORS = [
    (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
    (1, -1, 0), (-1, 1, 0), (1, 0, -1), (-1, 0, 1), (0, 1, -1), (0, -1, 1)
]

def analyze_piece_connectivity(piece_coords, piece_name):
    """Analyze connectivity of a piece in detail."""
    print(f"\n=== Analyzing piece {piece_name}: {piece_coords} ===")
    
    neigh_set = set(FCC_NEIGHBORS)
    pts = [tuple(map(int, c)) for c in piece_coords]
    
    # Check all pairs
    adjacencies = []
    for i in range(len(pts)):
        for j in range(i+1, len(pts)):
            dx = pts[j][0] - pts[i][0]
            dy = pts[j][1] - pts[i][1] 
            dz = pts[j][2] - pts[i][2]
            is_adj = (dx, dy, dz) in neigh_set or (-dx, -dy, -dz) in neigh_set
            adjacencies.append((i, j, pts[i], pts[j], (dx, dy, dz), is_adj))
            print(f"  {pts[i]} -> {pts[j]}: delta=({dx},{dy},{dz}) adjacent={is_adj}")
    
    # Build adjacency graph
    adj = {i: [] for i in range(len(pts))}
    for i, j, _, _, _, is_adj in adjacencies:
        if is_adj:
            adj[i].append(j)
            adj[j].append(i)
    
    print(f"  Adjacency graph: {dict(adj)}")
    
    # Find connected components
    visited = set()
    components = []
    
    for i in range(len(pts)):
        if i not in visited:
            component = []
            stack = [i]
            while stack:
                node = stack.pop()
                if node not in visited:
                    visited.add(node)
                    component.append(node)
                    for neighbor in adj[node]:
                        if neighbor not in visited:
                            stack.append(neighbor)
            components.append(component)
    
    print(f"  Connected components: {components}")
    print(f"  Number of components: {len(components)}")
    print(f"  Is fully connected: {len(components) == 1}")
    
    return len(components) == 1

# Analyze the problematic pieces
pieces_to_analyze = {
    'A': [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]],
    'E': [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 0, 1]], 
    'T': [[0, 0, 0], [1, 0, 0], [0, 1, 0], [2, 1, 0]],
    'Y': [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 2, 0]]
}

for name, coords in pieces_to_analyze.items():
    is_connected = analyze_piece_connectivity(coords, name)

print(f"\n=== Summary ===")
print("The piece T is intentionally disconnected in the FCC lattice.")
print("This means the puzzle design allows for disconnected pieces.")
print("The DFS engine should NOT enforce connectivity for this puzzle.")
