import React, { useEffect, useRef, useState } from 'react';
import { ThreeCanvas, ThreeCanvasRef } from '../3d/ThreeCanvas';
import { InstancedSpheres } from '../3d/InstancedSpheres';
import { engineToWorldInt } from '../../lib/lattice';
import { SolutionJson, Placement } from '../../types/solution';
import * as THREE from 'three';

interface SolutionViewer3DProps {
  solution: SolutionJson | null;
  maxPlacements?: number;
  brightness?: number;
}

// Generate PBR paint colors for pieces A-Z - professional paint palette
const generatePieceColors = (): Record<string, string> => {
  const colors: Record<string, string> = {};
  
  // ColorBrewer qualitative palette - scientifically designed for maximum distinction
  const pbrPaintColors = [
    '#e41a1c', // Red (A)
    '#377eb8', // Blue (B)
    '#4daf4a', // Green (C)
    '#984ea3', // Purple (D)
    '#ff7f00', // Orange (E)
    '#ffff33', // Yellow (F)
    '#a65628', // Brown (G)
    '#f781bf', // Pink (H)
    '#999999', // Gray (I)
    '#66c2a5', // Teal (J)
    '#fc8d62', // Salmon (K)
    '#8da0cb', // Lavender (L)
    '#e78ac3', // Light Pink (M)
    '#a6d854', // Light Green (N)
    '#ffd92f', // Gold (O)
    '#e5c494', // Beige (P)
    '#b3b3b3', // Light Gray (Q)
    '#8dd3c7', // Mint (R)
    '#ffffb3', // Pale Yellow (S)
    '#bebada', // Pale Purple (T)
    '#fb8072', // Light Red (U)
    '#80b1d3', // Light Blue (V)
    '#fdb462', // Peach (W)
    '#b3de69', // Lime (X)
    '#fccde5', // Very Light Pink (Y)
    '#d9d9d9'  // Very Light Gray (Z)
  ];
  
  for (let i = 0; i < 26; i++) {
    const piece = String.fromCharCode(65 + i); // A-Z
    colors[piece] = pbrPaintColors[i] || `hsl(${i * 14}, 75%, 50%)`;
  }
  
  return colors;
};

const PIECE_COLORS = generatePieceColors();

