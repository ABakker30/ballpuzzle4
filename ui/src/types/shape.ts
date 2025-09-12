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

// Container JSON format (matches actual file structure)
export interface ContainerJson {
  name?: string;
  cid?: string;
  cells?: number;
  lattice?: string;
  lattice_type?: string;
  coordinates?: number[][]; // Array of [i, j, k] triplets
}
