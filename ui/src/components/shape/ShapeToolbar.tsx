import React, { useRef, useState } from 'react';
import { ContainerV1, EngineCell } from '../../types/shape';
import { engineToWorldInt } from '../../lib/lattice';
import { loadContainerV1, ContainerLoadResponse } from '../../lib/container-loader';
import { Slider } from '../common/Slider';

export interface ShapeToolbarProps {
  containerName: string;
  cellCount: number;
  onLoadContainer: (container: ContainerV1) => void;
  onFitView: () => void;
  onResetView: () => void;
  onSaveAsNew: () => void;
  onClear: () => void;
  liveCID: string;
  canSave: boolean;
  editMode: 'add' | 'delete';
  onEditModeChange: (mode: 'add' | 'delete') => void;
  onShowError?: (title: string, message: string, details?: string[]) => void;
  onShowWarning?: (message: string) => void;
  brightness: number;
  onBrightnessChange: (brightness: number) => void;
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
  onClear,
  editMode,
  onEditModeChange,
  onShowError,
  onShowWarning,
  brightness,
  onBrightnessChange
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    
    try {
      const result: ContainerLoadResponse = await loadContainerV1(file);
      
      if (!result.success) {
        // Schema validation failed
        if (onShowError) {
          onShowError(
            'Invalid Container Format',
            result.error,
            result.details
          );
        } else {
          const details = result.details ? '\n\nDetails:\n' + result.details.join('\n') : '';
          alert(`${result.error}${details}`);
        }
        return;
      }
      
      // Check for CID mismatch
      if (result.cidMismatch && result.computedCid) {
        const warningMsg = `CID mismatch detected!\nExpected: ${result.container.cid}\nComputed: ${result.computedCid}\n\nThe container will still load, but the CID may be incorrect.`;
        
        if (onShowWarning) {
          onShowWarning(warningMsg);
        } else {
          console.warn('CID mismatch:', {
            expected: result.container.cid,
            computed: result.computedCid
          });
        }
      }
      
      // Successfully loaded
      onLoadContainer(result.container);
      
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error occurred';
      if (onShowError) {
        onShowError('Load Error', 'Failed to load container file', [errorMsg]);
      } else {
        alert(`Failed to load container: ${errorMsg}`);
      }
    } finally {
      setIsLoading(false);
      // Clear the input so the same file can be selected again
      event.target.value = '';
    }
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
        <button 
          className="button" 
          onClick={handleLoadClick}
          title="Load shape from file"
        >
          Load
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".json,.fcc.json"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      </div>

      <div className="toolbar-section">
        {/* Edit Mode Toggle */}
        <button
          className={`edit-mode-toggle ${editMode === 'add' ? 'add-mode' : 'delete-mode'}`}
          onClick={() => onEditModeChange(editMode === 'add' ? 'delete' : 'add')}
          title={editMode === 'add' ? 'Switch to Delete Mode' : 'Switch to Add Mode'}
        >
          {editMode === 'add' ? '+' : '−'}
        </button>
      </div>

      <div className="toolbar-section">
        <button 
          className="button primary" 
          onClick={handleSaveShape}
          disabled={!canSave}
          title={!canSave ? `Cell count must be divisible by 4 (current: ${cellCount})` : 'Save shape to file'}
        >
          Save
        </button>
      </div>


      <div className="toolbar-section">
        <Slider
          label="Brightness"
          min={0.1}
          max={8.0}
          step={0.1}
          value={brightness}
          onChange={onBrightnessChange}
          width="120px"
          formatValue={(value) => `${value.toFixed(1)}`}
          title="Adjust scene lighting brightness"
        />
      </div>

      <div className="toolbar-section">
        <div className="stats-chips">
          <div className="chip">
            <span className="chip-label">Cells:</span>
            <span className="chip-value">{cellCount}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
