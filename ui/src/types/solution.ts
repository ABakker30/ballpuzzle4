export interface LatticeCell { i:number; j:number; k:number; }

export interface ContainerJson {
  cid: string;
  cells: number;
  lattice?: string;        // "fcc" expected
  coords?: LatticeCell[];  // optional, present in some exports
}

export interface Placement {
  piece: number; orient: number; i:number; j:number; k:number;
}

export interface SolutionJson {
  sid: string;
  cid: string;
  placements: Placement[];
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
