import React, { useRef } from 'react';
import { SolutionJson } from '../../types/solution';

interface SolutionToolbarProps {
  onLoadSolution: (solution: SolutionJson) => void;
  solution: SolutionJson | null;
  maxPlacements: number;
  onMaxPlacementsChange: (max: number) => void;
  brightness: number;
  onBrightnessChange: (brightness: number) => void;
}

export const SolutionToolbar: React.FC<SolutionToolbarProps> = ({
  onLoadSolution,
  solution,
  maxPlacements,
  onMaxPlacementsChange,
  brightness,
  onBrightnessChange
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const solutionData = JSON.parse(content) as SolutionJson;
        
        // Validate that it has placements
        if (!solutionData.placements || !Array.isArray(solutionData.placements)) {
          throw new Error('Invalid solution format: missing or invalid placements array');
        }
        
        onLoadSolution(solutionData);
      } catch (error) {
        console.error('Error loading solution:', error);
        alert(`Error loading solution: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    };
    reader.readAsText(file);
  };

  const handleLoadClick = async () => {
    // Try File System Access API first (modern browsers)
    if ('showOpenFilePicker' in window) {
      try {
        const [fileHandle] = await (window as any).showOpenFilePicker({
          types: [{
            description: 'Solution JSON files',
            accept: { 'application/json': ['.json'] }
          }],
          multiple: false
        });
        
        const file = await fileHandle.getFile();
        const content = await file.text();
        const solutionData = JSON.parse(content) as SolutionJson;
        
        // Validate that it has placements
        if (!solutionData.placements || !Array.isArray(solutionData.placements)) {
          throw new Error('Invalid solution format: missing or invalid placements array');
        }
        
        onLoadSolution(solutionData);
        return;
      } catch (error) {
        // User cancelled or error occurred, fall back to input
        if ((error as Error).name !== 'AbortError') {
          console.warn('File System Access API failed:', error);
        }
      }
    }
    
    // Fallback: traditional file input
    fileInputRef.current?.click();
  };

  const totalPlacements = solution?.placements?.length || 0;

  return (
    <div className="shape-toolbar">
      <div className="toolbar-section">
        <button className="button" onClick={handleLoadClick}>
          Load Solution
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      </div>

      {solution && (
        <div className="toolbar-section">
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            Show placements:
            <input
              type="range"
              min="0"
              max={totalPlacements}
              value={Math.min(maxPlacements, totalPlacements)}
              onChange={(e) => onMaxPlacementsChange(parseInt(e.target.value))}
              style={{ width: '150px' }}
            />
            <span style={{ minWidth: '60px', fontSize: '14px' }}>
              {Math.min(maxPlacements, totalPlacements)} / {totalPlacements}
            </span>
          </label>
        </div>
      )}

      <div className="toolbar-section">
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          Brightness:
          <input
            type="range"
            min="0.2"
            max="3.0"
            step="0.1"
            value={brightness}
            onChange={(e) => onBrightnessChange(parseFloat(e.target.value))}
            style={{ width: '120px' }}
          />
          <span style={{ minWidth: '40px', fontSize: '14px' }}>
            {brightness.toFixed(1)}x
          </span>
        </label>
      </div>

      <div className="toolbar-section">
        <div className="stats-chips">
          <div className="chip">
            <span className="chip-label">Engine:</span>
            <span className="chip-value">{solution?.solver?.engine || 'Unknown'}</span>
          </div>
          <div className="chip">
            <span className="chip-label">Placements:</span>
            <span className="chip-value">{totalPlacements}</span>
          </div>
          {solution?.piecesUsed && (
            <div className="chip">
              <span className="chip-label">Pieces:</span>
              <span className="chip-value">
                {Object.values(solution.piecesUsed).reduce((sum, count) => sum + count, 0)}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
