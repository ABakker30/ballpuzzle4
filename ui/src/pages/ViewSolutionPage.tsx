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

  const handleCreateMovie = async (duration: number, showPlacement: boolean, showSeparation: boolean) => {
    if (!viewer3DRef.current || isCreatingMovie) return;
    
    setIsCreatingMovie(true);
    setMovieProgress({ progress: 0, phase: 'Starting...' });
    
    try {
      const movieBlob = await viewer3DRef.current.createMovie(
        duration, 
        showPlacement, 
        showSeparation,
        (progress: number, phase: string) => {
          setMovieProgress({ progress, phase });
        }
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
      console.error('Failed to create movie:', error);
      alert(`Failed to create movie: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsCreatingMovie(false);
      setMovieProgress({ progress: 0, phase: '' });
    }
  };

  return (
    <div style={{ display: 'grid', gap: '16px', height: '100%' }}>
      <h2>View Solution</h2>
      
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
      
      {isCreatingMovie && (
        <div style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          backgroundColor: 'var(--surface)',
          padding: '20px',
          borderRadius: '8px',
          border: '1px solid var(--border)',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          zIndex: 1000,
          minWidth: '400px',
          textAlign: 'center'
        }}>
          <h3>Creating Movie...</h3>
          <p>{movieProgress.phase}</p>
          <div style={{ 
            width: '100%', 
            height: '20px', 
            backgroundColor: 'var(--border)', 
            borderRadius: '10px',
            overflow: 'hidden',
            marginTop: '10px'
          }}>
            <div style={{
              width: `${movieProgress.progress}%`,
              height: '100%',
              backgroundColor: 'var(--accent)',
              transition: 'width 0.3s ease'
            }} />
          </div>
          <p style={{ marginTop: '10px', fontSize: '14px', color: 'var(--muted)' }}>
            {Math.round(movieProgress.progress)}% complete
          </p>
          <p style={{ fontSize: '12px', color: 'var(--muted)' }}>
            Frames are being saved to your selected directory
          </p>
        </div>
      )}
    </div>
  );
};
