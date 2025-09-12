import React, { useRef } from 'react';
import { ContainerJson, EngineCell } from '../../types/shape';
import { engineToWorldInt } from '../../lib/lattice';

export interface ShapeToolbarProps {
  containerName: string;
  cellCount: number;
  onLoadContainer: (container: ContainerJson) => void;
  onFitView: () => void;
  onResetView: () => void;
  onSaveAsNew: () => void;
  onClear: () => void;
  liveCID: string;
  canSave: boolean;
}

export const ShapeToolbar: React.FC<ShapeToolbarProps> = ({
  onLoadContainer,
  onFitView,
  onResetView,
  cellCount = 0,
  containerName = 'No container loaded',
  onSaveAsNew,
  liveCID = '',
  canSave = true,
  onClear
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const container = JSON.parse(content) as ContainerJson;
        
        // Basic validation - check for coordinates field
        const coords = container.coordinates || [];
        if (!Array.isArray(coords)) {
          throw new Error('Invalid container format: coordinates must be an array');
        }
        
        // Validate coordinate format
        if (coords.length > 0 && !Array.isArray(coords[0])) {
          throw new Error('Invalid container format: coordinates must be arrays of [i,j,k]');
        }
        
        // Normalize the container format
        const normalizedContainer = {
          ...container,
          coordinates: coords
        };
        
        onLoadContainer(normalizedContainer);
      } catch (error) {
        console.error('Error loading container:', error);
        alert(`Error loading container: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    };
    reader.readAsText(file);
  };

  const handleLoadClick = () => {
    fileInputRef.current?.click();
  };

  const handleSaveShape = () => {
    if (!canSave || !onSaveAsNew) return;
    
    // Call the existing save function which will trigger file download
    onSaveAsNew();
  };

  return (
    <div className="shape-toolbar">
      <div className="toolbar-section">
        <button className="button" onClick={handleLoadClick}>
          Load Shape
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      </div>


      <div className="toolbar-section">
        <button 
          className="button primary" 
          onClick={handleSaveShape}
          disabled={!canSave}
          title={!canSave ? `Cell count must be divisible by 4 (current: ${cellCount})` : 'Save shape to file'}
        >
          Save Shape
        </button>
        <button 
          className="button" 
          onClick={onClear}
          title="Clear all cells"
        >
          Clear
        </button>
      </div>


      <div className="toolbar-section">
        <div className="stats-chips">
          <div className="chip">
            <span className="chip-label">Container:</span>
            <span className="chip-value">{containerName}</span>
          </div>
          <div className="chip">
            <span className="chip-label">Cells:</span>
            <span className="chip-value">{cellCount}</span>
          </div>
          {liveCID && (
            <div className="chip">
              <span className="chip-label">CID:</span>
              <span className="chip-value">{liveCID.slice(6, 14)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
