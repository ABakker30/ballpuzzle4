import React, { useMemo, useState } from "react";
import type { ContainerJson, SolutionJson, EventsAny, EventsSummary } from "../types/solution";
import { LoadersPanel } from "../components/View/Loaders";
import { Timeline } from "../components/View/Timeline";
import { summarizeEvents } from "../utils/jsonl";

export default function ViewPage() {
  const [container, setContainer] = useState<ContainerJson | null>(null);
  const [solution, setSolution] = useState<SolutionJson | null>(null);
  const [events, setEvents] = useState<EventsAny[] | null>(null);
  const [idx, setIdx] = useState(0);

  const eventsSummary: EventsSummary | null = useMemo(
    () => events ? summarizeEvents(events) : null, [events]
  );

  const placementsShown = useMemo(
    () => solution?.placements?.slice(0, idx) ?? [],
    [solution, idx]
  );

  return (
    <div style={{display:"grid", gap:16}}>
      <h2>View a Solution</h2>

      <LoadersPanel
        onContainer={(_, data)=> setContainer(data)}
        onSolution={(_, data)=> { setSolution(data); setIdx(0); }}
        onEvents={(_, data)=> setEvents(data)}
      />

      <div className="card">
        <h3>Summary</h3>
        <div className="kpi-grid">
          <div className="kpi"><div className="kpi-label">Container CID</div><div className="kpi-value">{container?.cid ?? "—"}</div></div>
          <div className="kpi"><div className="kpi-label">Cells</div><div className="kpi-value">{container?.cells ?? "—"}</div></div>
          <div className="kpi"><div className="kpi-label">Solution SID</div><div className="kpi-value">{solution?.sid ?? "—"}</div></div>
          <div className="kpi"><div className="kpi-label">Placements</div><div className="kpi-value">{solution?.placements?.length ?? 0}</div></div>
          <div className="kpi"><div className="kpi-label">Events: Nodes</div><div className="kpi-value">{eventsSummary?.nodes?.toLocaleString?.() ?? "—"}</div></div>
          <div className="kpi"><div className="kpi-label">Events: Pruned</div><div className="kpi-value">{eventsSummary?.pruned?.toLocaleString?.() ?? "—"}</div></div>
          <div className="kpi"><div className="kpi-label">Events: Max Depth</div><div className="kpi-value">{eventsSummary?.depthMax ?? "—"}</div></div>
          <div className="kpi"><div className="kpi-label">Events: Solutions</div><div className="kpi-value">{eventsSummary?.solutions ?? "—"}</div></div>
          <div className="kpi"><div className="kpi-label">Elapsed</div><div className="kpi-value">{eventsSummary?.elapsedMs != null ? (eventsSummary.elapsedMs/1000).toFixed(1)+"s" : "—"}</div></div>
        </div>
      </div>

      {solution?.placements && solution.placements.length > 0 && (
        <>
          <Timeline placements={solution.placements} onIndexChange={setIdx} />
          <div className="card">
            <h3>Placements (0..{idx})</h3>
            <div style={{maxHeight: 280, overflow:"auto"}}>
              <table style={{width:"100%", fontSize:12}}>
                <thead><tr>
                  <th>#</th><th>Piece</th><th>Orient</th><th>i</th><th>j</th><th>k</th>
                </tr></thead>
                <tbody>
                  {solution.placements.slice(0, idx).map((p, n) => (
                    <tr key={n}>
                      <td>{n+1}</td><td>{p.piece}</td><td>{p.orient}</td>
                      <td>{p.i}</td><td>{p.j}</td><td>{p.k}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
