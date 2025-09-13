// Engine/FCC coordinates (stored in container JSON files)
export interface EngineCell {
  i: number;
  j: number;
  k: number;
}

// World-int coordinates (used internally by editor)
export interface WorldCell {
  X: number;
  Y: number;
  Z: number;
}

// Container v1.0 format (strict)
export interface ContainerV1 {
  version: '1.0';
  lattice: 'fcc';
  cells: number[][]; // Array of [i, j, k] triplets
  cid: string;
  designer: {
    name: string;
    date: string;
    email?: string;
  };
  // UI compatibility field (mapped from cells)
  coordinates?: number[][];
}

// Legacy container format (deprecated - for backward compatibility only)
export interface ContainerJson {
  version?: string;
  lattice?: string;
  coordinates?: number[][]; // Array of [i, j, k] triplets
  cid?: string;
  designer?: {
    name: string;
    date: string;
    email?: string;
  };
  // Legacy fields (deprecated)
  name?: string;
  cells?: number;
  lattice_type?: string;
}
