#!/usr/bin/env python3
"""
Complete analysis of legacy piece orientations vs current FCC analysis.
"""

# Complete legacy piece data
LEGACY_PIECES = {
    "A": 3, "B": 8, "C": 24, "D": 6, "E": 48, "F": 12, "G": 24, "H": 12, "I": 12,
    "J": 24, "K": 2, "L": 12, "M": 24, "N": 24, "O": 24, "P": 24, "Q": 24, "R": 24,
    "S": 24, "T": 24, "U": 12, "V": 12, "W": 12, "X": 12, "Y": 48
}

# Current FCC analysis results
CURRENT_ANALYSIS = {
    'A': 24, 'B': 24, 'C': 24, 'D': 6, 'E': 48, 'F': 12, 'G': 24, 'H': 12, 'I': 12,
    'J': 24, 'K': 2, 'L': 12, 'M': 24, 'N': 24, 'O': 24, 'P': 24, 'Q': 24, 'R': 24,
    'S': 24, 'T': 24, 'U': 12, 'V': 12, 'W': 12, 'X': 12, 'Y': 48
}

def analyze_complete_comparison():
    """Complete comparison of legacy vs current orientation counts."""
    print("=== COMPLETE LEGACY VS CURRENT ANALYSIS ===\n")
    
    print("Piece | Legacy | Current | Match | Reduction Factor")
    print("------|--------|---------|-------|------------------")
    
    matches = 0
    total_legacy = 0
    total_current = 0
    max_reduction = 0
    
    for piece_id in sorted(LEGACY_PIECES.keys()):
        legacy_count = LEGACY_PIECES[piece_id]
        current_count = CURRENT_ANALYSIS[piece_id]
        match = "Y" if legacy_count == current_count else "N"
        reduction_factor = current_count / legacy_count if legacy_count > 0 else 1
        
        total_legacy += legacy_count
        total_current += current_count
        
        if legacy_count == current_count:
            matches += 1
        
        if reduction_factor > max_reduction:
            max_reduction = reduction_factor
        
        print(f"  {piece_id}   |   {legacy_count:2d}   |   {current_count:2d}    |  {match}   |      {reduction_factor:.1f}x")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total pieces: {len(LEGACY_PIECES)}")
    print(f"Matching pieces: {matches}/{len(LEGACY_PIECES)} ({100*matches/len(LEGACY_PIECES):.1f}%)")
    print(f"Total orientations - Legacy: {total_legacy}")
    print(f"Total orientations - Current: {total_current}")
    print(f"Overall reduction potential: {total_current/total_legacy:.1f}x")
    print(f"Maximum piece reduction: {max_reduction:.1f}x")
    
    # Calculate candidate space impact
    print(f"\n=== CANDIDATE SPACE IMPACT ===")
    print(f"Legacy system candidate space: ~{total_legacy:,}")
    print(f"Current system candidate space: ~{total_current:,}")
    print(f"Potential speedup from symmetry reduction: {total_current/total_legacy:.1f}x")
    
    # Show pieces with highest reduction potential
    print(f"\n=== HIGHEST REDUCTION PIECES ===")
    reductions = []
    for piece_id in LEGACY_PIECES.keys():
        legacy_count = LEGACY_PIECES[piece_id]
        current_count = CURRENT_ANALYSIS[piece_id]
        if current_count > legacy_count:
            reduction = current_count / legacy_count
            reductions.append((piece_id, legacy_count, current_count, reduction))
    
    reductions.sort(key=lambda x: x[3], reverse=True)
    for piece_id, legacy, current, reduction in reductions[:5]:
        print(f"  {piece_id}: {legacy} -> {current} ({reduction:.1f}x reduction)")

if __name__ == "__main__":
    analyze_complete_comparison()
