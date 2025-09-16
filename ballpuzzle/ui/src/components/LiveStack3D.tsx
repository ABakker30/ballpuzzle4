import React, { useState, useRef, useMemo, useEffect } from 'react';
import { ThreeCanvas, ThreeCanvasRef } from './3d/ThreeCanvas';
import { InstancedSpheres } from './3d/InstancedSpheres';
import { StatusData, PlacedPiece } from '../types/status';
import { useStatus } from '../hooks/useStatus';
import { fccToWorld, Vector3 } from '../lib/fcc';
import * as THREE from 'three';

export const LiveStack3D: React.FC = () => {
  const { data, error } = useStatus();
  const [follow, setFollow] = useState(true);
  const [latticeScale, setLatticeScale] = useState(1);
  const [fullPieceMode, setFullPieceMode] = useState(false);
  const [scene, setScene] = useState<THREE.Scene | null>(null);
  const canvasRef = useRef<ThreeCanvasRef>(null);
  const hasAutoFittedRef = useRef(false);

  // Calculate sphere positions from v2 placed pieces
  const sphereData = useMemo(() => {
    const safeReturn = { positions: [], colors: [], count: 0 };
    
    console.log('LiveStack3D: Processing v2 data:', JSON.stringify(data, null, 2));
    
    if (data?.version !== 2) {
      console.log('LiveStack3D: Expected v2 format, got version:', data?.version);
      return safeReturn;
    }
    
    if (!data?.stack || !Array.isArray(data.stack)) {
      console.log('LiveStack3D: No stack data or not array. Stack:', data?.stack);
      console.log('LiveStack3D: Full data keys:', Object.keys(data || {}));
      return safeReturn;
    }
    
    console.log('LiveStack3D: Stack has', data.stack.length, 'items');
    if (data.stack.length > 0) {
      console.log('LiveStack3D: First stack item:', JSON.stringify(data.stack[0], null, 2));
    }
    
    try {
      const positions: Vector3[] = [];
      const colors: Vector3[] = [];
      
      if (fullPieceMode) {
        // Show all cells for each piece
        data.stack.forEach((placedPiece: PlacedPiece) => {
          if (!placedPiece.cells || !Array.isArray(placedPiece.cells)) {
            console.log('LiveStack3D: Piece missing cells array:', placedPiece);
            return;
          }
          placedPiece.cells.forEach((cell) => {
            if (typeof cell.i === 'number' && typeof cell.j === 'number' && typeof cell.k === 'number') {
              const worldPos = fccToWorld(cell.i, cell.j, cell.k, latticeScale);
              positions.push(worldPos);
              
              // Color by piece type using instance_id for consistency
              const hue = (placedPiece.instance_id * 137.5) % 360;
              const color = new THREE.Color().setHSL(hue / 360, 0.7, 0.6);
              colors.push({ x: color.r, y: color.g, z: color.b });
            }
          });
        });
      } else {
        // Show only anchor positions (first cell per piece)
        data.stack.forEach((placedPiece: PlacedPiece) => {
          if (!placedPiece.cells || !Array.isArray(placedPiece.cells) || placedPiece.cells.length === 0) {
            console.log('LiveStack3D: Piece missing cells array or empty:', placedPiece);
            return;
          }
          const anchor = placedPiece.cells[0];
          if (typeof anchor.i === 'number' && typeof anchor.j === 'number' && typeof anchor.k === 'number') {
            const worldPos = fccToWorld(anchor.i, anchor.j, anchor.k, latticeScale);
            positions.push(worldPos);
            
            // Color by piece type using instance_id for consistency
            const hue = (placedPiece.instance_id * 137.5) % 360;
            const color = new THREE.Color().setHSL(hue / 360, 0.7, 0.6);
            colors.push({ x: color.r, y: color.g, z: color.b });
          }
        });
      }
      
      console.log('LiveStack3D: Generated', positions.length, 'positions:', positions);
      return { positions, colors, count: positions.length };
    } catch (error) {
      console.error('LiveStack3D: Error processing sphere data', error);
      return safeReturn;
    }
  }, [data?.stack, fullPieceMode, latticeScale]);

  // Add spheres to scene when data changes
  useEffect(() => {
    console.log('LiveStack3D: useEffect triggered - scene:', !!scene, 'sphereData.count:', sphereData.count);
    
    if (!scene) {
      console.log('LiveStack3D: No scene available yet');
      return;
    }
    
    if (sphereData.count === 0) {
      console.log('LiveStack3D: No sphere data to render');
      return;
    }

    // Clear existing spheres
    const existingSpheres = scene.children.filter(child => child.userData.isSphere);
    console.log('LiveStack3D: Removing', existingSpheres.length, 'existing spheres');
    existingSpheres.forEach(sphere => scene.remove(sphere));

    // Add new spheres
    const geometry = new THREE.SphereGeometry(0.2, 16, 12); // Slightly larger spheres
    
    sphereData.positions.forEach((pos, index) => {
      const color = sphereData.colors[index] 
        ? new THREE.Color(sphereData.colors[index].x, sphereData.colors[index].y, sphereData.colors[index].z) 
        : new THREE.Color(0x4a90e2);
        
      const material = new THREE.MeshStandardMaterial({
        color: color,
        metalness: 0.1,
        roughness: 0.3,
      });
      
      const sphere = new THREE.Mesh(geometry, material);
      sphere.position.set(pos.x, pos.y, pos.z);
      sphere.userData.isSphere = true;
      sphere.castShadow = true;
      sphere.receiveShadow = true;
      scene.add(sphere);
      
      console.log(`LiveStack3D: Added sphere ${index} at position (${pos.x.toFixed(2)}, ${pos.y.toFixed(2)}, ${pos.z.toFixed(2)}) with color`, color);
    });

    console.log('LiveStack3D: Added', sphereData.count, 'spheres to scene. Total scene children:', scene.children.length);
  }, [scene, sphereData]);

  // Auto-fit on first non-empty stack
  useEffect(() => {
    if (!follow || !canvasRef.current || sphereData.count === 0) return;

    if (!hasAutoFittedRef.current && sphereData.count > 0) {
      const bounds = new THREE.Box3();
      sphereData.positions.forEach((pos: Vector3) => {
        bounds.expandByPoint(new THREE.Vector3(pos.x, pos.y, pos.z));
      });
      bounds.expandByScalar(2);
      canvasRef.current.fit(bounds);
      hasAutoFittedRef.current = true;
    }
  }, [sphereData.count, follow]);

  const handleFit = () => {
    if (!canvasRef.current || sphereData.positions.length === 0) return;
    
    const bounds = new THREE.Box3();
    sphereData.positions.forEach((pos: Vector3) => {
      bounds.expandByPoint(new THREE.Vector3(pos.x, pos.y, pos.z));
    });
    bounds.expandByScalar(2);
    canvasRef.current.fit(bounds);
  };

  // Handle error and loading states after all hooks
  if (error) {
    return <div className="text-red-500">Status Error: {error}</div>;
  }

  if (!data) {
    return <div className="text-gray-500">Loading status...</div>;
  }

  const stackLength = data?.stack?.length || 0;
  const isStackTruncated = data?.stack_truncated || false;

  return (
    <div className="viewer-card">
      <div className="viewer-head">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <strong>Live 3D (stack)</strong>
          {isStackTruncated && (
            <span className="badge note">showing tail</span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <label htmlFor="full-piece-mode" style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.875rem' }}>
            <input
              id="full-piece-mode"
              name="fullPieceMode"
              type="checkbox"
              checked={fullPieceMode}
              onChange={(e) => setFullPieceMode(e.target.checked)}
            />
            Full pieces
          </label>
          <label htmlFor="follow-mode" style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.875rem' }}>
            <input
              id="follow-mode"
              name="follow"
              type="checkbox"
              checked={follow}
              onChange={(e) => setFollow(e.target.checked)}
            />
            Follow
          </label>
          <button onClick={handleFit} style={{ padding: '4px 8px', fontSize: '0.75rem' }}>
            Fit
          </button>
        </div>
      </div>
      <div className="viewer-body" style={{ height: '400px', width: '100%', position: 'relative' }}>
        <div style={{ width: '100%', height: '100%', border: '1px solid #ccc' }}>
          <ThreeCanvas 
            ref={canvasRef} 
            onReady={({ scene, camera, renderer }) => {
              setScene(scene);
              // Position camera to see the origin area
              camera.position.set(5, 5, 5);
              camera.lookAt(0, 0, 0);
              
              console.log('LiveStack3D: Scene setup complete');
              console.log('- Camera position:', camera.position);
              console.log('- Renderer size:', renderer.getSize(new THREE.Vector2()));
            }}
          />
        </div>
        {stackLength > 0 && (
          <div style={{
            marginTop: 8, 
            fontSize: '0.75rem', 
            color: 'var(--muted)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span>
              {stackLength} piece{stackLength !== 1 ? 's' : ''} placed
              {fullPieceMode && ` (${sphereData.count} atoms)`}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <label htmlFor="scale-slider" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                Scale:
                <input
                  id="scale-slider"
                  name="latticeScale"
                  type="range"
                  min="0.5"
                  max="3"
                  step="0.1"
                  value={latticeScale}
                  onChange={(e) => setLatticeScale(parseFloat(e.target.value))}
                  style={{ width: 60 }}
                />
                <span style={{ minWidth: 24, textAlign: 'right' }}>
                  {latticeScale.toFixed(1)}
                </span>
              </label>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
