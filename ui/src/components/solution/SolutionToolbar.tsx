import React, { useRef, useState } from 'react';
import { SolutionJson } from '../../types/solution';
import { Slider } from '../common/Slider';

interface SolutionToolbarProps {
  solution: SolutionJson | null;
  maxPlacements: number;
  totalPlacements: number;
  onMaxPlacementsChange: (value: number) => void;
  onLoadSolution: (solution: SolutionJson) => void;
  pieceSpacing: number;
  onPieceSpacingChange: (spacing: number) => void;
  onTakeScreenshot: () => void;
  onCreateMovie: (duration: number, fpsQuality: 'preview' | 'production' | 'high', showPlacement: boolean, placementPercentage: number, showSeparation: boolean, separationPercentage: number, aspectRatio: 'square' | 'landscape' | 'portrait' | 'instagram_story' | 'instagram_post', showRotation: boolean, rotationPercentage: number, rotations: number) => void;
}

export const SolutionToolbar: React.FC<SolutionToolbarProps> = ({
  onLoadSolution,
  solution,
  maxPlacements,
  totalPlacements,
  onMaxPlacementsChange,
  pieceSpacing,
  onPieceSpacingChange,
  onTakeScreenshot,
  onCreateMovie
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showMovieDialog, setShowMovieDialog] = useState(false);
  const [movieDuration, setMovieDuration] = useState(10);
  const [fpsQuality, setFpsQuality] = useState<'preview' | 'production' | 'high'>('production');
  const [showPlacementAnimation, setShowPlacementAnimation] = useState(true);
  const [placementPercentage, setPlacementPercentage] = useState(40);
  const [showSeparationAnimation, setShowSeparationAnimation] = useState(true);
  const [separationPercentage, setSeparationPercentage] = useState(40);
  const [aspectRatio, setAspectRatio] = useState<'square' | 'landscape' | 'portrait' | 'instagram_story' | 'instagram_post'>('square');
  const [showRotationAnimation, setShowRotationAnimation] = useState(false);
  const [rotationPercentage, setRotationPercentage] = useState(20);
  const [rotations, setRotations] = useState(1);

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

  const handleCreateMovie = () => {
    onCreateMovie(movieDuration, fpsQuality, showPlacementAnimation, placementPercentage, showSeparationAnimation, separationPercentage, aspectRatio, showRotationAnimation, rotationPercentage, rotations);
    setShowMovieDialog(false);
  };

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
            step={0.1}
            value={Math.min(maxPlacements, totalPlacements)}
            onChange={onMaxPlacementsChange}
            width="150px"
            formatValue={(value) => `${value.toFixed(1)} / ${totalPlacements}`}
          />
        </div>
      )}

      {solution && (
        <div className="toolbar-section">
          <Slider
            label="Separation"
            min={1}
            max={2}
            step={0.01}
            value={pieceSpacing}
            onChange={onPieceSpacingChange}
            width="150px"
            title="Scale piece centroids from pivot; 1.0 = original, 2.0 = doubled distance"
          />
        </div>
      )}

      {solution && (
        <div className="toolbar-section">
          <button className="button" onClick={onTakeScreenshot} title="Take Screenshot">
            📸
          </button>
          <button className="button" onClick={() => setShowMovieDialog(true)} title="Create Movie">
            🎬
          </button>
        </div>
      )}

      {showMovieDialog && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'var(--surface)',
            padding: '24px',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            minWidth: '300px'
          }}>
            <h3 style={{ margin: '0 0 16px 0' }}>Create Movie</h3>
            
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>
                Duration (seconds):
              </label>
              <input
                type="number"
                min="1"
                max="60"
                value={movieDuration}
                onChange={(e) => setMovieDuration(parseInt(e.target.value))}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid var(--border)',
                  borderRadius: '4px'
                }}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>
                Quality:
              </label>
              <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="radio"
                    name="fpsQuality"
                    value="preview"
                    checked={fpsQuality === 'preview'}
                    onChange={(e) => setFpsQuality(e.target.value as any)}
                    style={{ marginRight: '4px' }}
                  />
                  Preview (10fps)
                </label>
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="radio"
                    name="fpsQuality"
                    value="production"
                    checked={fpsQuality === 'production'}
                    onChange={(e) => setFpsQuality(e.target.value as any)}
                    style={{ marginRight: '4px' }}
                  />
                  Production (30fps)
                </label>
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="radio"
                    name="fpsQuality"
                    value="high"
                    checked={fpsQuality === 'high'}
                    onChange={(e) => setFpsQuality(e.target.value as any)}
                    style={{ marginRight: '4px' }}
                  />
                  High (60fps)
                </label>
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>
                Canvas Format:
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px', marginBottom: '16px' }}>
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="radio"
                    name="aspectRatio"
                    value="square"
                    checked={aspectRatio === 'square'}
                    onChange={(e) => setAspectRatio(e.target.value as any)}
                    style={{ marginRight: '4px' }}
                  />
                  Square (1:1)
                </label>
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="radio"
                    name="aspectRatio"
                    value="landscape"
                    checked={aspectRatio === 'landscape'}
                    onChange={(e) => setAspectRatio(e.target.value as any)}
                    style={{ marginRight: '4px' }}
                  />
                  Landscape (16:9)
                </label>
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="radio"
                    name="aspectRatio"
                    value="portrait"
                    checked={aspectRatio === 'portrait'}
                    onChange={(e) => setAspectRatio(e.target.value as any)}
                    style={{ marginRight: '4px' }}
                  />
                  Portrait (9:16)
                </label>
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="radio"
                    name="aspectRatio"
                    value="instagram_story"
                    checked={aspectRatio === 'instagram_story'}
                    onChange={(e) => setAspectRatio(e.target.value as any)}
                    style={{ marginRight: '4px' }}
                  />
                  Story (9:16)
                </label>
                <label style={{ display: 'flex', alignItems: 'center' }}>
                  <input
                    type="radio"
                    name="aspectRatio"
                    value="instagram_post"
                    checked={aspectRatio === 'instagram_post'}
                    onChange={(e) => setAspectRatio(e.target.value as any)}
                    style={{ marginRight: '4px' }}
                  />
                  Post (4:5)
                </label>
              </div>
              
              
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                <label style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  <input
                    type="checkbox"
                    checked={showPlacementAnimation}
                    onChange={(e) => setShowPlacementAnimation(e.target.checked)}
                    style={{ marginRight: '8px' }}
                  />
                  Placement Animation
                </label>
                {showPlacementAnimation && (
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={placementPercentage}
                    onChange={(e) => setPlacementPercentage(parseInt(e.target.value))}
                    style={{
                      width: '60px',
                      padding: '4px',
                      border: '1px solid var(--border)',
                      borderRadius: '4px',
                      marginLeft: '8px'
                    }}
                  />
                )}
                {showPlacementAnimation && <span style={{ marginLeft: '4px' }}>%</span>}
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                <label style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  <input
                    type="checkbox"
                    checked={showSeparationAnimation}
                    onChange={(e) => setShowSeparationAnimation(e.target.checked)}
                    style={{ marginRight: '8px' }}
                  />
                  Separation Animation
                </label>
                {showSeparationAnimation && (
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={separationPercentage}
                    onChange={(e) => setSeparationPercentage(parseInt(e.target.value))}
                    style={{
                      width: '60px',
                      padding: '4px',
                      border: '1px solid var(--border)',
                      borderRadius: '4px',
                      marginLeft: '8px'
                    }}
                  />
                )}
                {showSeparationAnimation && <span style={{ marginLeft: '4px' }}>%</span>}
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                <label style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  <input
                    type="checkbox"
                    checked={showRotationAnimation}
                    onChange={(e) => setShowRotationAnimation(e.target.checked)}
                    style={{ marginRight: '8px' }}
                  />
                  Rotation Animation
                </label>
                {showRotationAnimation && (
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={rotationPercentage}
                    onChange={(e) => setRotationPercentage(parseInt(e.target.value))}
                    style={{
                      width: '60px',
                      padding: '4px',
                      border: '1px solid var(--border)',
                      borderRadius: '4px',
                      marginLeft: '8px'
                    }}
                  />
                )}
                {showRotationAnimation && <span style={{ marginLeft: '4px' }}>%</span>}
                {showRotationAnimation && (
                  <input
                    type="number"
                    min="0"
                    max="10"
                    step="0.5"
                    value={rotations}
                    onChange={(e) => setRotations(parseFloat(e.target.value))}
                    style={{
                      width: '60px',
                      padding: '4px',
                      border: '1px solid var(--border)',
                      borderRadius: '4px',
                      marginLeft: '8px'
                    }}
                  />
                )}
                {showRotationAnimation && <span style={{ marginLeft: '4px', fontSize: '0.9em' }}>rot</span>}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button 
                className="button" 
                onClick={() => setShowMovieDialog(false)}
                style={{ backgroundColor: 'var(--border)' }}
              >
                Cancel
              </button>
              <button 
                className="button" 
                onClick={handleCreateMovie}
                disabled={!showPlacementAnimation && !showSeparationAnimation}
              >
                Create Movie
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
