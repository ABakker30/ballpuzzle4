/**
 * FCC (Face-Centered Cubic) coordinate system utilities
 * Converts integer FCC coordinates to world space positions
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
  // FCC basis vectors: b1=(0,1,1), b2=(1,0,1), b3=(1,1,0)
  // world = (i*b1 + j*b2 + k*b3)/2 * a
  const x = (j + k) / 2 * a;
  const y = (i + k) / 2 * a;
  const z = (i + j) / 2 * a;
  
  return { x, y, z };
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
