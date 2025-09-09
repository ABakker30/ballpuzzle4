import React from "react";
import { useStatus } from "../hooks/useStatus";

function KPI({ label, value }: { label:string; value:React.ReactNode }) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
    </div>
  );
}

export default function StatusPanel() {
  const { data, error, lastOkAt } = useStatus();
  if (error && !data) return <div className="card error">Status unavailable: {error}</div>;
  if (!data) return <div className="card">Waiting for status…</div>;

  const seconds = (data.elapsed_ms / 1000).toFixed(1);
  const stale = lastOkAt ? (Date.now() - lastOkAt) > (3 * 1000) : false;

  return (
    <div className="status-wrap">
      <div className="kpi-grid">
        <KPI label="Engine" value={String(data.engine).toUpperCase()} />
        <KPI label="Phase" value={data.phase ?? "—"} />
        <KPI label="Elapsed" value={`${seconds}s`} />
        <KPI label="Nodes" value={data.nodes.toLocaleString()} />
        <KPI label="Pruned" value={data.pruned.toLocaleString()} />
        <KPI label="Depth" value={data.depth} />
        {typeof data.best_depth === "number" && <KPI label="Best Depth" value={data.best_depth} />}
        <KPI label="Solutions" value={data.solutions} />
        {typeof data.k === "number" && <KPI label="K" value={data.k} />}
      </div>

      <div className="meta">
        <div>Container: <code title={data.container.cid}>{data.container.cid}</code> ({data.container.cells} cells)</div>
        <div>Run ID: <code>{data.run_id}</code></div>
        <div>Last update: {new Date(data.ts_ms).toLocaleTimeString()}</div>
        {stale && <div className="badge">Paused or finished?</div>}
        {error && <div className="badge warn">Read error: {error}</div>}
        {data.stack_truncated && <div className="badge">Showing tail of stack</div>}
      </div>
    </div>
  );
}
