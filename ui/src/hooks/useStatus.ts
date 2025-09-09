import { useEffect, useRef, useState } from "react";
import { isStatusV1, type StatusSnapshotV1 } from "../types/status";

const DEFAULT_URL = import.meta.env.VITE_STATUS_URL || "/.status/status.json";
const DEFAULT_INTERVAL = Number(import.meta.env.VITE_STATUS_INTERVAL_MS || 1000);

export function useStatus(url = DEFAULT_URL, intervalMs = DEFAULT_INTERVAL) {
  const [data, setData] = useState<StatusSnapshotV1 | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastOkAt, setLastOkAt] = useState<number | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    let aborted = false;
    async function tick() {
      try {
        const res = await fetch(`${url}?_=${Date.now()}`, { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (isStatusV1(json)) {
          if (!aborted) { setData(json); setError(null); setLastOkAt(Date.now()); }
        } else {
          throw new Error("Invalid status shape");
        }
      } catch (e:any) {
        if (!aborted) setError(e?.message || "Fetch error");
      } finally {
        if (!aborted) timer.current = window.setTimeout(tick, intervalMs) as unknown as number;
      }
    }
    tick();
    return () => { aborted = true; if (timer.current) window.clearTimeout(timer.current); };
  }, [url, intervalMs]);

  return { data, error, lastOkAt };
}
