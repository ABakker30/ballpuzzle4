/**
 * === FCC Lattice Conversion ===
 *
 * Engine (rhombohedral FCC indices) -> World (x,y,z):
 *   x = (j + k)/2 * a
 *   y = (i + k)/2 * a
 *   z = (i + j)/2 * a
 *
 * World (x,y,z) -> Engine (i,j,k):
 *   i = (y + z - x) / a
 *   j = (x + z - y) / a
 *   k = (x + y - z) / a
 *
 * Notes:
 * - 'a' is the lattice spacing (ball radius scale).
 * - Always round i,j,k to nearest integer after inverse, with small epsilon.
 * - Rotation snapping: check that inverse-mapped coords are integers.
 * - Keep scale 'a' consistent across viewer, snapping, and solution save.
 * - Convex hull orientation is applied in world space, but placements are
 *   saved back in engine (ijk) so solutions remain canonical.
 */

export interface Vector3 {
  x: number;
  y: number;
  z: number;
}

/**
 * Convert FCC lattice coordinates to world space position
 * @param i - FCC coordinate i
 * @param j - FCC coordinate j  
 * @param k - FCC coordinate k
 * @param a - Lattice parameter (scaling factor)
 * @returns World space position as Vector3
 */
export function fccToWorld(i: number, j: number, k: number, a: number = 1): Vector3 {
  const x = (j + k) / 2 * a;
  const y = (i + k) / 2 * a;
  const z = (i + j) / 2 * a;
  
  return { x, y, z };
}

/**
 * Convert world space position to FCC lattice coordinates
 * @param x - World coordinate x
 * @param y - World coordinate y
 * @param z - World coordinate z
 * @param a - Lattice parameter (scaling factor)
 * @returns FCC coordinates as {i, j, k}
 */
export function worldToFcc(x: number, y: number, z: number, a: number = 1): {i: number, j: number, k: number} {
  const i = (y + z - x) / a;
  const j = (x + z - y) / a;
  const k = (x + y - z) / a;
  
  return { i, j, k };
}

/**
 * Convert world space position to FCC lattice coordinates with rounding
 * @param x - World coordinate x
 * @param y - World coordinate y
 * @param z - World coordinate z
 * @param a - Lattice parameter (scaling factor)
 * @param epsilon - Rounding tolerance (default 1e-6)
 * @returns FCC coordinates as {i, j, k} rounded to nearest integers
 */
export function worldToFccRounded(x: number, y: number, z: number, a: number = 1, epsilon: number = 1e-6): {i: number, j: number, k: number} {
  const coords = worldToFcc(x, y, z, a);
  
  return {
    i: Math.round(coords.i + epsilon),
    j: Math.round(coords.j + epsilon), 
    k: Math.round(coords.k + epsilon)
  };
}

/**
 * Generate deterministic color for piece index
 * @param index - Piece index (0-based)
 * @returns RGB color as hex string
 */
export function pieceColor(index: number): string {
  // Generate deterministic HSL color based on index
  const hue = (index * 137.508) % 360; // Golden angle for good distribution
  const saturation = 70 + (index % 3) * 10; // 70-90% saturation
  const lightness = 50 + (index % 2) * 15; // 50-65% lightness
  
  return hslToHex(hue, saturation, lightness);
}

/**
 * Convert HSL to hex color
 */
function hslToHex(h: number, s: number, l: number): string {
  const sNorm = s / 100;
  const lNorm = l / 100;
  
  const c = (1 - Math.abs(2 * lNorm - 1)) * sNorm;
  const x = c * (1 - Math.abs((h / 60) % 2 - 1));
  const m = lNorm - c / 2;
  
  let r = 0, g = 0, b = 0;
  
  if (0 <= h && h < 60) {
    r = c; g = x; b = 0;
  } else if (60 <= h && h < 120) {
    r = x; g = c; b = 0;
  } else if (120 <= h && h < 180) {
    r = 0; g = c; b = x;
  } else if (180 <= h && h < 240) {
    r = 0; g = x; b = c;
  } else if (240 <= h && h < 300) {
    r = x; g = 0; b = c;
  } else if (300 <= h && h < 360) {
    r = c; g = 0; b = x;
  }
  
  const rHex = Math.round((r + m) * 255).toString(16).padStart(2, '0');
  const gHex = Math.round((g + m) * 255).toString(16).padStart(2, '0');
  const bHex = Math.round((b + m) * 255).toString(16).padStart(2, '0');
  
  return `#${rHex}${gHex}${bHex}`;
}

/**
 * Generate a unique key for world coordinates
 */
export function keyW(x: number, y: number, z: number): string {
  return `${x.toFixed(3)},${y.toFixed(3)},${z.toFixed(3)}`;
}

/**
 * Get direct neighbors in FCC lattice
 */
export function getDirectNeighbors(cell: { X: number; Y: number; Z: number }): Array<{ X: number; Y: number; Z: number }> {
  // FCC has 12 nearest neighbors
  const neighbors = [
    { X: cell.X + 0.5, Y: cell.Y + 0.5, Z: cell.Z },
    { X: cell.X - 0.5, Y: cell.Y - 0.5, Z: cell.Z },
    { X: cell.X + 0.5, Y: cell.Y, Z: cell.Z + 0.5 },
    { X: cell.X - 0.5, Y: cell.Y, Z: cell.Z - 0.5 },
    { X: cell.X, Y: cell.Y + 0.5, Z: cell.Z + 0.5 },
    { X: cell.X, Y: cell.Y - 0.5, Z: cell.Z - 0.5 },
    { X: cell.X + 0.5, Y: cell.Y - 0.5, Z: cell.Z },
    { X: cell.X - 0.5, Y: cell.Y + 0.5, Z: cell.Z },
    { X: cell.X + 0.5, Y: cell.Y, Z: cell.Z - 0.5 },
    { X: cell.X - 0.5, Y: cell.Y, Z: cell.Z + 0.5 },
    { X: cell.X, Y: cell.Y + 0.5, Z: cell.Z - 0.5 },
    { X: cell.X, Y: cell.Y - 0.5, Z: cell.Z + 0.5 }
  ];
  return neighbors;
}
