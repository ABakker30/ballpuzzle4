import React, { useState, useEffect, useMemo } from "react";
import { buildSolveCLI } from "../utils/cli";
import { ContainerPathPicker, StatusPathPicker } from "./inputs/PathPickers";

export default function RunForm() {
  const [engine, setEngine] = useState<"dfs" | "dlx" | "c">("dfs");
  const [container, setContainer] = useState("data/containers/legacy_fixed/16 cell container.json");
  const [solutions, setSolutions] = useState<number | undefined>(1);
  const [timeLimit, setTimeLimit] = useState<number | undefined>(10);
  const [statusJson, setStatusJson] = useState("ui/public/.status/status.json");
  const [interval, setInterval] = useState(1000);
  const [stackCap, setStackCap] = useState(100);
  const [nodeLimit, setNodeLimit] = useState<number | undefined>(1000000);
  const [k, setK] = useState<number | undefined>(0);
  const [phase, setPhase] = useState("");
  const [runId, setRunId] = useState("");
  const [os, setOs] = useState<"bash" | "powershell">("powershell");
  const [wrap, setWrap] = useState(true);
  const [copied, setCopied] = useState(false);
  const [statusReachable, setStatusReachable] = useState<boolean | null>(null);

  const singlelineCmd = useMemo(() => buildSolveCLI({
    engine,
    container,
    statusJson,
    statusIntervalMs: interval,
    statusMaxStack: stackCap,
    timeLimitS: timeLimit,
    nodeLimit,
    solutions,
    k,
    phase: phase || undefined,
    runId: runId || undefined,
  }), [engine, container, statusJson, interval, stackCap, timeLimit, nodeLimit, solutions, k, phase, runId]);

  const applyDfsQuick = () => {
    setEngine("dfs");
    setContainer("data/containers/legacy_fixed/16 cell container.json");
    setSolutions(1);
    setTimeLimit(10);
    setStatusJson("ui/public/.status/status.json");
    setInterval(1000);
    setStackCap(100);
    setNodeLimit(10000);
    setK(0);
    setPhase("");
    setRunId("dfs-quick");
  };

  const applyDlxDemo = () => {
    setEngine("dlx");
    setContainer("data/containers/samples/Shape_3.json");
    setSolutions(5);
    setTimeLimit(30);
    setStatusJson("ui/public/.status/status.json");
    setInterval(500);
    setStackCap(200);
    setNodeLimit(50000);
    setK(0);
    setPhase("");
    setRunId("dlx-demo");
  };

  function toMultiline(cmd: string, shell: "bash" | "powershell") {
    const breaks = [
      "--container",
      "--status-json",
      "--status-interval-ms",
      "--status-max-stack",
      "--time-limit-s",
      "--node-limit",
      "--solutions",
      "--k",
      "--phase",
      "--run-id",
    ];
    let out = cmd;
    for (const flag of breaks) out = out.replace(new RegExp(` ${flag} `, "g"), ` \\\n  ${flag} `);
    if (shell === "powershell") {
      // Powershell uses backtick for line-continuation; show wrapped with backticks
      out = out.replace(/\\\n/g, "`\n");
    }
    return out;
  }

  const multilineCmd = useMemo(() => toMultiline(singlelineCmd, os), [singlelineCmd, os]);

  function copySingleline() {
    navigator.clipboard.writeText(singlelineCmd).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    });
  }

  // Check status file reachability
  useEffect(() => {
    const basename = statusJson.split('/').pop() || 'status.json';
    const checkUrl = `/.status/${basename}`;
    
    fetch(checkUrl)
      .then(response => setStatusReachable(response.ok))
      .catch(() => setStatusReachable(false));
  }, [statusJson]);

  return (
    <div className="panel">
      <h3>Run a Solve (CLI Builder)</h3>
      <div className="subtle">Prepare a command to run locally. Open the Status tab to monitor live.</div>

      {/* Presets */}
      <div className="pills">
        <button className="pill" onClick={applyDfsQuick}>DFS Quick</button>
        <button className="pill" onClick={applyDlxDemo}>DLX Demo</button>
      </div>

      {/* BASIC */}
      <div className="form-grid">
        <div className="field">
          <label><strong>Engine</strong></label>
          <select className="input" value={engine} onChange={e=>setEngine(e.target.value as "dfs" | "dlx" | "c")}>
            <option value="dfs">DFS</option>
            <option value="dlx">DLX</option>
            <option value="c">C</option>
          </select>
        </div>

        <div className="field full">
          <label htmlFor="container-path"><strong>Container</strong></label>
          <div style={{display:"flex", gap:8}}>
            <input id="container-path" name="container" className="input" value={container} onChange={e=>setContainer(e.target.value)} placeholder="path to container json" style={{flex:1}} />
            <ContainerPathPicker value={container} onChange={setContainer} />
          </div>
          <div className="help">Pick a JSON or type a repo path (e.g. <code>data/containers/samples/Shape_1.json</code>).</div>
        </div>

        <div className="field">
          <label htmlFor="solutions"><strong>Solutions</strong></label>
          <input id="solutions" name="solutions" className="input" type="number" value={solutions ?? ""} onChange={e=>setSolutions(e.target.value ? Number(e.target.value) : undefined)} />
        </div>

        <div className="field">
          <label htmlFor="time-limit"><strong>Time limit (s)</strong></label>
          <input id="time-limit" name="timeLimit" className="input" type="number" value={timeLimit ?? ""} onChange={e=>setTimeLimit(e.target.value ? Number(e.target.value) : undefined)} />
          <div className="help">Stop after this many seconds.</div>
        </div>

        <div className="field full">
          <label><strong>Status JSON</strong></label>
          <StatusPathPicker value={statusJson} onChange={setStatusJson} />
          <div style={{marginTop:6}}>
            {statusReachable === true && <span className="badge ok">reachable</span>}
            {statusReachable === false && <span className="badge">not found (yet)</span>}
          </div>
        </div>
      </div>

      {/* ADVANCED */}
      <details style={{marginTop:16}}>
        <summary>Advanced options</summary>
        <div className="form-grid" style={{marginTop:12}}>
          <div className="field">
            <label htmlFor="interval"><strong>Interval (ms)</strong></label>
            <input id="interval" name="interval" className="input" type="number" value={interval} onChange={e=>setInterval(Number(e.target.value)||1000)} />
            <div className="help">Status update frequency.</div>
          </div>

          <div className="field">
            <label htmlFor="stack-cap"><strong>Stack cap</strong></label>
            <input id="stack-cap" name="stackCap" className="input" type="number" value={stackCap} onChange={e=>setStackCap(Number(e.target.value)||512)} />
            <div className="help">Max stack depth to track.</div>
          </div>

          <div className="field">
            <label htmlFor="node-limit"><strong>Node limit</strong></label>
            <input id="node-limit" name="nodeLimit" className="input" type="number" value={nodeLimit ?? ""} onChange={e=>setNodeLimit(e.target.value ? Number(e.target.value) : undefined)} />
          </div>

          <div className="field">
            <label htmlFor="k-value"><strong>K</strong></label>
            <input id="k-value" name="k" className="input" type="number" value={k ?? ""} onChange={e=>setK(e.target.value ? Number(e.target.value) : undefined)} />
          </div>

          <div className="field">
            <label htmlFor="phase"><strong>Phase</strong></label>
            <input id="phase" name="phase" className="input" value={phase} onChange={e=>setPhase(e.target.value)} />
          </div>

          <div className="field">
            <label htmlFor="run-id"><strong>Run ID</strong></label>
            <input id="run-id" name="runId" className="input" value={runId} onChange={e=>setRunId(e.target.value)} placeholder="auto" />
          </div>
        </div>
      </details>

      {/* ===== Command Preview ===== */}
      <div className="code-panel" style={{marginTop:16}}>
        <div className="code-header">
          <div className="code-title">Command Preview</div>
          <div style={{display:"flex", gap:12, alignItems:"center"}}>
            <div className="code-tabs" role="tablist" aria-label="Shell">
              <button className="btn-ghost" role="tab" aria-selected={os==="bash"} onClick={()=>setOs("bash")}>Bash</button>
              <button className="btn-ghost" role="tab" aria-selected={os==="powershell"} onClick={()=>setOs("powershell")}>PowerShell</button>
            </div>
            <div className="code-actions">
              <button className="btn-ghost" onClick={()=>setWrap(w=>!w)} aria-pressed={wrap}>
                {wrap ? "Unwrap" : "Wrap"}
              </button>
            </div>
          </div>
        </div>

        <div className="code-body">
          <pre className="cmd">{wrap ? multilineCmd : singlelineCmd}</pre>
        </div>

        <div className="code-foot">
          <button className="btn-copy" onClick={copySingleline}>
            {copied ? "Copied ✓" : "Copy"}
          </button>
          <a className="btn-link" href="/.status/status.json" target="_blank" rel="noreferrer">Open status.json</a>
          <a className="btn-link" href="#" onClick={() => window.location.hash = "#status"}>Go to Status</a>
          <span className="badge-soft note">Running this command overwrites the status file set above.</span>
        </div>
      </div>
    </div>
  );
}
