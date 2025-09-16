#!/usr/bin/env python3
"""Compare container coordinates with solution coordinates to identify mismatch."""

import json

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def extract_solution_coordinates(solution):
    """Extract all coordinates from solution placements."""
    all_coords = []
    for placement in solution.get("placements", []):
        coords = placement.get("coordinates", [])
        for coord in coords:
            all_coords.append(tuple(coord))
    return set(all_coords)

def main():
    # Load container
    container = load_json("data/containers/v1/16 cell container.fcc.json")
    container_cells = set(tuple(cell) for cell in container["cells"])
    
    # Load solution
    solution = load_json("solutions/16_cell_container.fcc_solution.json")
    solution_coords = extract_solution_coordinates(solution)
    
    print("=== COORDINATE COMPARISON ===")
    print(f"Container cells ({len(container_cells)}):")
    for cell in sorted(container_cells):
        print(f"  {cell}")
    
    print(f"\nSolution coordinates ({len(solution_coords)}):")
    for coord in sorted(solution_coords):
        print(f"  {coord}")
    
    print(f"\n=== ANALYSIS ===")
    print(f"Container cells: {len(container_cells)}")
    print(f"Solution coords: {len(solution_coords)}")
    
    # Check overlap
    overlap = container_cells & solution_coords
    print(f"Overlapping coords: {len(overlap)}")
    for coord in sorted(overlap):
        print(f"  OK {coord}")
    
    # Check missing from solution
    missing_from_solution = container_cells - solution_coords
    if missing_from_solution:
        print(f"\nMissing from solution ({len(missing_from_solution)}):")
        for coord in sorted(missing_from_solution):
            print(f"  MISS {coord}")
    
    # Check extra in solution
    extra_in_solution = solution_coords - container_cells
    if extra_in_solution:
        print(f"\nExtra in solution ({len(extra_in_solution)}):")
        for coord in sorted(extra_in_solution):
            print(f"  EXTRA {coord}")
    
    # Final verdict
    if container_cells == solution_coords:
        print(f"\nMATCH: Solution coordinates exactly match container cells")
    else:
        print(f"\nMISMATCH: Solution coordinates do not match container cells")

if __name__ == "__main__":
    main()
