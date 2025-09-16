#!/usr/bin/env python3
"""
Analyze the legacy piece orientation data and compare with our FCC analysis.
"""

# Complete legacy piece data from the user
LEGACY_PIECES = {
  "A": [
    [
      [
        0,
        0,
        0
      ],
      [
        1,
        0,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        1,
        -1,
        1
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        1,
        0
      ],
      [
        0,
        0,
        1
      ],
      [
        -1,
        1,
        1
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        1,
        0
      ],
      [
        -1,
        0,
        1
      ],
      [
        -1,
        1,
        1
      ]
    ]
  ],
  "B": [
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        1,
        0
      ],
      [
        -2,
        1,
        0
      ],
      [
        -1,
        2,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        1,
        0
      ],
      [
        1,
        1,
        0
      ],
      [
        -1,
        2,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        0,
        -2,
        1
      ],
      [
        0,
        -1,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        1,
        -2,
        1
      ],
      [
        -1,
        -1,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        0,
        1
      ],
      [
        -2,
        0,
        1
      ],
      [
        -1,
        0,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        0,
        1
      ],
      [
        -2,
        1,
        1
      ],
      [
        -1,
        -1,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        0,
        1
      ],
      [
        1,
        0,
        1
      ],
      [
        -1,
        0,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        0,
        1
      ],
      [
        0,
        1,
        1
      ],
      [
        0,
        -1,
        2
      ]
    ]
  ],
  "C": [
    [
      [
        0,
        0,
        0
      ],
      [
        1,
        0,
        0
      ],
      [
        -1,
        1,
        0
      ],
      [
        -2,
        1,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        1,
        0,
        0
      ],
      [
        -1,
        0,
        1
      ],
      [
        -2,
        0,
        1
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        1,
        0,
        0
      ],
      [
        1,
        1,
        0
      ],
      [
        2,
        1,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        1,
        0,
        0
      ],
      [
        1,
        0,
        1
      ],
      [
        2,
        0,
        1
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        1,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        1,
        -2,
        1
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        1,
        0
      ],
      [
        -2,
        1,
        0
      ],
      [
        -3,
        2,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        1,
        0
      ],
      [
        -1,
        2,
        0
      ],
      [
        -2,
        3,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        1,
        0
      ],
      [
        -2,
        1,
        1
      ],
      [
        -3,
        2,
        1
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        1,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        0,
        -2,
        1
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        1,
        0
      ],
      [
        1,
        1,
        0
      ],
      [
        1,
        2,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        1,
        0
      ],
      [
        -1,
        2,
        0
      ],
      [
        -1,
        3,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        1,
        0
      ],
      [
        0,
        1,
        1
      ],
      [
        0,
        2,
        1
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        0,
        -2,
        1
      ],
      [
        0,
        -3,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        1,
        -2,
        1
      ],
      [
        1,
        -3,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        -1,
        -1,
        2
      ],
      [
        -1,
        -2,
        3
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        0,
        -1,
        2
      ],
      [
        0,
        -2,
        3
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        0,
        1
      ],
      [
        -2,
        0,
        1
      ],
      [
        -3,
        0,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        0,
        1
      ],
      [
        -2,
        1,
        1
      ],
      [
        -3,
        1,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        0,
        1
      ],
      [
        -1,
        -1,
        2
      ],
      [
        -2,
        -1,
        3
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        0,
        1
      ],
      [
        -1,
        0,
        2
      ],
      [
        -2,
        0,
        3
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        0,
        1
      ],
      [
        1,
        0,
        1
      ],
      [
        1,
        0,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        0,
        1
      ],
      [
        0,
        1,
        1
      ],
      [
        0,
        1,
        2
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        0,
        1
      ],
      [
        0,
        -1,
        2
      ],
      [
        0,
        -1,
        3
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        0,
        1
      ],
      [
        -1,
        0,
        2
      ],
      [
        -1,
        0,
        3
      ]
    ]
  ],
  "D": [
    [
      [
        0,
        0,
        0
      ],
      [
        1,
        0,
        0
      ],
      [
        2,
        0,
        0
      ],
      [
        3,
        0,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        1,
        0
      ],
      [
        -2,
        2,
        0
      ],
      [
        -3,
        3,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        1,
        0
      ],
      [
        0,
        2,
        0
      ],
      [
        0,
        3,
        0
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        0,
        -2,
        2
      ],
      [
        0,
        -3,
        3
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        -1,
        0,
        1
      ],
      [
        -2,
        0,
        2
      ],
      [
        -3,
        0,
        3
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        0,
        1
      ],
      [
        0,
        0,
        2
      ],
      [
        0,
        0,
        3
      ]
    ]
  ],
  "K": [
    [
      [
        0,
        0,
        0
      ],
      [
        1,
        0,
        0
      ],
      [
        0,
        1,
        0
      ],
      [
        0,
        0,
        1
      ]
    ],
    [
      [
        0,
        0,
        0
      ],
      [
        0,
        -1,
        1
      ],
      [
        -1,
        0,
        1
      ],
      [
        0,
        0,
        1
      ]
    ]
  ]
}

