import type { EventsAny, EventsSummary } from "../types/solution";

/** Parse a JSONL string into events (lenient; skips bad lines). */
export function parseJsonl(text: string): EventsAny[] {
  const lines = text.split(/\r?\n/);
  const out: EventsAny[] = [];
  for (const line of lines) {
    const s = line.trim();
    if (!s) continue;
    try {
      const obj = JSON.parse(s);
      if (obj && typeof obj.type === "string") out.push(obj as EventsAny);
    } catch { /* skip invalid line */ }
  }
  return out;
}

/** Compute simple rollup metrics from events. */
export function summarizeEvents(events: EventsAny[]): EventsSummary {
  let nodes = 0, pruned = 0, depth = 0, depthMax = 0, solutions = 0;
  let elapsedMs: number | undefined;

  for (const e of events) {
    switch (e.type) {
      case "node": nodes++; break;
      case "pruned": pruned += (e as any).count ?? 1; break;
      case "placement": depth++; if (depth > depthMax) depthMax = depth; break;
      case "backtrack": depth = Math.max(0, depth - 1); break;
      case "solution": solutions++; break;
      case "done": elapsedMs = elapsedMs ?? (e as any).elapsed_ms; break;
    }
  }

  return { nodes, pruned, depthMax, solutions, elapsedMs };
}
