/**
 * CID computation for container JSON files
 * Computes canonical identifier from engine/FCC coordinates
 */

export interface EngineCell {
  i: number;
  j: number;
  k: number;
}

/**
 * Compute CID from engine coordinates using the same canonicalization as container-loader
 * This ensures CID consistency between save and load operations
 */
export async function computeCID(engineCoords: EngineCell[]): Promise<string> {
  // Convert to cells format for canonicalization
  const cells = engineCoords.map(coord => [coord.i, coord.j, coord.k]);
  
  // Use the same canonicalization process as container-loader
  const canonicalCells = canonicalizeCells(cells);
  const payload = {
    version: '1.0',
    lattice: 'fcc',
    cells: canonicalCells
  };
  
  const serialized = JSON.stringify(payload, null, 0);
  const encoder = new TextEncoder();
  const data = encoder.encode(serialized);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  
  return `sha256:${hashHex}`;
}

// Import canonicalization functions from container-loader
// FCC rotation matrices (24 proper rotations)
const FCC_ROTATIONS = [
  [[1, 0, 0], [0, 1, 0], [0, 0, 1]],    // Identity
  [[1, 0, 0], [0, 0, -1], [0, 1, 0]],   // 90° around X
  [[1, 0, 0], [0, -1, 0], [0, 0, -1]],  // 180° around X
  [[1, 0, 0], [0, 0, 1], [0, -1, 0]],   // 270° around X
  [[0, 0, 1], [0, 1, 0], [-1, 0, 0]],   // 90° around Y
  [[-1, 0, 0], [0, 1, 0], [0, 0, -1]],  // 180° around Y
  [[0, 0, -1], [0, 1, 0], [1, 0, 0]],   // 270° around Y
  [[0, -1, 0], [1, 0, 0], [0, 0, 1]],   // 90° around Z
  [[-1, 0, 0], [0, -1, 0], [0, 0, 1]],  // 180° around Z
  [[0, 1, 0], [-1, 0, 0], [0, 0, 1]],   // 270° around Z
  [[0, 1, 0], [0, 0, 1], [1, 0, 0]],    // 120° [1,1,1]
  [[0, 0, 1], [1, 0, 0], [0, 1, 0]],    // 240° [1,1,1]
  [[0, 0, -1], [1, 0, 0], [0, -1, 0]],  // 120° [1,1,-1]
  [[0, -1, 0], [0, 0, -1], [1, 0, 0]],  // 240° [1,1,-1]
  [[0, 0, 1], [-1, 0, 0], [0, -1, 0]],  // 120° [1,-1,1]
  [[0, -1, 0], [0, 0, 1], [-1, 0, 0]],  // 240° [1,-1,1]
  [[0, 0, -1], [-1, 0, 0], [0, 1, 0]],  // 120° [-1,1,1]
  [[0, 1, 0], [0, 0, -1], [-1, 0, 0]],  // 240° [-1,1,1]
  [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],   // 90° around [1,1,0]
  [[0, 0, 1], [0, -1, 0], [1, 0, 0]],   // 90° around [1,-1,0]
  [[0, 0, -1], [0, -1, 0], [-1, 0, 0]], // 90° around [-1,-1,0]
  [[-1, 0, 0], [0, 0, -1], [0, -1, 0]], // 90° around [-1,1,0]
  [[0, -1, 0], [-1, 0, 0], [0, 0, -1]], // 90° around [1,0,1]
  [[0, 1, 0], [1, 0, 0], [0, 0, -1]],   // 90° around [-1,0,1]
];

function normalizeTranslation(cells: number[][]): number[][] {
  if (cells.length === 0) return cells;
  
  // Find minimum coordinates
  const min = [Infinity, Infinity, Infinity];
  for (const cell of cells) {
    for (let i = 0; i < 3; i++) {
      min[i] = Math.min(min[i], cell[i]);
    }
  }
  
  // Translate to origin
  return cells.map(cell => [
    cell[0] - min[0],
    cell[1] - min[1], 
    cell[2] - min[2]
  ]);
}

function applyRotation(cells: number[][], rotation: number[][]): number[][] {
  return cells.map(cell => [
    rotation[0][0] * cell[0] + rotation[0][1] * cell[1] + rotation[0][2] * cell[2],
    rotation[1][0] * cell[0] + rotation[1][1] * cell[1] + rotation[1][2] * cell[2],
    rotation[2][0] * cell[0] + rotation[2][1] * cell[1] + rotation[2][2] * cell[2]
  ]);
}

function canonicalizeCells(cells: number[][]): number[][] {
  if (cells.length === 0) return cells;
  
  const normalized = normalizeTranslation(cells);
  const candidates: number[][][] = [];
  
  // Apply all 24 FCC rotations
  for (const rotation of FCC_ROTATIONS) {
    const rotated = applyRotation(normalized, rotation);
    const renormalized = normalizeTranslation(rotated);
    const sorted = [...renormalized].sort((a, b) => {
      for (let i = 0; i < 3; i++) {
        if (a[i] !== b[i]) return a[i] - b[i];
      }
      return 0;
    });
    candidates.push(sorted);
  }
  
  // Return lexicographically smallest candidate
  return candidates.reduce((min, candidate) => {
    const compareArrays = (a: number[][], b: number[][]) => {
      for (let i = 0; i < Math.min(a.length, b.length); i++) {
        for (let j = 0; j < 3; j++) {
          if (a[i][j] !== b[i][j]) return a[i][j] - b[i][j];
        }
      }
      return a.length - b.length;
    };
    
    return compareArrays(candidate, min) < 0 ? candidate : min;
  });
}

/**
 * Extract short CID for display (first 8 chars after prefix)
 */
export function shortCID(cid: string): string {
  if (cid.startsWith('sha256:')) {
    return cid.slice(7, 15);
  }
  return cid.slice(0, 8);
}
