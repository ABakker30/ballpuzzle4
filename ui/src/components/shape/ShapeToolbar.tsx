import React, { useRef, useState } from 'react';
import { ContainerV1, EngineCell } from '../../types/shape';
import { engineToWorldInt } from '../../lib/lattice';
import { loadContainerV1, ContainerLoadResponse } from '../../lib/container-loader';

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
  onShowError?: (title: string, message: string, details?: string[]) => void;
  onShowWarning?: (message: string) => void;
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
  onShowError,
  onShowWarning
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
        <button className="button" onClick={handleLoadClick} disabled={isLoading}>
          {isLoading ? 'Loading...' : 'Load Shape'}
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
