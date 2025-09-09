type Args = Record<string, string | number | boolean | null | undefined>;

function quote(s:string) {
  return /[^\w\-./:]/.test(s) ? `"${s.replace(/"/g,'\\"')}"` : s;
}

export function buildSolveCLI(opts: {
  engine: "dfs"|"dlx"|"c";
  container: string;
  statusJson: string;
  statusIntervalMs?: number;
  statusMaxStack?: number;
  timeLimitS?: number;
  nodeLimit?: number;
  solutions?: number;
  k?: number;
  phase?: string;
  runId?: string;
}) {
  const base = ["python","-m","cli.solve"];
  const args: Args = {
    "--engine": opts.engine,
    "--status-json": opts.statusJson,
    "--status-interval-ms": opts.statusIntervalMs ?? 1000,
    "--status-max-stack": opts.statusMaxStack ?? 512,
    "--time-limit": opts.timeLimitS,
    "--caps-max-nodes": opts.nodeLimit,
    "--max-results": opts.solutions,
    "--status-phase": opts.phase,
  };
  const parts = [...base];
  for (const [k,v] of Object.entries(args)) {
    if (v === undefined || v === null || v === false) continue;
    parts.push(k, String(v));
  }
  // Add container as positional argument at the end
  parts.push(opts.container);
  return parts.map(quote).join(" ");
}
