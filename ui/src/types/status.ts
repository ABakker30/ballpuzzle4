export type EngineName = "dfs" | "dlx" | "c" | string;

export interface Cell {
  i: number;
  j: number;
  k: number;
}

export interface PlacedPiece {
  instance_id: number;
  piece_type: number;
  piece_label: string; // e.g., "A"
  cells: Cell[];       // container FCC
}

export interface Metrics {
  nodes: number;
  pruned: number;
  depth: number;
  solutions: number;
  elapsed_ms: number;
  best_depth?: number;
}

export interface ContainerInfo {
  cid: string;
  cells: number;
}

export interface StatusData {
  version: 2;
  ts_ms: number;
  engine: string;
  phase: string;      // init|search|verifying|done
  run_id: string;
  container: ContainerInfo;
  metrics: Metrics;
  stack_truncated: boolean;
  stack: PlacedPiece[];
}

export function isValidStatus(x: any): x is StatusData {
  return !!x && x.version === 2 && x.container && Array.isArray(x.stack);
}
