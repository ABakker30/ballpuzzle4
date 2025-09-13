import React, { useRef } from 'react';
import { SolutionJson } from '../../types/solution';
import { Slider } from '../common/Slider';

interface SolutionToolbarProps {
  onLoadSolution: (solution: SolutionJson) => void;
  solution: SolutionJson | null;
  maxPlacements: number;
  onMaxPlacementsChange: (max: number) => void;
}

export const SolutionToolbar: React.FC<SolutionToolbarProps> = ({
  onLoadSolution,
  solution,
  maxPlacements,
  onMaxPlacementsChange
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
          <Slider
            label="Show placements"
            min={0}
            max={totalPlacements}
            value={Math.min(maxPlacements, totalPlacements)}
            onChange={onMaxPlacementsChange}
            width="150px"
            formatValue={(value) => `${value} / ${totalPlacements}`}
          />
        </div>
      )}

    </div>
  );
};
