/**
 * Lattice coordinate conversions between World-int and Engine/FCC coordinates
 * 
 * World-int: Simple cubic grid (X,Y,Z) where editor operates
 * Engine/FCC: Face-centered cubic (i,j,k) stored in container JSON
 * 
 * Conversion formulas:
 * Engine → World: X = j + k, Y = i + k, Z = i + j
 * World → Engine: i = (Y + Z - X) / 2, j = (X + Z - Y) / 2, k = (X + Y - Z) / 2
 * 
 * FCC parity rule: (X + Y + Z) must be even for valid World cells
 */

export interface WorldCell {
  X: number;
  Y: number;
  Z: number;
}

export interface EngineCell {
  i: number;
  j: number;
  k: number;
}

/**
 * Check if World-int coordinates satisfy FCC parity rule
 */
export function isValidWorldCell(X: number, Y: number, Z: number): boolean {
  return ((X + Y + Z) % 2) === 0;
}

/**
 * Convert Engine/FCC coordinates to World-int coordinates
 */
export function engineToWorldInt(i: number, j: number, k: number): WorldCell {
  return {
    X: j + k,
    Y: i + k,
    Z: i + j
  };
}

/**
 * Convert World-int coordinates to Engine/FCC coordinates
 * Returns null if coordinates don't satisfy FCC parity rule
 */
export function worldToEngineInt(X: number, Y: number, Z: number): EngineCell | null {
  // Check parity rule first
  if (!isValidWorldCell(X, Y, Z)) {
    return null;
  }

  // Calculate engine coordinates
  const i = (Y + Z - X) / 2;
  const j = (X + Z - Y) / 2;
  const k = (X + Y - Z) / 2;

  // Verify all results are integers (should be true for valid world cells)
  if (!Number.isInteger(i) || !Number.isInteger(j) || !Number.isInteger(k)) {
    return null;
  }

  return { i, j, k };
}

/**
 * Generate stable string key for World cell
 */
export function keyW(X: number, Y: number, Z: number): string {
  return `${X},${Y},${Z}`;
}

/**
 * Generate stable string key for Engine cell
 */
export function keyE(i: number, j: number, k: number): string {
  return `${i},${j},${k}`;
}

/**
 * Parse World cell key back to coordinates
 */
export function parseWorldKey(key: string): WorldCell {
  const [X, Y, Z] = key.split(',').map(Number);
  return { X, Y, Z };
}

/**
 * Parse Engine cell key back to coordinates
 */
export function parseEngineKey(key: string): EngineCell {
  const [i, j, k] = key.split(',').map(Number);
  return { i, j, k };
}

// Unit test functions for verification
export function testRoundTrip(): boolean {
  // Test various engine coordinates
  const testCases = [
    { i: 0, j: 0, k: 0 },
    { i: 1, j: 0, k: -1 },
    { i: 0, j: 1, k: 0 },
    { i: -1, j: 2, k: -1 },
    { i: 1, j: 2, k: -3 }
  ];

  for (const engine of testCases) {
    // Engine → World → Engine
    const world = engineToWorldInt(engine.i, engine.j, engine.k);
    const backToEngine = worldToEngineInt(world.X, world.Y, world.Z);
    
    if (!backToEngine || 
        backToEngine.i !== engine.i || 
        backToEngine.j !== engine.j || 
        backToEngine.k !== engine.k) {
      console.error('Round-trip failed for', engine, '→', world, '→', backToEngine);
      return false;
    }

    // Verify parity rule
    if (!isValidWorldCell(world.X, world.Y, world.Z)) {
      console.error('Parity rule failed for', world);
      return false;
    }
  }

  console.log('All round-trip tests passed');
  return true;
}

/**
 * Calculate optimal sphere radius based on minimum distance between cells
 * Returns half the minimum distance for proper sphere packing
 */
export function calculateOptimalRadius(cells: WorldCell[]): number {
  if (cells.length < 2) return 0.4;
  
  let minDistance = Infinity;
  
  for (let i = 0; i < cells.length; i++) {
    for (let j = i + 1; j < cells.length; j++) {
      const dx = cells[i].X - cells[j].X;
      const dy = cells[i].Y - cells[j].Y;
      const dz = cells[i].Z - cells[j].Z;
      const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
      
      if (distance < minDistance) {
        minDistance = distance;
      }
    }
  }
  
  // Return half the minimum distance to ensure spheres don't overlap
  return Math.max(0.1, minDistance / 2.2);
}

// Get all FCC neighbors of a cell (12-connected in FCC lattice)
export function getDirectNeighbors(cell: WorldCell): WorldCell[] {
  const neighbors: WorldCell[] = [];
  
  // In FCC lattice, neighbors are at distance sqrt(2) in world coordinates
  // These are the 12 nearest neighbors in FCC
  const offsets = [
    [1, 1, 0], [1, -1, 0], [-1, 1, 0], [-1, -1, 0],
    [1, 0, 1], [1, 0, -1], [-1, 0, 1], [-1, 0, -1],
    [0, 1, 1], [0, 1, -1], [0, -1, 1], [0, -1, -1]
  ];
  
  for (const [dx, dy, dz] of offsets) {
    neighbors.push({
      X: cell.X + dx,
      Y: cell.Y + dy,
      Z: cell.Z + dz
    });
  }
  
  return neighbors;
}

// Check if a cell is adjacent to any existing cells
export function isAdjacentToExistingCells(targetCell: WorldCell, existingCells: WorldCell[]): boolean {
  const neighbors = getDirectNeighbors(targetCell);
  
  return neighbors.some(neighbor => 
    existingCells.some(existing => 
      existing.X === neighbor.X && existing.Y === neighbor.Y && existing.Z === neighbor.Z
    )
  );
}

// Get valid neighbor positions that can be added (adjacent to existing cells and valid FCC)
export function getValidNeighborPositions(existingCells: WorldCell[]): WorldCell[] {
  const neighborSet = new Set<string>();
  const validNeighbors: WorldCell[] = [];
  
  // For each existing cell, get its neighbors
  existingCells.forEach(cell => {
    const neighbors = getDirectNeighbors(cell);
    
    neighbors.forEach(neighbor => {
      const key = keyW(neighbor.X, neighbor.Y, neighbor.Z);
      
      // Skip if already processed or if it's an existing cell
      if (neighborSet.has(key)) return;
      if (existingCells.some(existing => 
        existing.X === neighbor.X && existing.Y === neighbor.Y && existing.Z === neighbor.Z
      )) return;
      
      // Check if it's a valid FCC position
      if (isValidWorldCell(neighbor.X, neighbor.Y, neighbor.Z)) {
        neighborSet.add(key);
        validNeighbors.push(neighbor);
      }
    });
  });
  
  return validNeighbors;
}

// Run tests on module load (development only)
if (typeof window !== 'undefined' && window.location?.hostname === 'localhost') {
  testRoundTrip();
}
