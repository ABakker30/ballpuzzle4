import React from "react";
import { StatusData } from '../types/status';
import { useStatus } from '../hooks/useStatus';
import { LiveStack3D } from "./LiveStack3D";

function KPI({ label, value }: { label:string; value:React.ReactNode }) {
  return (
    <div className="kpi" style={{ minWidth: 0, overflow: 'hidden' }}>
      <div className="kpi-label" style={{ fontSize: '0.75rem', whiteSpace: 'nowrap' }}>{label}</div>
      <div className="kpi-value" style={{ fontSize: '1rem', fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis' }}>{value}</div>
    </div>
  );
}

function formatDuration(ms: number): string {
  const seconds = (ms / 1000).toFixed(1);
  return `${seconds}s`;
}

export default function StatusPanel() {
  const { data, error, lastOkAt } = useStatus();
  
  // Add error boundary and debugging
  if (error && !data) return <div className="card error">Status unavailable: {error}</div>;
  if (!data) return <div className="card">Waiting for status…</div>;

  // Validate data structure
  if (!data.metrics) {
    console.error('StatusPanel: Invalid data structure - missing metrics', data);
    return <div className="card error">Invalid status data format</div>;
  }

  const elapsed = formatDuration(data.metrics.elapsed_ms);
  
  return (
    <div className="status-panel">
      <div className="status-header">
        <h2>Status</h2>
        <div className="status-time">{elapsed}</div>
      </div>
      
      <div className="status-metrics" style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '12px', maxWidth: '100%' }}>
        <KPI label="Nodes" value={data ? data.metrics.nodes.toLocaleString() : "—"} />
        <KPI label="Pruned" value={data ? data.metrics.pruned.toLocaleString() : "—"} />
        <KPI label="Depth" value={data ? data.metrics.depth.toLocaleString() : "—"} />
        <KPI label="Best" value={data && data.metrics.best_depth ? data.metrics.best_depth.toLocaleString() : "—"} />
        <KPI label="Solutions" value={data ? data.metrics.solutions.toLocaleString() : "—"} />
        <KPI label="Phase" value={data ? data.phase : "—"} />
      </div>

      <div className="meta">
        <div>Container: <code title={data.container.cid}>{data.container.cid.length > 20 ? data.container.cid.substring(0, 20) + '...' : data.container.cid}</code> ({data.container.cells} cells)</div>
        <div>Run ID: <code>{data.run_id}</code></div>
        <div>Last update: {new Date(data.ts_ms).toLocaleTimeString()}</div>
        {lastOkAt && (Date.now() - lastOkAt) > (3 * 1000) && <div className="badge">Paused or finished?</div>}
        {error && <div className="badge warn">Read error: {error}</div>}
        {data.stack_truncated && <div className="badge">Showing tail of stack</div>}
      </div>

      <LiveStack3D />
    </div>
  );
}
