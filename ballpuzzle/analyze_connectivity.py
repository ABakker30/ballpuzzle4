#!/usr/bin/env python3
"""
Analyze piece connectivity in solution files to detect disconnected cells.
"""

import json
import sys
from typing import List, Tuple, Set

def get_fcc_neighbors(cell: Tuple[int, int, int]) -> List[Tuple[int, int, int]]:
    """Get FCC neighbors for a cell."""
    i, j, k = cell
    neighbors = []
    
    # FCC lattice neighbors (12 neighbors)
    deltas = [
        (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
        (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0),
        (1, 0, 1), (1, 0, -1), (-1, 0, 1), (-1, 0, -1),
        (0, 1, 1), (0, 1, -1), (0, -1, 1), (0, -1, -1)
    ]
    
    for di, dj, dk in deltas:
        neighbors.append((i + di, j + dj, k + dk))
    
    return neighbors

def is_connected(cells: List[Tuple[int, int, int]]) -> bool:
    """Check if a set of cells forms a connected component."""
    if len(cells) <= 1:
        return True
    
    cell_set = set(cells)
    visited = set()
    queue = [cells[0]]
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        
        # Check all neighbors
        for neighbor in get_fcc_neighbors(current):
            if neighbor in cell_set and neighbor not in visited:
                queue.append(neighbor)
    
    return len(visited) == len(cells)

def analyze_solution(solution_data: dict) -> dict:
    """Analyze a solution for piece connectivity issues."""
    results = {
        'total_pieces': len(solution_data['placements']),
        'disconnected_pieces': [],
        'piece_analysis': []
    }
    
    for i, placement in enumerate(solution_data['placements']):
        piece_type = placement['piece']
        cells = [tuple(cell) for cell in placement['cells_ijk']]
        
        analysis = {
            'index': i,
            'piece': piece_type,
            'orientation': placement['ori'],
            'cell_count': len(cells),
            'cells': cells,
            'is_connected': is_connected(cells)
        }
        
        results['piece_analysis'].append(analysis)
        
        if not analysis['is_connected']:
            results['disconnected_pieces'].append(analysis)
    
    return results

def main():
    # Read the last few solution events from events.jsonl
    solutions = []
    
    try:
        with open('events.jsonl', 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event.get('type') == 'solution':
                        solutions.append(event['solution'])
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print("events.jsonl not found")
        return
    
    # Analyze the last 3 solutions
    recent_solutions = solutions[-3:] if len(solutions) >= 3 else solutions
    
    print(f"Analyzing {len(recent_solutions)} recent solutions...")
    print("=" * 60)
    
    for i, solution in enumerate(recent_solutions):
        print(f"\nSOLUTION {i+1}:")
        print(f"Container: {solution['containerCidSha256'][:16]}...")
        print(f"Pieces used: {solution['piecesUsed']}")
        
        analysis = analyze_solution(solution)
        
        print(f"Total pieces: {analysis['total_pieces']}")
        print(f"Disconnected pieces: {len(analysis['disconnected_pieces'])}")
        
        if analysis['disconnected_pieces']:
            print("\nDISCONNECTED PIECES FOUND:")
            for piece in analysis['disconnected_pieces']:
                print(f"  - Piece {piece['index']}: {piece['piece']} (ori {piece['orientation']})")
                print(f"    Cells: {piece['cells']}")
        
        # Check for pieces with wrong cell count
        wrong_count = [p for p in analysis['piece_analysis'] if p['cell_count'] != 4]
        if wrong_count:
            print(f"\nPIECES WITH WRONG CELL COUNT:")
            for piece in wrong_count:
                print(f"  - Piece {piece['index']}: {piece['piece']} has {piece['cell_count']} cells (should be 4)")
        
        print("-" * 40)

if __name__ == "__main__":
    main()
