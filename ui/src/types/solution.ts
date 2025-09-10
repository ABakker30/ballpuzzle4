export interface LatticeCell { i:number; j:number; k:number; }

export interface ContainerJson {
  cid: string;
  cells: number;
  lattice?: string;        // "fcc" expected
  coords?: LatticeCell[];  // optional, present in some exports
}

export interface Placement {
  piece: string; 
  orientation?: number;
  orient?: number; 
  ori?: number;  // Actual field used in solution files
  t?: number[];  // Translation/anchor point [i,j,k]
  cells_ijk?: number[][]; // Full piece coordinates in engine format
  anchor?: number[];
  i?: number; 
  j?: number; 
  k?: number;
  coordinates?: number[][];
}

export interface SolutionJson {
  version?: number;
  containerCidSha256?: string;
  lattice?: string;
  piecesUsed?: Record<string, number>;
  placements: Placement[];
  sid?: string;
  cid?: string;
  sid_state_sha256?: string;
  sid_route_sha256?: string;
  sid_state_canon_sha256?: string;
  mode?: string;
  solver?: {
    engine: string;
    seed?: number;
    flags?: Record<string, any>;
  };
}

export type EventType =
  | "node" | "pruned" | "placement" | "backtrack" | "solution" | "done";

export interface EventBase { t?: number; type: EventType; }

export interface EventPlacement extends EventBase {
  type: "placement";
  piece: number; orient: number; i:number; j:number; k:number;
}

export interface EventPruned extends EventBase { type: "pruned"; count:number; }
export interface EventNode extends EventBase { type: "node"; }
export interface EventBacktrack extends EventBase { type: "backtrack"; }
export interface EventSolution extends EventBase { type: "solution"; sid?: string; }
export interface EventDone extends EventBase {
  type: "done"; nodes?: number; pruned?: number; depth?: number; elapsed_ms?: number;
}

export type EventsAny =
  | EventPlacement | EventPruned | EventNode | EventBacktrack | EventSolution | EventDone;

export interface EventsSummary {
  nodes: number;
  pruned: number;
  depthMax: number;
  solutions: number;
  elapsedMs?: number;
}
