// Engine FCC (rhombohedral ints) -> world viewing coordinates (cubic embedding)

export function toWorld(x: number, y: number, z: number, scale = 0.5) {
  // FCC primitive vectors in cubic/world space
  // a1 = (0,1,1), a2 = (1,0,1), a3 = (1,1,0)
  const wx = (0 * x + 1 * y + 1 * z) * scale; // (y + z)
  const wy = (1 * x + 0 * y + 1 * z) * scale; // (x + z)
  const wz = (1 * x + 1 * y + 0 * z) * scale; // (x + y)
  return { x: wx, y: wy, z: wz };
}

// Optional helper to center a set of cells around the origin for nicer framing
export function computeCenter(cells: [number,number,number][], scale = 0.5) {
  if (!cells.length) return { x: 0, y: 0, z: 0 };
  let sx = 0, sy = 0, sz = 0;
  for (const [x,y,z] of cells) {
    const w = toWorld(x,y,z,scale);
    sx += w.x; sy += w.y; sz += w.z;
  }
  const n = cells.length;
  return { x: sx / n, y: sy / n, z: sz / n };
}
