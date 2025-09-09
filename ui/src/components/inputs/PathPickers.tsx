import React, { useState, useRef } from "react";

interface ContainerPathPickerProps {
  value: string;
  onChange: (path: string) => void;
}

export function ContainerPathPicker({ value, onChange }: ContainerPathPickerProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Extract basename and preserve directory prefix if it looks like a repo path
      const basename = file.name;
      if (value.includes("data/containers/")) {
        const pathParts = value.split("/");
        pathParts[pathParts.length - 1] = basename;
        onChange(pathParts.join("/"));
      } else {
        onChange(`data/containers/samples/${basename}`);
      }
    }
    // Reset input to allow selecting same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".json,application/json"
        onChange={handleFileSelect}
        style={{ display: "none" }}
      />
      <button
        type="button"
        className="button"
        onClick={() => fileInputRef.current?.click()}
      >
        Browse…
      </button>
    </>
  );
}

interface StatusPathPickerProps {
  value: string;
  onChange: (path: string) => void;
}

export function StatusPathPicker({ value, onChange }: StatusPathPickerProps) {
  const [useDefault, setUseDefault] = useState(true);
  const [customFilename, setCustomFilename] = useState("status.json");
  const [folderSelected, setFolderSelected] = useState(false);

  const handleModeChange = (isDefault: boolean) => {
    setUseDefault(isDefault);
    if (isDefault) {
      onChange("ui/public/.status/status.json");
    } else {
      onChange(`ui/public/.status/${customFilename}`);
    }
  };

  const handleFilenameChange = (filename: string) => {
    setCustomFilename(filename);
    if (!useDefault) {
      onChange(`ui/public/.status/${filename}`);
    }
  };

  const handleFolderPick = async () => {
    try {
      // Feature detect File System Access API
      if ('showDirectoryPicker' in window) {
        const dirHandle = await (window as any).showDirectoryPicker();
        if (dirHandle.name.includes('.status')) {
          setFolderSelected(true);
        }
      }
    } catch (err) {
      // User cancelled or API not available
    }
  };

  const isValidFilename = /^[\w\-.]+\.json$/.test(customFilename);

  return (
    <div style={{ display: "grid", gap: "8px" }}>
      <div style={{ display: "flex", gap: "12px" }}>
        <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <input
            type="radio"
            checked={useDefault}
            onChange={() => handleModeChange(true)}
          />
          Use default (/.status/status.json)
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <input
            type="radio"
            checked={!useDefault}
            onChange={() => handleModeChange(false)}
          />
          Custom filename
        </label>
      </div>

      {!useDefault && (
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <input
            className="input"
            value={customFilename}
            onChange={(e) => handleFilenameChange(e.target.value)}
            placeholder="status.json"
            style={{ flex: 1 }}
          />
          {'showDirectoryPicker' in window && (
            <button
              type="button"
              className="button"
              onClick={handleFolderPick}
            >
              Pick status folder
            </button>
          )}
          {folderSelected && (
            <span className="badge ok">Folder selected</span>
          )}
        </div>
      )}

      {!useDefault && !isValidFilename && (
        <div className="help" style={{ color: "var(--bad)" }}>
          Filename must match pattern: letters, numbers, dots, hyphens, and end with .json
        </div>
      )}

      <div className="help">
        Plan A serves this at <code>/.status/{useDefault ? "status.json" : customFilename}</code>. 
        Engines must write into <code>ui/public/.status/</code>.
      </div>
    </div>
  );
}