export const SolutionViewer3D: React.FC<SolutionViewer3DProps> = ({ 
  solution, 
  maxPlacements = Infinity,
  brightness = 1.0
}) => {
  const canvasRef = useRef<ThreeCanvasRef>(null);
  const [sphereGroups, setSphereGroups] = useState<Array<{
    positions: Float32Array;
    colors: Float32Array;
    piece: string;
    radius: number;
  }>>([]);
  const [scene, setScene] = useState<THREE.Scene | null>(null);
  const [camera, setCamera] = useState<THREE.PerspectiveCamera | null>(null);
  const [cameraInitialized, setCameraInitialized] = useState<boolean>(false);

  const handleThreeReady = (context: { scene: THREE.Scene; camera: THREE.PerspectiveCamera; controls: any; renderer: THREE.WebGLRenderer }) => {
    setScene(context.scene);
    setCamera(context.camera);
  };

  // Update lighting brightness when brightness prop changes
  useEffect(() => {
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

  useEffect(() => {
    if (!solution || !solution.placements) {
      console.log('SolutionViewer3D: No solution or placements');
      setSphereGroups([]);
      return;
    }

    console.log('SolutionViewer3D: Processing solution with', solution.placements.length, 'placements');
    const pieceGroups: Record<string, Array<{ x: number; y: number; z: number }>> = {};
    const allWorldCells: Array<{ x: number; y: number; z: number }> = [];
    
    const placementsToShow = solution.placements.slice(0, maxPlacements);
    console.log('SolutionViewer3D: Showing', placementsToShow.length, 'placements');
    
    for (const placement of placementsToShow) {
      const piece = placement.piece;
      console.log('SolutionViewer3D: Processing piece', piece, placement);
      
      if (!pieceGroups[piece]) {
        pieceGroups[piece] = [];
      }
      
      // Extract coordinates from placement
      let coordinates: number[][] = [];
      
      if (placement.coordinates) {
        // Modern format with coordinates array
        coordinates = placement.coordinates;
        console.log('SolutionViewer3D: Using coordinates field');
      } else if ((placement as any).cells_ijk) {
        // Actual solution format with full piece coordinates
        coordinates = (placement as any).cells_ijk;
        console.log('SolutionViewer3D: Using cells_ijk field:', coordinates);
      } else if (placement.t) {
        // Fallback: use translation/anchor point only
        coordinates = [placement.t];
        console.log('SolutionViewer3D: Using t field as anchor');
      } else if (placement.anchor || (placement.i !== undefined && placement.j !== undefined && placement.k !== undefined)) {
        // Legacy format with anchor point
        const anchor = placement.anchor || [placement.i!, placement.j!, placement.k!];
        coordinates = [anchor];
        console.log('SolutionViewer3D: Using legacy anchor format');
      } else {
        console.warn('SolutionViewer3D: No coordinate data found for placement:', placement);
      }
      
      // Convert engine coordinates to world coordinates
      console.log('SolutionViewer3D: Converting coordinates for piece', piece, ':', coordinates);
      for (const coord of coordinates) {
        const [i, j, k] = coord;
        const worldCell = engineToWorldInt(i, j, k);
        console.log('SolutionViewer3D: Engine coord [', i, j, k, '] -> World coord [', worldCell.X, worldCell.Y, worldCell.Z, ']');
        if (worldCell) {
          const worldPos = {
            x: worldCell.X,
            y: worldCell.Y,
            z: worldCell.Z
          };
          pieceGroups[piece].push(worldPos);
          allWorldCells.push(worldPos);
        }
      }
    }
    
    // Convert to sphere groups
    console.log('SolutionViewer3D: Final piece groups:', pieceGroups);
    const groups = Object.entries(pieceGroups).map(([piece, cells]) => {
      console.log('SolutionViewer3D: Creating sphere group for piece', piece, 'with', cells.length, 'spheres');
      const positions = new Float32Array(cells.length * 3);
      const colors = new Float32Array(cells.length * 3);
      
      const hexColor = PIECE_COLORS[piece] || '#888888';
      const color = new THREE.Color(hexColor);
      
      console.log(`SolutionViewer3D: Piece ${piece} using color ${hexColor}, THREE.Color:`, color);
      
      cells.forEach((cell, i) => {
        positions[i * 3] = cell.x;
        positions[i * 3 + 1] = cell.y;
        positions[i * 3 + 2] = cell.z;
        
        colors[i * 3] = color.r;
        colors[i * 3 + 1] = color.g;
        colors[i * 3 + 2] = color.b;
      });
      
      // Debug: log the actual RGB values being set
      console.log(`SolutionViewer3D: Piece ${piece} RGB values:`, [color.r, color.g, color.b]);
      return { positions, colors, piece };
    });
    
    // Calculate optimal sphere radius based on minimum distance between world cells
    let optimalRadius = 0.3; // default
    if (allWorldCells.length >= 2) {
      let minDistance = Infinity;
      console.log('SolutionViewer3D: All world cells for distance calculation:', allWorldCells);
      
      for (let i = 0; i < allWorldCells.length; i++) {
        for (let j = i + 1; j < allWorldCells.length; j++) {
          const dx = allWorldCells[i].x - allWorldCells[j].x;
          const dy = allWorldCells[i].y - allWorldCells[j].y;
          const dz = allWorldCells[i].z - allWorldCells[j].z;
          const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
          console.log(`SolutionViewer3D: Distance between [${allWorldCells[i].x},${allWorldCells[i].y},${allWorldCells[i].z}] and [${allWorldCells[j].x},${allWorldCells[j].y},${allWorldCells[j].z}] = ${distance}`);
          
          if (distance < minDistance && distance > 0) {
            minDistance = distance;
          }
        }
      }
      
      // For FCC lattice, nearest neighbors should be at distance sqrt(2) ≈ 1.414
      // Use 50% of minimum distance so spheres touch but don't overlap
      optimalRadius = Math.max(0.1, minDistance * 0.5);
      console.log('SolutionViewer3D: Calculated optimal radius:', optimalRadius, 'from min distance:', minDistance);
      console.log('SolutionViewer3D: Expected FCC nearest neighbor distance should be ~1.414 for unit lattice');
      console.log('SolutionViewer3D: Using 50% of min distance so spheres touch exactly');
    }

    // Add radius to all groups
    const groupsWithRadius = groups.map(group => ({ ...group, radius: optimalRadius }));
    
    console.log('SolutionViewer3D: Setting sphere groups:', groupsWithRadius);
    setSphereGroups(groupsWithRadius);
  }, [solution, maxPlacements]);

  // Separate effect for initial camera positioning - only runs when solution changes
  useEffect(() => {
    if (!solution || !solution.placements || cameraInitialized || !canvasRef.current) {
      return;
    }

    // Calculate bounds from full solution (not filtered by maxPlacements)
    const bounds = new THREE.Box3();
    const pieceGroups: Record<string, Array<{ x: number; y: number; z: number }>> = {};
    
    for (const placement of solution.placements) {
      const piece = placement.piece;
      if (!pieceGroups[piece]) {
        pieceGroups[piece] = [];
      }

      const coordinates = placement.cells_ijk || [];
      for (const coord of coordinates) {
        const [i, j, k] = coord;
        const worldCell = engineToWorldInt(i, j, k);
        bounds.expandByPoint(new THREE.Vector3(worldCell.X, worldCell.Y, worldCell.Z));
      }
    }
    
    if (!bounds.isEmpty()) {
      console.log('SolutionViewer3D: Setting initial camera position for solution');
      canvasRef.current.fit(bounds);
      setCameraInitialized(true);
    }
  }, [solution, cameraInitialized]);

  // Reset camera initialization when solution changes
  useEffect(() => {
    setCameraInitialized(false);
  }, [solution]);

  return (
    <div style={{ width: '100%', height: '500px', border: '1px solid var(--border)', borderRadius: '8px' }}>
      <ThreeCanvas ref={canvasRef} onReady={handleThreeReady}>
        {scene && sphereGroups.map((group, index) => (
          <InstancedSpheres
            key={`${group.piece}-${index}`}
            positions={group.positions}
            colors={group.colors}
            radius={group.radius || 0.3}
            scene={scene}
          />
        ))}
      </ThreeCanvas>
    </div>
  );
};
