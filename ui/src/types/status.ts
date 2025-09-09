export type EngineName = "dfs" | "dlx" | "c" | string;

export interface StackItem { piece:number; orient:number; i:number; j:number; k:number; }
export interface ContainerInfo { cid:string; cells:number; }

export interface StatusSnapshotV1 {
  v: number; ts_ms: number; engine: EngineName; run_id: string;
  container: ContainerInfo; k?: number | null;
  nodes: number; pruned: number; depth: number; best_depth?: number | null;
  solutions: number; elapsed_ms: number; stack: StackItem[];
  stack_truncated?: boolean; hash_container_cid?: string | null; hash_solution_sid?: string | null;
  phase?: string | null;
}

export function isStatusV1(x:any): x is StatusSnapshotV1 {
  return !!x && x.v === 1 &&
    Number.isInteger(x.ts_ms) &&
    typeof x.engine === "string" &&
    x.container && typeof x.container.cid === "string" && Number.isInteger(x.container.cells) &&
    Number.isInteger(x.nodes) && Number.isInteger(x.pruned) &&
    Number.isInteger(x.depth) && Number.isInteger(x.solutions) && Number.isInteger(x.elapsed_ms) &&
    Array.isArray(x.stack);
}
