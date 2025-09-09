import React from "react";
import { FilePicker } from "./components/FilePicker";
import { Viewer3D } from "./components/Viewer3D";
import StatusPanel from "./components/StatusPanel";
import RunForm from "./components/RunForm";
import ViewPage from "./pages/ViewPage";
import { useAppStore } from "./store";
import "./styles/theme.css";
import "./styles.css";

function TabButton({ id, label }: { id: "home" | "viewer" | "dashboard" | "status" | "run" | "view"; label: string }) {
  const tab = useAppStore(s => s.tab);
  const setTab = useAppStore(s => s.setTab);
  const active = tab === id;
  return (
    <button className={active ? "tab active" : "tab"} onClick={() => setTab(id)}>
      {label}
    </button>
  );
}

function PlacementList() {
  const placements = useAppStore(s => s.solutionObj?.placements || []);
  const selectedIdx = useAppStore(s => s.selectedPlacementIdx);
  const setSelected = useAppStore(s => s.setSelectedPlacementIdx);
  if (!placements.length) return <div className="card">No placements loaded</div>;
  return (
    <div className="card" style={{ maxHeight: "calc(100vh - 180px)", overflowY: "auto" }}>
      <h3>Placements</h3>
      <ul style={{ listStyle:"none", padding:0, margin:0 }}>
        {placements.map((pl: any, idx: number) => (
          <li key={idx}
              className={idx === selectedIdx ? "row active" : "row"}
              onClick={() => setSelected(idx)}>
            <code>{pl.piece}</code> &nbsp; ori={pl.ori} &nbsp; t=[{pl.t.join(",")}]
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function App() {
  const tab = useAppStore(s => s.tab);
  const containerStatus = useAppStore(s => s.containerStatus);
  const solutionStatus = useAppStore(s => s.solutionStatus);
  const eventsStatus = useAppStore(s => s.eventsStatus);

  // Initialize theme from localStorage
  React.useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      document.documentElement.dataset.theme = savedTheme;
    }
  }, []);

  return (
    <div className="app">
      <header>
        <h1>Ballpuzzle UI</h1>
        <div className="tabs">
          <TabButton id="home" label="Home" />
          <TabButton id="viewer" label="Viewer (placeholder)" />
          <TabButton id="dashboard" label="Dashboard (placeholder)" />
          <TabButton id="status" label="Status" />
          <TabButton id="run" label="Run" />
          <TabButton id="view" label="View" />
        </div>
        <button 
          className="button" 
          onClick={() => {
            const theme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
            document.documentElement.dataset.theme = theme;
            localStorage.setItem('theme', theme);
          }}
          style={{ marginLeft: 'auto' }}
        >
          🌓
        </button>
      </header>

      <main>
        {tab === "home" && (
          <div className="grid">
            <section className="card">
              <h2>Container</h2>
              <FilePicker kind="container" />
              <Status {...containerStatus} />
            </section>
            <section className="card">
              <h2>Solution</h2>
              <FilePicker kind="solution" />
              <Status {...solutionStatus} />
            </section>
            <section className="card">
              <h2>Event Log</h2>
              <FilePicker kind="events" />
              <Status {...eventsStatus} />
            </section>
          </div>
        )}

        {tab === "viewer" && (
          <div className="grid" style={{ gridTemplateColumns: "280px 1fr" }}>
            <div>
              <PlacementList />
            </div>
            <div className="card" style={{ padding:0 }}>
              <Viewer3D />
            </div>
          </div>
        )}

        {tab === "dashboard" && (
          <div className="placeholder">
            <p>Dashboard placeholder. Next steps:</p>
            <ul>
              <li>Parse JSONL events, validate by schema</li>
              <li>Plot nodes/pruned/depth vs time</li>
              <li>Render <code>done</code> metrics</li>
            </ul>
          </div>
        )}

        {tab === "status" && <StatusPanel />}

        {tab === "run" && <RunForm />}

        {tab === "view" && <ViewPage />}
      </main>
    </div>
  );
}

function Status(props: { ok: boolean | null; message: string }) {
  if (props.ok === null) return <div className="badge">No file</div>;
  return (
    <div className={props.ok ? "badge ok" : "badge err"}>
      {props.ok ? "Valid" : "Invalid"} {props.message ? `— ${props.message}` : ""}
    </div>
  );
}
