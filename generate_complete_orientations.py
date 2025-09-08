#!/usr/bin/env python3
"""Generate complete sphere_orientations.py from All 4-Sphere Pieces.txt"""

import re

def main():
    # Read the All 4-Sphere Pieces.txt file
    with open('docs/All 4-Sphere Pieces.txt', 'r') as f:
        content = f.read()

    # Split by class headers
    blocks = re.split(r'Class\s+\d+:', content)[1:]  # Skip first empty split

    pieces = {}

    for block in blocks:
        # Find piece name (A-Y)
        name_match = re.search(r'\b([A-Y])\b', block)
        if not name_match:
            continue
        name = name_match.group(1)
        
        # Find ALL TRUE lines with coordinates
        true_matches = re.findall(r'<([^>]+)>\s+TRUE', block)
        
        orientations = []
        for coord_text in true_matches:
            # Extract coordinates from parentheses
            coord_matches = re.findall(r'\(([^)]+)\)', coord_text)
            
            atoms = []
            for coord_str in coord_matches:
                # Extract numbers from coordinate string
                numbers = re.findall(r'-?\d+', coord_str)
                if len(numbers) >= 3:
                    atoms.append([int(numbers[0]), int(numbers[1]), int(numbers[2])])
            
            # Only keep orientations with exactly 4 atoms (4-sphere pieces)
            if len(atoms) == 4:
                orientations.append(atoms)
        
        if orientations:
            pieces[name] = orientations

    # Generate Python code for sphere_orientations.py
    output = []
    output.append('# Auto-generated from All 4-Sphere Pieces.txt')
    output.append('# Complete static piece orientations - no dynamic generation needed')
    output.append('PIECES = {')

    for name in sorted(pieces.keys()):
        output.append(f'  "{name}": [')
        for orientation in pieces[name]:
            coord_str = ','.join(f'[{c[0]},{c[1]},{c[2]}]' for c in orientation)
            output.append(f'    [{coord_str}],')
        output.append('  ],')

    output.append('}')
    output.append('')
    output.append('def get_piece_orientations(piece_name: str):')
    output.append('    """Get all orientations for a piece."""')
    output.append('    if piece_name not in PIECES:')
    output.append('        raise KeyError(f"Piece \'{piece_name}\' not found")')
    output.append('    return PIECES[piece_name]')
    output.append('')
    output.append('def get_piece_orientation_count(piece_name: str) -> int:')
    output.append('    """Get the number of orientations for a piece."""')
    output.append('    return len(get_piece_orientations(piece_name))')
    output.append('')
    output.append('def get_all_piece_names():')
    output.append('    """Get all available piece names."""')
    output.append('    return list(PIECES.keys())')
    output.append('')

    # Write to sphere_orientations.py
    with open('src/pieces/sphere_orientations.py', 'w') as f:
        f.write('\n'.join(output))

    print(f'Generated complete sphere_orientations.py with {len(pieces)} pieces')
    for name in sorted(pieces.keys()):
        print(f'{name}: {len(pieces[name])} orientations')

if __name__ == "__main__":
    main()
