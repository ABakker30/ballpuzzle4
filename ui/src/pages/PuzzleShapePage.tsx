import React, { useState, useRef, useCallback } from 'react';
import * as THREE from 'three';
import { ThreeCanvas, ThreeCanvasRef } from '../components/3d/ThreeCanvas';
import { InstancedSpheres } from '../components/3d/InstancedSpheres';
import { ShapeToolbar } from '../components/shape/ShapeToolbar';
import { ContainerJson, WorldCell, EngineCell } from '../types/shape';
import { engineToWorldInt, worldToEngineInt, keyW, calculateOptimalRadius, parseWorldKey } from '../lib/lattice';
import { Vector3 } from '../lib/fcc';
import { ShapeEditor3D } from '../components/shape/ShapeEditor3D';
import { computeCID } from '../utils/cid';
import '../components/shape/ShapeEditor.css';

export const PuzzleShapePage: React.FC = () => {
  const [container, setContainer] = useState<ContainerJson | null>(null);
  const [worldCells, setWorldCells] = useState<Set<string>>(new Set());
  const [worldPositions, setWorldPositions] = useState<Vector3[]>([]);
  const [worldCellPositions, setWorldCellPositions] = useState<WorldCell[]>([]);
  const [sphereRadius, setSphereRadius] = useState<number>(0.5);
  const [scene, setScene] = useState<THREE.Scene | null>(null);
  const [camera, setCamera] = useState<THREE.PerspectiveCamera | null>(null);
  const [undoStack, setUndoStack] = useState<Array<{type: 'add' | 'remove', cell: WorldCell}>>([]);
  const [redoStack, setRedoStack] = useState<Array<{type: 'add' | 'remove', cell: WorldCell}>>([]);
  const [liveCID, setLiveCID] = useState<string>('');
  const [brightness] = useState<number>(4.0);
  const canvasRef = useRef<ThreeCanvasRef>(null);

  const handleLoadContainer = useCallback((newContainer: ContainerJson) => {
    console.log('Loading container:', newContainer);
    setContainer(newContainer);

    // Convert Engine coordinates to World-int coordinates
    const worldCellSet = new Set<string>();
    const positions: Vector3[] = [];
    const worldCellArray: WorldCell[] = [];

    if (newContainer.coordinates) {
      newContainer.coordinates.forEach(([i, j, k]) => {
        if (Array.isArray([i, j, k]) && [i, j, k].length === 3) {
          const worldCell = engineToWorldInt(i, j, k);
          const key = keyW(worldCell.X, worldCell.Y, worldCell.Z);
          worldCellSet.add(key);
          worldCellArray.push(worldCell);
          
          // Convert to render positions (scaled by viewer scale)
          positions.push({
            x: worldCell.X,
            y: worldCell.Y,
            z: worldCell.Z
          });
        }
      });
    }
    
    // Calculate optimal sphere radius
    const optimalRadius = calculateOptimalRadius(worldCellArray);
    console.log(`Calculated optimal sphere radius: ${optimalRadius}`);
    
    console.log(`Converted ${positions.length} Engine coordinates to World positions`);
    setWorldCells(worldCellSet);
    setWorldPositions(positions);
    setWorldCellPositions(worldCellArray);
    setSphereRadius(optimalRadius);

    // Auto-fit view to new container and set pivot to center
    if (canvasRef.current && positions.length > 0) {
      const bounds = new THREE.Box3();
      positions.forEach(pos => {
        bounds.expandByPoint(new THREE.Vector3(pos.x, pos.y, pos.z));
      });
      const center = bounds.getCenter(new THREE.Vector3());
      canvasRef.current.setTarget(center);
      canvasRef.current.fit(bounds);
    }
  }, []);

  const handleFitView = useCallback(() => {
    if (canvasRef.current && worldPositions.length > 0) {
      const bounds = new THREE.Box3();
      worldPositions.forEach(pos => {
        bounds.expandByPoint(new THREE.Vector3(pos.x, pos.y, pos.z));
      });
      canvasRef.current.fit(bounds);
    }
  }, [worldPositions]);

  const handleResetView = useCallback(() => {
    if (canvasRef.current) {
      // Reset to default view
      const bounds = new THREE.Box3(
        new THREE.Vector3(-5, -5, -5),
        new THREE.Vector3(5, 5, 5)
      );
      canvasRef.current.fit(bounds);
    }
  }, []);

  const handleThreeReady = useCallback((context: {
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    controls: any;
    renderer: THREE.WebGLRenderer;
  }) => {
    setScene(context.scene);
    setCamera(context.camera);
  }, []);

  // Update lighting brightness when brightness prop changes
  React.useEffect(() => {
    if (!scene) return;
    
    scene.traverse((child) => {
      if (child instanceof THREE.Light) {
        // Reset to base intensity then apply brightness multiplier
        if (child instanceof THREE.AmbientLight) {
          child.intensity = 1.2 * brightness;
        } else if (child instanceof THREE.DirectionalLight) {
          // Different base intensities for different lights
          if (child.position.length() > 12) { // Main directional light
            child.intensity = 0.8 * brightness;
          } else if (child.position.length() > 8) { // Fill lights
            child.intensity = 0.4 * brightness;
          } else { // Other fill lights
            child.intensity = 0.3 * brightness;
          }
        }
      }
    });
  }, [scene, brightness]);

  const computeLiveCID = useCallback(async (cells: WorldCell[]) => {
    const engineCells: EngineCell[] = [];
    
    cells.forEach(cell => {
      const engineCell = worldToEngineInt(cell.X, cell.Y, cell.Z);
      if (engineCell) {
        engineCells.push(engineCell);
      }
    });
    
    if (engineCells.length > 0) {
      const cid = await computeCID(engineCells);
      setLiveCID(cid);
    }
  }, []);

  const updateCellsOnly = useCallback((newCells: WorldCell[]) => {
    // Update positions for rendering
    const positions: Vector3[] = [];
    const worldCellSet = new Set<string>();
    
    newCells.forEach(cell => {
      const key = keyW(cell.X, cell.Y, cell.Z);
      worldCellSet.add(key);
      positions.push({ x: cell.X, y: cell.Y, z: cell.Z });
    });
    
    // Calculate dynamic sphere radius based on closest distance between points
    let calculatedRadius = 0.5; // Default fallback
    if (newCells.length > 1) {
      let minDistance = Infinity;
      
      for (let i = 0; i < newCells.length; i++) {
        for (let j = i + 1; j < newCells.length; j++) {
          const cell1 = newCells[i];
          const cell2 = newCells[j];
          const distance = Math.sqrt(
            Math.pow(cell1.X - cell2.X, 2) +
            Math.pow(cell1.Y - cell2.Y, 2) +
            Math.pow(cell1.Z - cell2.Z, 2)
          );
          minDistance = Math.min(minDistance, distance);
        }
      }
      
      if (minDistance !== Infinity) {
        calculatedRadius = minDistance / 2;
        console.log(`Calculated sphere radius: ${calculatedRadius} (min distance: ${minDistance})`);
      }
    }
    
    setSphereRadius(calculatedRadius);
    setWorldCells(worldCellSet);
    setWorldPositions(positions);
    setWorldCellPositions(newCells);
    
    // Compute live CID
    computeLiveCID(newCells);
  }, [computeLiveCID]);

  React.useEffect(() => {
    updateCellsOnly(worldCellPositions);
  }, [worldCellPositions, updateCellsOnly]);

  React.useEffect(() => {
    if (worldCells.size === 0) {
      setLiveCID('');
      return;
    }

    const updateCID = async () => {
      const engineCells: EngineCell[] = [];
      
      worldCells.forEach(key => {
        const worldCell = parseWorldKey(key);
        const engineCell = worldToEngineInt(worldCell.X, worldCell.Y, worldCell.Z);
        if (engineCell) {
          engineCells.push(engineCell);
        }
      });
      
      if (engineCells.length > 0) {
        const cid = await computeCID(engineCells);
        setLiveCID(cid);
      }
    };
    
    updateCID();
  }, [worldCells]);

  // Cell editing handlers
  const handleAddCell = useCallback((cell: WorldCell) => {
    console.log('=== HANDLE ADD CELL CALLED ===');
    console.log('Adding cell:', cell);
    console.log('Current worldCells size:', worldCells.size);
    console.log('Current worldCellPositions length:', worldCellPositions.length);
    
    const key = keyW(cell.X, cell.Y, cell.Z);
    console.log('Cell key:', key);
    console.log('Cell already exists:', worldCells.has(key));
    
    if (!worldCells.has(key)) {
      const newCells = [...worldCellPositions, cell];
      console.log('New cells array length:', newCells.length);
      setWorldCellPositions(newCells);
      updateCellsOnly(newCells);
      setUndoStack(prev => [...prev, { type: 'remove', cell }]);
      setRedoStack([]);
    }
  }, [worldCells, worldCellPositions, updateCellsOnly]);

  const handleRemoveCell = useCallback((cell: WorldCell) => {
    console.log('=== HANDLE REMOVE CELL CALLED ===');
    console.log('Removing cell:', cell);
    console.log('Current worldCells size:', worldCells.size);
    console.log('Current worldCellPositions length:', worldCellPositions.length);
    
    const key = keyW(cell.X, cell.Y, cell.Z);
    console.log('Cell key:', key);
    console.log('Cell exists:', worldCells.has(key));
    
    if (worldCells.has(key)) {
      const newCells = worldCellPositions.filter(c => 
        !(c.X === cell.X && c.Y === cell.Y && c.Z === cell.Z)
      );
      console.log('New cells array length:', newCells.length);
      setWorldCellPositions(newCells);
      updateCellsOnly(newCells);
      setUndoStack(prev => [...prev, { type: 'add', cell }]);
      setRedoStack([]);
    }
  }, [worldCells, worldCellPositions, updateCellsOnly]);

  const handleToggleCell = useCallback((cell: WorldCell) => {
    const key = keyW(cell.X, cell.Y, cell.Z);
    if (worldCells.has(key)) {
      handleRemoveCell(cell);
    } else {
      handleAddCell(cell);
    }
  }, [worldCells, handleAddCell, handleRemoveCell]);

  // Undo/Redo handlers
  const handleUndo = useCallback(() => {
    if (undoStack.length === 0) return;
    
    const lastAction = undoStack[undoStack.length - 1];
    const key = keyW(lastAction.cell.X, lastAction.cell.Y, lastAction.cell.Z);
    
    if (lastAction.type === 'add') {
      setWorldCells(prev => new Set([...prev, key]));
    } else {
      setWorldCells(prev => {
        const newSet = new Set(prev);
        newSet.delete(key);
        return newSet;
      });
    }
    
    setUndoStack(prev => prev.slice(0, -1));
    setRedoStack(prev => [...prev, lastAction]);
  }, [undoStack]);

  const handleRedo = useCallback(() => {
    if (redoStack.length === 0) return;
    
    const lastAction = redoStack[redoStack.length - 1];
    const key = keyW(lastAction.cell.X, lastAction.cell.Y, lastAction.cell.Z);
    
    if (lastAction.type === 'remove') {
      setWorldCells(prev => {
        const newSet = new Set(prev);
        newSet.delete(key);
        return newSet;
      });
    } else {
      setWorldCells(prev => new Set([...prev, key]));
    }
    
    setRedoStack(prev => prev.slice(0, -1));
    setUndoStack(prev => [...prev, lastAction]);
  }, [redoStack]);

  // Save as new handler
  const handleClear = useCallback(() => {
    // Clear all cell data
    setWorldCells(new Set());
    setWorldPositions([]);
    setWorldCellPositions([]);
    setUndoStack([]);
    setRedoStack([]);
    setLiveCID('');
    
    console.log('Cleared all cells');
  }, []);

  const handleSaveAsNew = useCallback(async () => {
    if (worldCells.size === 0) return;
    
    // Convert World cells back to Engine coordinates
    const engineCells: EngineCell[] = [];
    
    for (const cellKey of worldCells) {
      const [x, y, z] = cellKey.split(',').map(Number);
      const engineCell = worldToEngineInt(x, y, z);
      if (engineCell) {
        engineCells.push(engineCell);
      }
    }
    
    // Sort for consistent output
    engineCells.sort((a, b) => {
      if (a.i !== b.i) return a.i - b.i;
      if (a.j !== b.j) return a.j - b.j;
      return a.k - b.k;
    });
    
    const cid = await computeCID(engineCells);
    const containerData: ContainerJson = {
      cid,
      cells: engineCells.length,
      lattice: 'fcc',
      coords: engineCells
    };
    
    const jsonContent = JSON.stringify(containerData, null, 2);
    const defaultFilename = `container_${cid.slice(6, 14)}.json`;
    
    // Try File System Access API first (modern browsers)
    if ('showSaveFilePicker' in window) {
      try {
        const fileHandle = await (window as any).showSaveFilePicker({
          suggestedName: defaultFilename,
          types: [{
            description: 'JSON files',
            accept: { 'application/json': ['.json'] }
          }]
        });
        
        const writable = await fileHandle.createWritable();
        await writable.write(jsonContent);
        await writable.close();
        return;
      } catch (error) {
        // User cancelled or error occurred, fall back to download
        if ((error as Error).name !== 'AbortError') {
          console.warn('File System Access API failed:', error);
        }
      }
    }
    
    // Fallback: automatic download
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = defaultFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [worldCells]);

  const containerName = container?.cid || container?.name || 'Unknown';
  const cellCount = worldCells.size;

  return (
    <div className="puzzle-shape-page">
      <div className="shape-header">
        <h1>Puzzle Shape</h1>
        <ShapeToolbar
          containerName={containerName}
          cellCount={cellCount}
          onLoadContainer={handleLoadContainer}
          onFitView={handleFitView}
          onResetView={handleResetView}
          onSaveAsNew={handleSaveAsNew}
          onClear={handleClear}
          liveCID={liveCID}
          canSave={cellCount % 4 === 0}
        />
      </div>
      
      <div className="shape-viewer">
        <ThreeCanvas
          ref={canvasRef}
          onReady={handleThreeReady}
        >
          {scene && (
            <ShapeEditor3D
              cells={worldCellPositions}
              radius={sphereRadius}
              scene={scene}
              camera={camera}
              onAdd={handleAddCell}
              onRemove={handleRemoveCell}
              onRequestFit={() => {}}
            />
          )}
        </ThreeCanvas>
      </div>
    </div>
  );
};
