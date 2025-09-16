import React, { useEffect, useRef, useState } from "react";
import type { Placement } from "../../types/solution";

export function Timeline({
  placements, onIndexChange
}: { placements: Placement[]; onIndexChange: (idx:number)=>void }) {
  const [playing, setPlaying] = useState(false);
  const [idx, setIdx] = useState(0);
  const [speed, setSpeed] = useState(1); // steps per tick
  const raf = useRef<number | null>(null);

  useEffect(() => {
    if (!playing) return;
    function step() {
      setIdx(prev => {
        const next = Math.min(prev + speed, placements.length);
        onIndexChange(next);
        if (next >= placements.length) setPlaying(false);
        return next;
      });
      raf.current = requestAnimationFrame(step);
    }
    raf.current = requestAnimationFrame(step);
    return () => { if (raf.current) cancelAnimationFrame(raf.current); };
  }, [playing, speed, placements.length, onIndexChange]);

  useEffect(() => { onIndexChange(idx); }, [idx, onIndexChange]);

  return (
    <div className="card" style={{display:"grid", gap:8}}>
      <div style={{display:"flex", gap:8, alignItems:"center"}}>
        <button onClick={()=>setPlaying(p=>!p)}>{playing ? "Pause" : "Play"}</button>
        <button onClick={()=>{ setIdx(0); onIndexChange(0); }}>Reset</button>
        <label>Speed
          <input type="number" min={1} max={60} value={speed}
            onChange={e=>setSpeed(Math.max(1, Math.min(60, Number(e.target.value)||1)))} />
        </label>
        <div>Step {idx} / {placements.length}</div>
      </div>
      <input type="range" min={0} max={placements.length} value={idx}
        onChange={e => setIdx(Number(e.target.value))}/>
    </div>
  );
}
