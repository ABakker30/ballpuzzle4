import React, { useCallback, useRef } from "react";
import { useAppStore } from "../store";
import { validateContainer, validateSolution, validateEventLine } from "../libs/schema";

type Kind = "container" | "solution" | "events";

export const FilePicker: React.FC<{ kind: Kind }> = ({ kind }) => {
  const inputRef = useRef<HTMLInputElement>(null);

  const setStatus = useAppStore(s =>
    kind === "container" ? s.setContainerStatus :
    kind === "solution"  ? s.setSolutionStatus  : s.setEventsStatus
  );
  const setObj = useAppStore(s =>
    kind === "container" ? s.setContainerObj :
    kind === "solution"  ? s.setSolutionObj  : s.setEventsLines
  );

  const onFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const f = files[0];

    try {
      if (kind === "events") {
        const txt = await f.text();
        const lines = txt.split(/\r?\n/).filter(Boolean);
        // Validate first line for sanity; store all
        if (lines.length > 0) validateEventLine(JSON.parse(lines[0]));
        setStatus({ ok: true, message: `${lines.length} lines` });
        setObj(lines);
        return;
      }

      const obj = JSON.parse(await f.text());
      if (kind === "container") {
        validateContainer(obj);
        setStatus({ ok: true, message: `${obj.coordinates?.length ?? 0} cells` });
      } else {
        validateSolution(obj);
        setStatus({ ok: true, message: `${obj.placements?.length ?? 0} placements` });
      }
      setObj(obj);
    } catch (e: any) {
      setStatus({ ok: false, message: e?.message ?? "Invalid file" });
      setObj(null);
    }
  }, [kind, setObj, setStatus]);

  const onClick = () => inputRef.current?.click();

  const onDrop = (ev: React.DragEvent) => {
    ev.preventDefault();
    onFiles(ev.dataTransfer.files);
  };

  return (
    <div
      className="drop"
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDrop}
      onClick={onClick}
      title="Click or drop a file"
    >
      <input
        ref={inputRef}
        type="file"
        accept={kind === "events" ? ".jsonl" : ".json"}
        style={{ display: "none" }}
        onChange={(e) => onFiles(e.currentTarget.files)}
      />
      <div>Click or drop a {kind === "events" ? "JSONL event log" : "JSON file"}</div>
    </div>
  );
};