def analyze_legacy_orientations():
    """Analyze the legacy piece orientations."""
    print("=== LEGACY PIECE ORIENTATION ANALYSIS ===\n")
    
    total_orientations = 0
    
    for piece_id in sorted(LEGACY_PIECES.keys()):
        orientations = LEGACY_PIECES[piece_id]
        count = len(orientations)
        total_orientations += count
        
        print(f"Piece {piece_id}: {count} orientations")
        
        # Show first orientation as example
        if orientations:
            first_orientation = orientations[0]
            print(f"  Example: {first_orientation}")
        print()
    
    print(f"=== SUMMARY ===")
    print(f"Total pieces: {len(LEGACY_PIECES)}")
    print(f"Total orientations: {total_orientations}")
    print(f"Average orientations per piece: {total_orientations / len(LEGACY_PIECES):.1f}")
    
    # Compare with theoretical maximum (24 for FCC)
    pieces_with_max = sum(1 for orientations in LEGACY_PIECES.values() if len(orientations) == 24)
    pieces_with_fewer = len(LEGACY_PIECES) - pieces_with_max
    
    print(f"\n=== COMPARISON WITH FCC THEORY ===")
    print(f"Expected max orientations per piece (FCC): 24")
    print(f"Pieces with 24 orientations: {pieces_with_max}")
    print(f"Pieces with fewer orientations: {pieces_with_fewer}")
    
    # Show pieces with high symmetry (fewer orientations)
    if pieces_with_fewer > 0:
        print(f"\nPieces with symmetry (fewer than 24 orientations):")
        for piece_id in sorted(LEGACY_PIECES.keys()):
            count = len(LEGACY_PIECES[piece_id])
            if count < 24:
                print(f"  {piece_id}: {count} orientations (symmetry factor: {24//count})")

def compare_with_current_analysis():
    """Compare with our current FCC analysis results."""
    print(f"\n=== COMPARISON WITH CURRENT ANALYSIS ===")
    
    # Our current analysis from analyze_pieces.py showed:
    current_analysis = {
        'A': 24, 'B': 24, 'C': 24, 'D': 6, 'E': 48, 'F': 12, 'G': 24, 'H': 12, 'I': 12,
        'J': 24, 'K': 2, 'L': 12, 'M': 24, 'N': 24, 'O': 24, 'P': 24, 'Q': 24, 'R': 24,
        'S': 24, 'T': 24, 'U': 12, 'V': 12, 'W': 12, 'X': 12, 'Y': 48
    }
    
    print("Comparison (Legacy vs Current Analysis):")
    print("Piece | Legacy | Current | Match")
    print("------|--------|---------|------")
    
    matches = 0
    total_compared = 0
    
    for piece_id in sorted(set(LEGACY_PIECES.keys()) | set(current_analysis.keys())):
        legacy_count = len(LEGACY_PIECES.get(piece_id, []))
        current_count = current_analysis.get(piece_id, 0)
        match = "Y" if legacy_count == current_count else "N"
        
        if piece_id in LEGACY_PIECES and piece_id in current_analysis:
            total_compared += 1
            if legacy_count == current_count:
                matches += 1
        
        print(f"  {piece_id}   |   {legacy_count:2d}   |   {current_count:2d}    |  {match}")
    
    print(f"\nMatching pieces: {matches}/{total_compared} ({100*matches/total_compared:.1f}%)")
    
    # Identify key discrepancies
    print(f"\n=== KEY DISCREPANCIES ===")
    for piece_id in sorted(LEGACY_PIECES.keys()):
        if piece_id in current_analysis:
            legacy_count = len(LEGACY_PIECES[piece_id])
            current_count = current_analysis[piece_id]
            if legacy_count != current_count:
                print(f"Piece {piece_id}: Legacy={legacy_count}, Current={current_count} (diff: {current_count-legacy_count:+d})")

def analyze_piece_shapes():
    """Analyze the actual shapes to understand symmetry patterns."""
    print(f"\n=== PIECE SHAPE ANALYSIS ===")
    
    # Look at pieces with different orientation counts
    interesting_pieces = ['A', 'D', 'K']  # A=3, D=6, K=2 in legacy
    
    for piece_id in interesting_pieces:
        if piece_id in LEGACY_PIECES:
            orientations = LEGACY_PIECES[piece_id]
            print(f"\nPiece {piece_id} ({len(orientations)} orientations):")
            
            for i, orientation in enumerate(orientations):
                print(f"  Orientation {i+1}: {orientation}")
            
            # Analyze the base shape
            base_shape = orientations[0]
            print(f"  Base shape analysis:")
            print(f"    Atoms: {len(base_shape)}")
            
            # Calculate relative positions from first atom
            if len(base_shape) > 1:
                relative_positions = []
                base_atom = base_shape[0]
                for atom in base_shape[1:]:
                    rel_pos = [atom[i] - base_atom[i] for i in range(3)]
                    relative_positions.append(rel_pos)
                print(f"    Relative positions: {relative_positions}")

if __name__ == "__main__":
    analyze_legacy_orientations()
    compare_with_current_analysis()
    analyze_piece_shapes()
