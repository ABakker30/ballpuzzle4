import React, { useRef, useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import * as THREE from 'three';
import { ThreeCanvas, ThreeCanvasRef } from '../3d/ThreeCanvas';
import { UnifiedPiece } from '../3d/UnifiedPiece';
import { SolutionJson, Placement } from '../../types/solution';
import { fccToWorld, pieceColor, keyW, getDirectNeighbors } from '../../lib/fcc';
import { GeometryProcessor, OrientationResult } from '../../lib/geometryProcessor';

interface SolutionViewer3DProps {
  solution: SolutionJson | null;
  maxPlacements: number;
  brightness?: number;
  orientToSurface?: boolean;
  resetTrigger?: number;
  pieceSpacing?: number;
  onMaxPlacementsChange?: (value: number) => void;
  onPieceSpacingChange?: (value: number) => void;
}

export interface SolutionViewer3DRef {
  takeScreenshot: () => Promise<string>;
  createMovie: (duration: number, showPlacement: boolean, showSeparation: boolean, onProgress?: (progress: number, phase: string) => void) => Promise<Blob>;
}

// MPEG creation function using Web APIs
const createMPEGFromFrames = async (frameFiles: { name: string; blob: Blob }[], fps: number): Promise<Blob> => {
  // For browser-based MPEG creation, we'll use a simple approach
  // In a real implementation, you might use FFmpeg.wasm or similar
  
  // Create a ZIP file containing all frames and metadata
  const zipContent: { [filename: string]: Blob } = {};
  
  // Add all frame files
  frameFiles.forEach(frame => {
    zipContent[frame.name] = frame.blob;
  });
  
  // Add metadata file for video conversion
  const metadata = {
    fps,
    frameCount: frameFiles.length,
    format: 'png',
    instructions: 'Use ffmpeg to convert: ffmpeg -framerate ' + fps + ' -i frame_%06d.png -c:v mpeg1video output.mpg'
  };
  
  zipContent['metadata.json'] = new Blob([JSON.stringify(metadata, null, 2)], { type: 'application/json' });
  zipContent['convert.bat'] = new Blob([`ffmpeg -framerate ${fps} -i frame_%06d.png -c:v mpeg1video -q:v 2 movie.mpg`], { type: 'text/plain' });
  zipContent['convert.sh'] = new Blob([`#!/bin/bash\nffmpeg -framerate ${fps} -i frame_%06d.png -c:v mpeg1video -q:v 2 movie.mpg`], { type: 'text/plain' });
  
  // Create a simple ZIP-like structure (for demonstration)
  // In production, you'd use a proper ZIP library or FFmpeg.wasm
  const combinedData = Object.entries(zipContent).map(([name, blob]) => ({
    name,
    size: blob.size,
    type: blob.type
  }));
  
  const result = new Blob([JSON.stringify({
    type: 'movie-frames-package',
    frames: frameFiles.length,
    fps,
    files: combinedData,
    note: 'This package contains video frames. Use FFmpeg or similar tool to create MPEG video.'
  }, null, 2)], { type: 'application/json' });
  
  return result;
};

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

export const SolutionViewer3D = forwardRef<SolutionViewer3DRef, SolutionViewer3DProps>(({
  solution,
  maxPlacements,
  brightness = 1.0,
  orientToSurface = false,
  resetTrigger,
  pieceSpacing = 1.0,
  onMaxPlacementsChange,
  onPieceSpacingChange
}, ref) => {
  const canvasRef = useRef<ThreeCanvasRef>(null);
  const [pieceGroups, setPieceGroups] = useState<Array<{
    piece: string;
    spheres: {
      positions: Float32Array;
      colors: Float32Array;
      radius: number;
    };
    bonds: {
      positions: Float32Array;
      colors: Float32Array;
      radius: number;
    };
  }>>([]);
  const [scene, setScene] = useState<THREE.Scene | null>(null);
  const [camera, setCamera] = useState<THREE.Camera | null>(null);
  const [cameraInitialized, setCameraInitialized] = useState(false);
  const [orientationResult, setOrientationResult] = useState<OrientationResult | null>(null);
  const [originalTransform, setOriginalTransform] = useState<{
    position: THREE.Vector3;
    rotation: THREE.Quaternion;
  } | null>(null);
  const [movieOverrides, setMovieOverrides] = useState<{
    maxPlacements?: number;
    pieceSpacing?: number;
  } | null>(null);
  const [pieceSpacingData, setPieceSpacingData] = useState<{
    pieceCentroids: Record<string, THREE.Vector3>;
    pieceDirections: Record<string, THREE.Vector3>;
    maxRadius: number;
    pivot: THREE.Vector3;
    sphereDiameter: number;
  } | null>(null);
  const geometryProcessor = new GeometryProcessor();

  const handleThreeReady = (context: { scene: THREE.Scene; camera: THREE.PerspectiveCamera; controls: any; renderer: THREE.WebGLRenderer }) => {
    setScene(context.scene);
    setCamera(context.camera);
  };

  // Update lighting brightness when brightness prop changes or scene is ready
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
    
    console.log('SolutionViewer3D: Applied brightness multiplier:', brightness);
  }, [scene, brightness]); // Include scene to apply brightness when scene is first ready

  // Calculate piece spacing data when solution changes
  useEffect(() => {
    if (!solution || !solution.placements || pieceGroups.length === 0) {
      setPieceSpacingData(null);
      return;
    }

    // Calculate piece centroids and directions
    const pieceCentroids: Record<string, THREE.Vector3> = {};
    const pieceDirections: Record<string, THREE.Vector3> = {};
    const pieceSphereCount: Record<string, number> = {};

    // Group placements by piece and calculate centroids
    solution.placements.forEach((placement: Placement) => {
      const piece = placement.piece;
      if (!pieceCentroids[piece]) {
        pieceCentroids[piece] = new THREE.Vector3(0, 0, 0);
        pieceSphereCount[piece] = 0;
      }

      // Extract coordinates from placement - handle different formats
      let coordinates: number[][] = [];
      
      if (placement.coordinates) {
        coordinates = placement.coordinates;
      } else if ((placement as any).cells_ijk) {
        coordinates = (placement as any).cells_ijk;
      } else if (placement.i !== undefined && placement.j !== undefined && placement.k !== undefined) {
        coordinates = [[placement.i, placement.j, placement.k]];
      }

      // Add all coordinates for this piece to centroid calculation
      coordinates.forEach(coord => {
        const worldCoords = fccToWorld(coord[0], coord[1], coord[2]);
        pieceCentroids[piece].add(new THREE.Vector3(worldCoords.x, worldCoords.y, worldCoords.z));
        pieceSphereCount[piece]++;
      });
    });

    // Average to get true centroids
    Object.keys(pieceCentroids).forEach(piece => {
      pieceCentroids[piece].divideScalar(pieceSphereCount[piece]);
      console.log(`Piece ${piece} centroid: [${pieceCentroids[piece].x.toFixed(3)}, ${pieceCentroids[piece].y.toFixed(3)}, ${pieceCentroids[piece].z.toFixed(3)}] (${pieceSphereCount[piece]} spheres)`);
    });

    // Use hull centroid as pivot (from orientation result) or calculate from all spheres
    let pivot = new THREE.Vector3(0, 0, 0);
    if (orientationResult) {
      pivot = orientationResult.hullCentroid.clone();
    } else {
      // Calculate centroid of all spheres
      let totalSpheres = 0;
      Object.keys(pieceCentroids).forEach(piece => {
        pivot.add(pieceCentroids[piece].clone().multiplyScalar(pieceSphereCount[piece]));
        totalSpheres += pieceSphereCount[piece];
      });
      pivot.divideScalar(totalSpheres);
    }

    // Calculate baseline vectors (v_i = c_i - p) and max radius
    let maxRadius = 0;
    console.log('SolutionViewer3D: Calculating baseline vectors from pivot:', pivot.toArray());
    Object.keys(pieceCentroids).forEach(piece => {
      const centroid = pieceCentroids[piece];
      const baselineVector = centroid.clone().sub(pivot); // v_i = c_i - p
      const radius = baselineVector.length();
      
      console.log(`Piece ${piece}: centroid=[${centroid.x.toFixed(3)}, ${centroid.y.toFixed(3)}, ${centroid.z.toFixed(3)}], baseline=[${baselineVector.x.toFixed(3)}, ${baselineVector.y.toFixed(3)}, ${baselineVector.z.toFixed(3)}], radius=${radius.toFixed(3)}`);
      
      if (radius > 0.001) { // Avoid pieces at pivot
        pieceDirections[piece] = baselineVector; // Store full baseline vector, not normalized
        maxRadius = Math.max(maxRadius, radius);
      } else {
        pieceDirections[piece] = new THREE.Vector3(0, 0, 0); // No-move marker
        console.log(`Piece ${piece}: marked as no-move (at pivot)`);
      }
    });

    // Calculate sphere diameter (2 * radius)
    const sphereDiameter = pieceGroups.length > 0 ? pieceGroups[0].spheres.radius * 2 : 0.6;

    setPieceSpacingData({
      pieceCentroids,
      pieceDirections,
      maxRadius,
      pivot,
      sphereDiameter
    });

    console.log('SolutionViewer3D: Calculated piece spacing data:', {
      pieceCount: Object.keys(pieceCentroids).length,
      maxRadius,
      sphereDiameter,
      pivot: pivot.toArray()
    });
  }, [solution, pieceGroups, orientationResult]);

  useEffect(() => {
    if (!solution || !solution.placements) {
      console.log('SolutionViewer3D: No solution or placements');
      setPieceGroups([]);
      return;
    }

    console.log('SolutionViewer3D: Processing solution with', solution.placements.length, 'placements');
    const pieceCells: Record<string, Array<{ x: number; y: number; z: number }>> = {};
    const allWorldCells: Array<{ x: number; y: number; z: number }> = [];
    
    const effectiveMaxPlacements = movieOverrides?.maxPlacements ?? maxPlacements;
    const placementsToShow = solution.placements.slice(0, effectiveMaxPlacements);
    console.log('SolutionViewer3D: Showing', placementsToShow.length, 'placements');
    
    for (const placement of placementsToShow) {
      const piece = placement.piece;
      console.log('SolutionViewer3D: Processing piece', piece, placement);
      
      if (!pieceCells[piece]) {
        pieceCells[piece] = [];
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
        const worldCell = fccToWorld(i, j, k);
        console.log('SolutionViewer3D: Engine coord [', i, j, k, '] -> World coord [', worldCell.x, worldCell.y, worldCell.z, ']');
        if (worldCell) {
          const worldPos = {
            x: worldCell.x,
            y: worldCell.y,
            z: worldCell.z
          };
          pieceCells[piece].push(worldPos);
          allWorldCells.push(worldPos);
        }
      }
    }
    
    // Helper function to find adjacent cells within the same piece
    const findAdjacentCells = (cells: Array<{ x: number; y: number; z: number }>) => {
      const bonds: Array<{ start: { x: number; y: number; z: number }, end: { x: number; y: number; z: number } }> = [];
      
      // Create a set of existing cell positions for fast lookup
      const cellSet = new Set<string>();
      cells.forEach(cell => {
        cellSet.add(keyW(cell.x, cell.y, cell.z));
      });
      
      // For each cell, check all its FCC neighbors
      cells.forEach(cell => {
        const worldCell = { X: cell.x, Y: cell.y, Z: cell.z };
        const neighbors = getDirectNeighbors(worldCell);
        
        neighbors.forEach((neighbor: { X: number; Y: number; Z: number }) => {
          const neighborKey = keyW(neighbor.X, neighbor.Y, neighbor.Z);
          
          // If this neighbor exists in our piece, create a bond
          if (cellSet.has(neighborKey)) {
            // Find the neighbor cell object
            const neighborCell = cells.find(c => 
              c.x === neighbor.X && c.y === neighbor.Y && c.z === neighbor.Z
            );
            
            if (neighborCell) {
              // Avoid duplicate bonds by only adding if current cell comes before neighbor
              const currentKey = keyW(cell.x, cell.y, cell.z);
              if (currentKey < neighborKey) {
                bonds.push({ start: cell, end: neighborCell });
              }
            }
          }
        });
      });
      
      return bonds;
    };

    // Convert to unified piece groups with both spheres and bonds
    console.log('SolutionViewer3D: Final piece cells:', pieceCells);
    const unifiedGroups = Object.entries(pieceCells).map(([piece, cells]) => {
      console.log('SolutionViewer3D: Creating unified group for piece', piece, 'with', cells.length, 'spheres');
      
      // Create sphere data
      const spherePositions = new Float32Array(cells.length * 3);
      const sphereColors = new Float32Array(cells.length * 3);
      
      const hexColor = PIECE_COLORS[piece] || '#888888';
      const color = new THREE.Color(hexColor);
      
      console.log(`SolutionViewer3D: Piece ${piece} using color ${hexColor}, THREE.Color:`, color);
      
      cells.forEach((cell, i) => {
        spherePositions[i * 3] = cell.x;
        spherePositions[i * 3 + 1] = cell.y;
        spherePositions[i * 3 + 2] = cell.z;
        
        sphereColors[i * 3] = color.r;
        sphereColors[i * 3 + 1] = color.g;
        sphereColors[i * 3 + 2] = color.b;
      });
      
      // Create bond data
      const adjacentBonds = findAdjacentCells(cells);
      console.log(`SolutionViewer3D: Found ${adjacentBonds.length} bonds for piece ${piece}`);
      
      let bondPositions = new Float32Array(0);
      let bondColors = new Float32Array(0);
      
      if (adjacentBonds.length > 0) {
        bondPositions = new Float32Array(adjacentBonds.length * 6); // 2 points per bond
        bondColors = new Float32Array(adjacentBonds.length * 3); // 1 color per bond
        
        adjacentBonds.forEach((bond, i) => {
          // Store start and end positions for each bond
          bondPositions[i * 6] = bond.start.x;
          bondPositions[i * 6 + 1] = bond.start.y;
          bondPositions[i * 6 + 2] = bond.start.z;
          bondPositions[i * 6 + 3] = bond.end.x;
          bondPositions[i * 6 + 4] = bond.end.y;
          bondPositions[i * 6 + 5] = bond.end.z;
          
          // Store color for each bond
          bondColors[i * 3] = color.r;
          bondColors[i * 3 + 1] = color.g;
          bondColors[i * 3 + 2] = color.b;
        });
      }
      
      // Debug: log the actual RGB values being set
      console.log(`SolutionViewer3D: Piece ${piece} RGB values:`, [color.r, color.g, color.b]);
      
      return {
        piece,
        spheres: {
          positions: spherePositions,
          colors: sphereColors,
          radius: 0.3 // Will be updated after calculation
        },
        bonds: {
          positions: bondPositions,
          colors: bondColors,
          radius: 0.1 // Will be updated after calculation
        }
      };
    });
    
    // Calculate optimal sphere radius: distance between two points of a piece / 2 in world view
    let optimalRadius = 0.3; // default
    
    // Find minimum distance between any two world cells within the same piece
    let minPieceDistance = Infinity;
    
    unifiedGroups.forEach(group => {
      const sphereCount = group.spheres.positions.length / 3;
      if (sphereCount >= 2) {
        for (let i = 0; i < sphereCount; i++) {
          for (let j = i + 1; j < sphereCount; j++) {
            const x1 = group.spheres.positions[i * 3];
            const y1 = group.spheres.positions[i * 3 + 1];
            const z1 = group.spheres.positions[i * 3 + 2];
            
            const x2 = group.spheres.positions[j * 3];
            const y2 = group.spheres.positions[j * 3 + 1];
            const z2 = group.spheres.positions[j * 3 + 2];
            
            const dx = x1 - x2;
            const dy = y1 - y2;
            const dz = z1 - z2;
            const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
            
            if (distance < minPieceDistance && distance > 0) {
              minPieceDistance = distance;
              console.log(`SolutionViewer3D: Found min distance ${distance} between points in piece ${group.piece}`);
            }
          }
        }
      }
    });
    
    if (minPieceDistance !== Infinity) {
      // Sphere radius = distance between two points of a piece / 2
      optimalRadius = minPieceDistance / 2;
      console.log('SolutionViewer3D: Calculated sphere radius:', optimalRadius, 'from min piece distance:', minPieceDistance);
    } else {
      console.log('SolutionViewer3D: No valid piece distances found, using default radius:', optimalRadius);
    }

    // Update sphere and bond radii with calculated values
    unifiedGroups.forEach(group => {
      group.spheres.radius = optimalRadius;
      group.bonds.radius = optimalRadius * 0.3;
    });

    // Add radius to all groups
    const groupsWithRadius = unifiedGroups.map(group => ({ ...group, radius: optimalRadius }));
    
    console.log('SolutionViewer3D: Setting unified piece groups:', groupsWithRadius);
    console.log('SolutionViewer3D: First group spheres data:', groupsWithRadius[0]?.spheres);
    console.log('SolutionViewer3D: First group bonds data:', groupsWithRadius[0]?.bonds);
    setPieceGroups(groupsWithRadius);

    // Compute orientation if enabled
    if (orientToSurface && groupsWithRadius.length > 0) {
      try {
        // Convert unified groups to format expected by geometryProcessor
        const sphereGroupsForOrientation = groupsWithRadius.map(group => ({
          positions: group.spheres.positions
        }));
        const result = geometryProcessor.computeRestOrientation(sphereGroupsForOrientation);
        setOrientationResult(result);
        console.log('SolutionViewer3D: Computed orientation result:', result);
      } catch (error) {
        console.warn('SolutionViewer3D: Failed to compute orientation:', error);
        setOrientationResult(null);
      }
    } else {
      setOrientationResult(null);
    }
  }, [solution, maxPlacements, orientToSurface, movieOverrides]);

  // Separate effect for initial camera positioning - only runs when solution changes
  useEffect(() => {
    if (!solution || !solution.placements || cameraInitialized || !canvasRef.current) {
      return;
    }

    console.log('SolutionViewer3D: Camera initialization triggered - this should only happen on solution load');

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
        const worldCell = fccToWorld(i, j, k);
        bounds.expandByPoint(new THREE.Vector3(worldCell.x, worldCell.y, worldCell.z));
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

  // Effect to apply orientation transform to the scene
  useEffect(() => {
    if (!scene || !orientationResult) return;

    // Find all sphere and bond instances
    const instances = scene.children.filter(child => 
      child.userData.type === 'InstancedSpheres' || child.userData.type === 'InstancedBonds'
    );

    if (instances.length === 0) return;

    // Store original transforms if not already stored
    if (!originalTransform) {
      const firstInstance = instances[0];
      setOriginalTransform({
        position: firstInstance.position.clone(),
        rotation: firstInstance.quaternion.clone()
      });
    }

    // Apply transform to each instance
    instances.forEach((instance, idx) => {
      // Store original transform if not already stored
      if (!instance.userData.originalPosition) {
        instance.userData.originalPosition = instance.position.clone();
        instance.userData.originalQuaternion = instance.quaternion.clone();
      }
      
      // Reset to original position first
      const originalPos = instance.userData.originalPosition.clone();
      const originalQuat = instance.userData.originalQuaternion.clone();
      
      instance.position.copy(originalPos);
      instance.quaternion.copy(originalQuat);
      
      // Translate to put hull centroid at origin
      instance.position.sub(orientationResult.hullCentroid);
      
      // Apply rotation about origin (which is now the hull centroid)
      instance.position.applyQuaternion(orientationResult.rotation);
      instance.quaternion.multiplyQuaternions(orientationResult.rotation, instance.quaternion);
      
      // Translate back and apply grounding
      instance.position.add(orientationResult.hullCentroid);
      instance.position.add(orientationResult.translation);
    });

    console.log('SolutionViewer3D: Applied orientation transform to', instances.length, 'instances');
  }, [scene, orientationResult, originalTransform]);

  // Effect to handle reset orientation
  useEffect(() => {
    if (resetTrigger === 0 || !scene || !originalTransform) return;

    // Find all sphere and bond instances
    const instances = scene.children.filter(child => 
      child.userData.type === 'InstancedSpheres' || child.userData.type === 'InstancedBonds'
    );

    // Reset each instance to original transform
    instances.forEach(instance => {
      if (instance.userData.originalPosition && instance.userData.originalQuaternion) {
        instance.position.copy(instance.userData.originalPosition);
        instance.quaternion.copy(instance.userData.originalQuaternion);
      }
    });
    
    // Clear orientation result
    setOrientationResult(null);
    
    console.log('SolutionViewer3D: Reset orientation to original for', instances.length, 'instances');
  }, [resetTrigger, scene, originalTransform]);

  // Effect to apply piece spacing transforms
  useEffect(() => {
    if (!scene || !pieceSpacingData) {
      console.log('SolutionViewer3D: Piece spacing skipped - scene:', !!scene, 'data:', !!pieceSpacingData, 'spacing:', pieceSpacing);
      return;
    }

    const effectivePieceSpacing = movieOverrides?.pieceSpacing ?? pieceSpacing;
    const { pieceCentroids, pieceDirections } = pieceSpacingData;

    // Find all unified piece instances
    const instances = scene.children.filter(child => 
      child.userData.type === 'UnifiedPiece'
    );

    console.log('SolutionViewer3D: Found instances for spacing:', instances.length);
    console.log('SolutionViewer3D: Available pieces:', Object.keys(pieceCentroids));
    console.log('SolutionViewer3D: Spacing value s =', effectivePieceSpacing);

    let transformedCount = 0;
    instances.forEach((instance, idx) => {
      const piece = instance.userData.piece;
      console.log(`Instance ${idx}: type=${instance.userData.type}, piece=${piece}`);
      
      if (!piece || !pieceCentroids[piece] || !pieceDirections[piece]) {
        console.log(`Skipping instance ${idx}: missing data for piece ${piece}`);
        return;
      }

      const baselineVector = pieceDirections[piece]; // v_i = c_i - p (baseline vector)
      console.log(`Piece ${piece} baseline vector: [${baselineVector.x.toFixed(3)}, ${baselineVector.y.toFixed(3)}, ${baselineVector.z.toFixed(3)}]`);
      
      // Skip pieces at pivot (no-move marker)
      if (baselineVector.length() < 0.001) {
        console.log(`Skipping piece ${piece}: at pivot`);
        return;
      }

      // Calculate translation offset: Δp_i(s) = (s-1) * v_i
      const offset = baselineVector.clone().multiplyScalar(effectivePieceSpacing - 1.0);

      // Store original position if not already stored
      if (!instance.userData.originalSpacingPosition) {
        instance.userData.originalSpacingPosition = instance.position.clone();
      }

      // Apply spacing offset to original position
      const originalPos = instance.userData.originalSpacingPosition.clone();
      const newPos = originalPos.add(offset);
      instance.position.copy(newPos);
      
      console.log(`Transformed piece ${piece}: s=${effectivePieceSpacing}, baseline=[${baselineVector.x.toFixed(3)}, ${baselineVector.y.toFixed(3)}, ${baselineVector.z.toFixed(3)}], offset=[${offset.x.toFixed(2)}, ${offset.y.toFixed(2)}, ${offset.z.toFixed(2)}]`);
      transformedCount++;
    });

    console.log('SolutionViewer3D: Applied centroid scaling:', effectivePieceSpacing, 'transformed:', transformedCount, 'instances');
  }, [scene, pieceSpacingData, pieceSpacing, movieOverrides]);

  // Effect to reset piece spacing when spacing is 1.0 (original pose)
  useEffect(() => {
    if (!scene || pieceSpacing !== 1.0) return;

    // Find all instances and reset to original spacing positions
    const instances = scene.children.filter(child => 
      child.userData.type === 'UnifiedPiece'
    );

    instances.forEach(instance => {
      if (instance.userData.originalSpacingPosition) {
        instance.position.copy(instance.userData.originalSpacingPosition);
      }
    });

    console.log('SolutionViewer3D: Reset piece spacing to original pose for', instances.length, 'instances');
  }, [scene, pieceSpacing]);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    takeScreenshot: async (): Promise<string> => {
      if (!canvasRef.current) {
        throw new Error('Canvas not ready');
      }
      
      console.log('SolutionViewer3D: Taking screenshot - camera should NOT be altered');
      
      // Get the canvas element from ThreeCanvas
      const canvas = canvasRef.current.getCanvas();
      if (!canvas) {
        throw new Error('Canvas element not found');
      }
      
      // Create a square crop based on canvas height
      const sourceCanvas = canvas;
      const height = sourceCanvas.height;
      const width = sourceCanvas.width;
      const size = Math.min(width, height);
      
      // Create a new canvas for the cropped square image
      const cropCanvas = document.createElement('canvas');
      cropCanvas.width = size;
      cropCanvas.height = size;
      const cropCtx = cropCanvas.getContext('2d');
      
      if (!cropCtx) {
        throw new Error('Failed to get 2D context for crop canvas');
      }
      
      // Calculate crop position (center the crop)
      const cropX = (width - size) / 2;
      const cropY = (height - size) / 2;
      
      // Draw the cropped portion to the new canvas
      cropCtx.drawImage(sourceCanvas, cropX, cropY, size, size, 0, 0, size, size);
      
      // Convert cropped canvas to data URL
      const dataUrl = cropCanvas.toDataURL('image/png');
      
      console.log('SolutionViewer3D: Screenshot captured and cropped to square successfully');
      return dataUrl;
    },
    
    createMovie: async (duration: number, showPlacement: boolean, showSeparation: boolean, onProgress?: (progress: number, phase: string) => void): Promise<Blob> => {
      if (!canvasRef.current || !solution) {
        throw new Error('Canvas or solution not ready');
      }
      
      // Open directory picker for saving frames
      let directoryHandle: any = null;
      if ('showDirectoryPicker' in window) {
        try {
          directoryHandle = await (window as any).showDirectoryPicker();
        } catch (err) {
          throw new Error('Directory selection cancelled or not supported');
        }
      } else {
        throw new Error('Directory picker not supported in this browser');
      }
      
      const fps = 30;
      const totalFrames = duration * fps;
      const frameFiles: { name: string; blob: Blob }[] = [];
      
      // Animation sequence timing
      const phaseFrames = Math.floor(totalFrames / 5); // 5 phases
      let frameIndex = 0;
      
      // Easing function (ease-in-out)
      const easeInOut = (t: number): number => {
        return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
      };
      
      // Helper function to capture and crop frame
      const captureSquareFrame = async (): Promise<Blob | null> => {
        const canvas = canvasRef.current?.getCanvas();
        if (!canvas) return null;
        
        // Create square crop
        const height = canvas.height;
        const width = canvas.width;
        const size = Math.min(width, height);
        
        const cropCanvas = document.createElement('canvas');
        cropCanvas.width = size;
        cropCanvas.height = size;
        const cropCtx = cropCanvas.getContext('2d');
        
        if (!cropCtx) return null;
        
        const cropX = (width - size) / 2;
        const cropY = (height - size) / 2;
        
        cropCtx.drawImage(canvas, cropX, cropY, size, size, 0, 0, size, size);
        
        // Convert to blob
        return new Promise((resolve) => {
          cropCanvas.toBlob((blob) => resolve(blob), 'image/png');
        });
      };
      
      // Helper function to save frame to directory
      const saveFrameToDirectory = async (frameBlob: Blob, filename: string) => {
        if (directoryHandle) {
          try {
            const fileHandle = await directoryHandle.getFileHandle(filename, { create: true });
            const writable = await fileHandle.createWritable();
            await writable.write(frameBlob);
            await writable.close();
          } catch (err) {
            console.error('Failed to save frame:', filename, err);
          }
        }
      };
      
      // Helper function to wait for render and update progress
      const waitForRender = (phase: string, progress: number) => {
        if (onProgress) {
          onProgress(progress, phase);
        }
        return new Promise(resolve => setTimeout(resolve, 100)); // Slower for visibility
      };
      
      // Store original state
      const originalMaxPlacements = maxPlacements;
      const originalSpacing = pieceSpacing;
      
      try {
        // Phase 1: Show full solution (static)
        for (let i = 0; i < phaseFrames; i++) {
          const progress = (frameIndex / totalFrames) * 100;
          await waitForRender('Phase 1: Static Full Solution', progress);
          
          const frameBlob = await captureSquareFrame();
          if (frameBlob) {
            const filename = `frame_${frameIndex.toString().padStart(6, '0')}.png`;
            frameFiles.push({ name: filename, blob: frameBlob });
            await saveFrameToDirectory(frameBlob, filename);
          }
          frameIndex++;
        }
        
        // Phase 2: Placement animation (if enabled)
        if (showPlacement && solution.placements) {
          const placementFrames = phaseFrames;
          for (let i = 0; i < placementFrames; i++) {
            const progress = i / (placementFrames - 1);
            const easedProgress = easeInOut(progress);
            
            // Animate through placements by changing maxPlacements
            const targetPlacement = Math.max(1, Math.floor(easedProgress * solution.placements.length));
            
            // Update both callback and internal state
            if (onMaxPlacementsChange) {
              onMaxPlacementsChange(targetPlacement);
            }
            // Override the maxPlacements for movie creation
            setMovieOverrides(prev => ({ ...prev, maxPlacements: targetPlacement }));
            
            const overallProgress = (frameIndex / totalFrames) * 100;
            await waitForRender('Phase 2: Placement Animation', overallProgress);
            
            const frameBlob = await captureSquareFrame();
            if (frameBlob) {
              const filename = `frame_${frameIndex.toString().padStart(6, '0')}.png`;
              frameFiles.push({ name: filename, blob: frameBlob });
              await saveFrameToDirectory(frameBlob, filename);
            }
            frameIndex++;
          }
        }
        
        // Phase 3: Show full solution again (static)
        for (let i = 0; i < phaseFrames; i++) {
          const progress = (frameIndex / totalFrames) * 100;
          await waitForRender('Phase 3: Static Full Solution', progress);
          
          const frameBlob = await captureSquareFrame();
          if (frameBlob) {
            const filename = `frame_${frameIndex.toString().padStart(6, '0')}.png`;
            frameFiles.push({ name: filename, blob: frameBlob });
            await saveFrameToDirectory(frameBlob, filename);
          }
          frameIndex++;
        }
        
        // Phase 4: Separation animation (if enabled)
        if (showSeparation) {
          const separationFrames = phaseFrames;
          
          for (let i = 0; i < separationFrames; i++) {
            const progress = i / (separationFrames - 1);
            const easedProgress = easeInOut(progress);
            
            // Animate spacing from 1.0 to 2.0
            const animatedSpacing = 1.0 + easedProgress * 1.0;
            
            // Update both callback and internal state
            if (onPieceSpacingChange) {
              onPieceSpacingChange(animatedSpacing);
            }
            // Override the pieceSpacing for movie creation
            setMovieOverrides(prev => ({ ...prev, pieceSpacing: animatedSpacing }));
            
            const overallProgress = (frameIndex / totalFrames) * 100;
            await waitForRender('Phase 4: Separation Animation', overallProgress);
            
            const frameBlob = await captureSquareFrame();
            if (frameBlob) {
              const filename = `frame_${frameIndex.toString().padStart(6, '0')}.png`;
              frameFiles.push({ name: filename, blob: frameBlob });
              await saveFrameToDirectory(frameBlob, filename);
            }
            frameIndex++;
          }
        }
        
        // Phase 5: Show final state (static)
        for (let i = 0; i < phaseFrames; i++) {
          const progress = (frameIndex / totalFrames) * 100;
          await waitForRender('Phase 5: Final State', progress);
          
          const frameBlob = await captureSquareFrame();
          if (frameBlob) {
            const filename = `frame_${frameIndex.toString().padStart(6, '0')}.png`;
            frameFiles.push({ name: filename, blob: frameBlob });
            await saveFrameToDirectory(frameBlob, filename);
          }
          frameIndex++;
        }
        
        // Create movie from frames
        const movieBlob = await createMPEGFromFrames(frameFiles, fps);
        return movieBlob;
        
      } finally {
        // Reset to original state
        setMovieOverrides(null);
        if (onMaxPlacementsChange) {
          onMaxPlacementsChange(originalMaxPlacements);
        }
        if (onPieceSpacingChange) {
          onPieceSpacingChange(originalSpacing);
        }
      }
    }
  }), [solution]);

  return (
    <div style={{ width: '100%', height: '500px', border: '1px solid var(--border)', borderRadius: '8px', display: 'flex', justifyContent: 'center' }}>
      <div style={{ width: '500px', height: '500px' }}>
        <ThreeCanvas ref={canvasRef} onReady={handleThreeReady}>
        {scene && pieceGroups.length > 0 && (
          <>
            {console.log('SolutionViewer3D: Rendering', pieceGroups.length, 'piece groups')}
            {pieceGroups.map((group, index) => (
              <UnifiedPiece
                key={`piece-${group.piece}-${index}`}
                piece={group.piece}
                spheres={group.spheres}
                bonds={group.bonds}
                scene={scene}
              />
            ))}
          </>
        )}
        </ThreeCanvas>
      </div>
    </div>
  );
});
