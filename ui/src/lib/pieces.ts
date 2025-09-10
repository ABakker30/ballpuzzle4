import { fccToWorld, Vector3 } from './fcc';

// Piece definitions - each piece has 4 atoms at FCC coordinates
export const PIECE_DEFINITIONS: Record<number, number[][]> = {
  0: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]], // A
  1: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], // B
  2: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 0]], // C
  3: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [2, 1, 0]], // D
  4: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 0, 1]], // E
  5: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 0, 1]], // F
  6: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]], // G
  7: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 1, 1]], // H
  8: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 1]], // I
  9: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [2, 0, 0]], // J
  10: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 1, 1]], // K
  11: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 1]], // L
  12: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 1, 0]], // M
  13: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 0, 1]], // N
  14: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 0, 1]], // O
  15: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 2]], // P
  16: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [2, 1, 0]], // Q
  17: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 0, 1]], // R
  18: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [2, 0, 0]], // S
  19: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [2, 1, 0]], // T
  20: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 1]], // U
  21: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], // V
  22: [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 0, 2]], // W
  23: [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 1, 1]], // X
  24: [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 2, 0]], // Y
};

export interface PiecePlacement {
  piece: number;
  i: number;
  j: number;
  k: number;
  orientation?: number;
}

export interface AtomPosition {
  position: Vector3;
  pieceIndex: number;
  atomIndex: number; // 0-3 for each atom in the piece
}

/**
 * Expand a piece placement into all 4 atom positions in world coordinates
 */
export function expandPieceToAtoms(
  placement: PiecePlacement, 
  latticeScale: number = 1
): AtomPosition[] {
  const pieceDefinition = PIECE_DEFINITIONS[placement.piece];
  if (!pieceDefinition) {
    console.warn(`Unknown piece type: ${placement.piece}`);
    return [];
  }

  const atoms: AtomPosition[] = [];
  
  // For each atom in the piece definition
  pieceDefinition.forEach((atomOffset, atomIndex) => {
    // Add the piece anchor position to the atom offset
    const atomFccI = placement.i + atomOffset[0];
    const atomFccJ = placement.j + atomOffset[1];
    const atomFccK = placement.k + atomOffset[2];
    
    // Convert to world coordinates
    const worldPos = fccToWorld(atomFccI, atomFccJ, atomFccK, latticeScale);
    
    atoms.push({
      position: worldPos,
      pieceIndex: placement.piece,
      atomIndex
    });
  });

  return atoms;
}

/**
 * Expand multiple piece placements into all atom positions
 */
export function expandStackToAtoms(
  stack: PiecePlacement[], 
  latticeScale: number = 1
): AtomPosition[] {
  const allAtoms: AtomPosition[] = [];
  
  stack.forEach(placement => {
    const pieceAtoms = expandPieceToAtoms(placement, latticeScale);
    allAtoms.push(...pieceAtoms);
  });

  return allAtoms;
}

/**
 * Get piece name from index (A-Y)
 */
export function getPieceName(pieceIndex: number): string {
  if (pieceIndex < 0 || pieceIndex > 24) return '?';
  return String.fromCharCode(65 + pieceIndex); // A=65, B=66, etc.
}

/**
 * Get piece definition for debugging
 */
export function getPieceDefinition(pieceIndex: number): number[][] | undefined {
  return PIECE_DEFINITIONS[pieceIndex];
}
