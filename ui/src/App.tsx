import React from "react";
import { FilePicker } from "./components/FilePicker";
import { Viewer3D } from "./components/Viewer3D";
import StatusPanel from "./components/StatusPanel";
import RunForm from "./components/RunForm";
import ViewPage from "./pages/ViewPage";
import { ViewSolutionPage } from "./pages/ViewSolutionPage";
import { PuzzleShapePage } from "./pages/PuzzleShapePage";
import { useAppStore } from "./store";
import "./styles/theme.css";
import "./styles.css";

function TabButton({ id, label }: { id: "shape" | "solve" | "view" | "status"; label: string }) {
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
          <TabButton id="shape" label="Puzzle Shape" />
          <TabButton id="solve" label="Solve Puzzle" />
          <TabButton id="view" label="View Solution" />
          <TabButton id="status" label="Status (Live)" />
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
        {tab === "shape" && <PuzzleShapePage />}

        {tab === "solve" && <RunForm />}

        {tab === "view" && <ViewSolutionPage />}

        {tab === "status" && <StatusPanel />}
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
