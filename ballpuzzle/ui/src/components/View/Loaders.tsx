import React, { useRef } from "react";
import type { ContainerJson, SolutionJson, EventsAny } from "../../types/solution";
import { parseJsonl } from "../../utils/jsonl";

export function FilePicker({
  label, accept, onLoad
}: { label:string; accept:string; onLoad:(name:string, data:any)=>void }) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <div className="card">
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:12}}>
        <div>{label}</div>
        <div style={{display:"flex",gap:8}}>
          <input ref={ref} type="file" accept={accept}
            onChange={async (e) => {
              const f = e.target.files?.[0]; if (!f) return;
              const text = await f.text();
              let data:any = null;
              try {
                if (accept.includes("jsonl")) data = parseJsonl(text) as EventsAny[];
                else data = JSON.parse(text);
                onLoad(f.name, data);
              } catch (err:any) {
                onLoad(f.name, { __error: err?.message || "Parse error" });
              } finally {
                if (ref.current) ref.current.value = "";
              }
            }} />
        </div>
      </div>
    </div>
  );
}

export function LoadersPanel({
  onContainer, onSolution, onEvents
}: {
  onContainer: (meta:{name:string}, data:ContainerJson)=>void;
  onSolution: (meta:{name:string}, data:SolutionJson)=>void;
  onEvents:   (meta:{name:string}, data:EventsAny[])=>void;
}) {
  return (
    <div style={{display:"grid", gap:12}}>
      <FilePicker label="Container JSON" accept=".json,application/json"
        onLoad={(name, data)=> onContainer({name}, data as ContainerJson)} />
      <FilePicker label="Solution JSON" accept=".json,application/json"
        onLoad={(name, data)=> onSolution({name}, data as any)} />
      <FilePicker label="Events JSONL (optional)" accept=".jsonl,text/plain"
        onLoad={(name, data)=> onEvents({name}, data as any)} />
    </div>
  );
}
