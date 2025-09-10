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
 * Compute CID from engine coordinates using SHA-256
 * Sorts coordinates canonically and generates CIDv2-<hex> identifier
 */
export async function computeCID(engineCoords: EngineCell[]): Promise<string> {
  // Sort coordinates canonically by (i, j, k)
  const sortedCoords = [...engineCoords].sort((a, b) => {
    if (a.i !== b.i) return a.i - b.i;
    if (a.j !== b.j) return a.j - b.j;
    return a.k - b.k;
  });

  // Create canonical string representation
  const coordString = sortedCoords
    .map(coord => `${coord.i},${coord.j},${coord.k}`)
    .join(';');

  // Compute SHA-256 hash
  const encoder = new TextEncoder();
  const data = encoder.encode(coordString);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  
  // Convert to hex string
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  
  return `CIDv2-${hashHex}`;
}

/**
 * Extract short CID for display (first 8 chars after prefix)
 */
export function shortCID(cid: string): string {
  if (cid.startsWith('CIDv2-')) {
    return cid.slice(6, 14);
  }
  return cid.slice(0, 8);
}
