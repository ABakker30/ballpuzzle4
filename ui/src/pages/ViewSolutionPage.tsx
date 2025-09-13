import React, { useState, useRef } from 'react';
import { SolutionViewer3D, SolutionViewer3DRef } from '../components/solution/SolutionViewer3D';
import { SolutionToolbar } from '../components/solution/SolutionToolbar';
import { SolutionJson } from '../types/solution';

export const ViewSolutionPage: React.FC = () => {
  const [solution, setSolution] = useState<SolutionJson | null>(null);
  const [maxPlacements, setMaxPlacements] = useState<number>(Infinity);
  const [pieceSpacing, setPieceSpacing] = useState<number>(1.0);
  const [isCreatingMovie, setIsCreatingMovie] = useState(false);
  const [movieProgress, setMovieProgress] = useState({ progress: 0, phase: '' });
  const [movieAbortController, setMovieAbortController] = useState<AbortController | null>(null);
  const viewer3DRef = useRef<SolutionViewer3DRef>(null);
  
  const handleLoadSolution = (solutionData: SolutionJson) => {
    setSolution(solutionData);
    setMaxPlacements(solutionData.placements?.length || 0);
  };

  const handleTakeScreenshot = async () => {
    if (!viewer3DRef.current) return;
    
    try {
      const dataUrl = await viewer3DRef.current.takeScreenshot();
      
      // Convert data URL to blob
      const response = await fetch(dataUrl);
      const blob = await response.blob();
      
      // Use File System Access API if available
      if ('showSaveFilePicker' in window) {
        try {
          const fileHandle = await (window as any).showSaveFilePicker({
            suggestedName: `solution-screenshot-${Date.now()}.png`,
            types: [{
              description: 'PNG Images',
              accept: { 'image/png': ['.png'] }
            }]
          });
          
          const writable = await fileHandle.createWritable();
          await writable.write(blob);
          await writable.close();
          return;
        } catch (err) {
          // User cancelled or error occurred, fall back to download
        }
      }
      
      // Fallback to traditional download
      const link = document.createElement('a');
      link.download = `solution-screenshot-${Date.now()}.png`;
      link.href = dataUrl;
      link.click();
    } catch (error) {
      console.error('Failed to take screenshot:', error);
      alert('Failed to take screenshot. Please try again.');
    }
  };

  const handleStopMovie = () => {
    if (movieAbortController) {
      movieAbortController.abort();
      setMovieAbortController(null);
      setIsCreatingMovie(false);
      setMovieProgress({ progress: 0, phase: '' });
    }
  };

  const handleCreateMovie = async (duration: number, fpsQuality: 'preview' | 'production' | 'high', showPlacement: boolean, placementPercentage: number, showSeparation: boolean, separationPercentage: number, aspectRatio: 'square' | 'landscape' | 'portrait' | 'instagram_story' | 'instagram_post', showRotation: boolean, rotationPercentage: number, rotations: number) => {
    if (!viewer3DRef.current || isCreatingMovie) return;
    
    const abortController = new AbortController();
    setMovieAbortController(abortController);
    setIsCreatingMovie(true);
    setMovieProgress({ progress: 0, phase: 'Starting...' });
    
    try {
      const movieBlob = await viewer3DRef.current.createMovie(
        duration, 
        fpsQuality,
        showPlacement, 
        placementPercentage,
        showSeparation,
        separationPercentage,
        (progress: number, phase: string) => setMovieProgress({ progress, phase }),
        abortController.signal,
        aspectRatio,
        showRotation,
        rotationPercentage,
        rotations
      );
      
      // Use File System Access API if available
      if ('showSaveFilePicker' in window) {
        try {
          const fileHandle = await (window as any).showSaveFilePicker({
            suggestedName: `solution-movie-frames-${Date.now()}.json`,
            types: [{
              description: 'Movie Frame Package',
              accept: { 'application/json': ['.json'] }
            }]
          });
          
          const writable = await fileHandle.createWritable();
          await writable.write(movieBlob);
          await writable.close();
          return;
        } catch (err) {
          // User cancelled or error occurred, fall back to download
        }
      }
      
      // Fallback to traditional download
      const url = URL.createObjectURL(movieBlob);
      const link = document.createElement('a');
      link.download = `solution-movie-frames-${Date.now()}.json`;
      link.href = url;
      link.click();
      
      // Clean up the URL object
      URL.revokeObjectURL(url);
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Movie creation was cancelled by user');
      } else {
        console.error('Failed to create movie:', error);
        alert(`Failed to create movie: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    } finally {
      setIsCreatingMovie(false);
      setMovieProgress({ progress: 0, phase: '' });
      setMovieAbortController(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw' }}>
      
      <SolutionToolbar
        onLoadSolution={handleLoadSolution}
        solution={solution}
        maxPlacements={maxPlacements}
        totalPlacements={solution?.placements?.length || 0}
        onMaxPlacementsChange={setMaxPlacements}
        pieceSpacing={pieceSpacing}
        onPieceSpacingChange={setPieceSpacing}
        onTakeScreenshot={handleTakeScreenshot}
        onCreateMovie={handleCreateMovie}
      />

      <div style={{ flex: 1, width: '100%' }}>
        <SolutionViewer3D
          ref={viewer3DRef}
          solution={solution}
          maxPlacements={maxPlacements}
          brightness={2.0}
          orientToSurface={true}
          pieceSpacing={pieceSpacing}
          onMaxPlacementsChange={setMaxPlacements}
          onPieceSpacingChange={setPieceSpacing}
        />
      </div>
      {isCreatingMovie && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          backgroundColor: 'var(--surface)',
          padding: '16px',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 1000,
          minWidth: '200px',
          textAlign: 'center'
        }}>
          <div style={{ 
            width: '100%', 
            height: '8px', 
            backgroundColor: 'var(--border)', 
            borderRadius: '4px',
            overflow: 'hidden',
            marginBottom: '8px'
          }}>
            <div style={{
              width: `${movieProgress.progress}%`,
              height: '100%',
              backgroundColor: 'var(--accent)',
              transition: 'width 0.3s ease'
            }} />
          </div>
          <p style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '500' }}>
            {Math.round(movieProgress.progress)}% complete
          </p>
          <button 
            onClick={handleStopMovie}
            style={{
              padding: '6px 12px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};
