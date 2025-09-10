import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as THREE from 'three';
import { WorldCell, keyW, getValidNeighborPositions, getDirectNeighbors, isValidWorldCell, isAdjacentToExistingCells } from '../../lib/lattice';

export interface ShapeEditor3DProps {
  cells: WorldCell[];
  scale?: number;
  radius?: number;
  scene?: THREE.Scene | null;
  camera?: THREE.PerspectiveCamera | null;
  onAdd?: (cell: WorldCell) => void;
  onRemove?: (cell: WorldCell) => void;
  onHover?: (cell: WorldCell | null, willAdd?: boolean) => void;
  onRequestFit?: () => void;
}

export const ShapeEditor3D: React.FC<ShapeEditor3DProps> = ({
  cells,
  scale = 1.0,
  radius = 0.4,
  scene,
  camera,
  onAdd,
  onRemove,
  onHover,
  onRequestFit
}) => {
  const meshRef = useRef<THREE.InstancedMesh | null>(null);
  const highlightMeshRef = useRef<THREE.Mesh | null>(null);
  const raycasterRef = useRef<THREE.Raycaster>(new THREE.Raycaster());
  const mouseRef = useRef<THREE.Vector2>(new THREE.Vector2());
  const [hoveredCell, setHoveredCell] = useState<WorldCell | null>(null);
  const [willAdd, setWillAdd] = useState<boolean>(false);
  const cellIndexMapRef = useRef<Map<number, WorldCell>>(new Map());
  const validNeighborsRef = useRef<WorldCell[]>([]);

  // Convert cells to positions and build index map
  const positions = React.useMemo(() => {
    const posArray = new Float32Array(cells.length * 3);
    const indexMap = new Map<number, WorldCell>();
    
    cells.forEach((cell, index) => {
      posArray[index * 3] = cell.X * scale;
      posArray[index * 3 + 1] = cell.Y * scale;
      posArray[index * 3 + 2] = cell.Z * scale;
      indexMap.set(index, cell);
    });
    
    cellIndexMapRef.current = indexMap;
    
    // Update valid neighbor positions
    const neighbors = getValidNeighborPositions(cells);
    validNeighborsRef.current = neighbors;
    console.log('=== VALID NEIGHBORS COMPUTED ===');
    console.log('Cells input:', cells);
    console.log('Valid neighbors output:', neighbors);
    
    return posArray;
  }, [cells, scale]);

  // Handle mouse events for picking
  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!scene || !camera) return;
    
    console.log('=== MOUSE MOVE HANDLER CALLED ===');

    const canvas = event.target as HTMLCanvasElement;
    const rect = canvas.getBoundingClientRect();
    
    mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycasterRef.current.setFromCamera(mouseRef.current, camera);
    
    let targetCell: WorldCell | null = null;

    // First try to intersect with existing cells
    if (meshRef.current && cells.length > 0) {
      const intersects = raycasterRef.current.intersectObject(meshRef.current);
      if (intersects.length > 0 && intersects[0].instanceId !== undefined) {
        const instanceId = intersects[0].instanceId;
        targetCell = cellIndexMapRef.current.get(instanceId) || null;
      }
    }

    // If no existing cell hit, check if we're hovering over a valid neighbor position
    if (!targetCell) {
      // Get all valid neighbor positions (adjacent to existing cells)
      const validNeighbors = cells.length > 0 ? validNeighborsRef.current : [];
      
      // If no existing cells, allow adding anywhere valid
      if (cells.length === 0) {
        // Cast ray to find intersection with Y=0 plane for first cell
        const gridPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
        const intersectionPoint = new THREE.Vector3();
        
        if (raycasterRef.current.ray.intersectPlane(gridPlane, intersectionPoint)) {
          const gridX = Math.round(intersectionPoint.x / scale);
          const gridY = Math.round(intersectionPoint.y / scale);
          const gridZ = Math.round(intersectionPoint.z / scale);
          
          if (isValidWorldCell(gridX, gridY, gridZ)) {
            const gridPoint = new THREE.Vector3(gridX * scale, gridY * scale, gridZ * scale);
            const distance = raycasterRef.current.ray.distanceToPoint(gridPoint);
            
            if (distance < radius * 5) {
              targetCell = { X: gridX, Y: gridY, Z: gridZ };
            }
          }
        }
      } else {
        // Check each valid neighbor position
        let bestDistance = Infinity;
        let bestCell: WorldCell | null = null;
        
        for (const neighbor of validNeighbors) {
          const neighborPoint = new THREE.Vector3(neighbor.X * scale, neighbor.Y * scale, neighbor.Z * scale);
          const distance = raycasterRef.current.ray.distanceToPoint(neighborPoint);
          
          console.log(`Checking neighbor ${neighbor.X},${neighbor.Y},${neighbor.Z}: distance=${distance}, threshold=${radius * 10}`);
          
          if (distance < bestDistance && distance < radius * 10) { 
            bestDistance = distance;
            bestCell = neighbor;
            console.log(`Selected neighbor: ${neighbor.X},${neighbor.Y},${neighbor.Z}`);
          }
        }
        
        targetCell = bestCell;
      }
    }

    // Determine if this would be an add or remove operation
    let isAddOperation = false;
    if (targetCell) {
      const cellExists = cells.some(cell => keyW(cell.X, cell.Y, cell.Z) === keyW(targetCell.X, targetCell.Y, targetCell.Z));
      isAddOperation = !cellExists;
    }

    // Update hover state and highlight
    if (targetCell) {
      setHoveredCell(targetCell);
      setWillAdd(isAddOperation);
      onHover?.(targetCell);
      
      if (highlightMeshRef.current) {
        highlightMeshRef.current.position.set(targetCell.X * scale, targetCell.Y * scale, targetCell.Z * scale);
        const material = highlightMeshRef.current.material as THREE.MeshStandardMaterial;
        material.color.setHex(isAddOperation ? 0x00ff00 : 0xff0000); // Green for add, red for remove
        highlightMeshRef.current.visible = true;
      }
    } else if (hoveredCell) {
      setHoveredCell(null);
      setWillAdd(false);
      onHover?.(null);
      if (highlightMeshRef.current) {
        highlightMeshRef.current.visible = false;
      }
    }
    
    // Debug logging
    console.log('=== Enhanced Mouse Move Debug ===');
    console.log('Cells count:', cells.length);
    console.log('Existing world cells:', cells.map(cell => ({ x: cell.X, y: cell.Y, z: cell.Z })));
    
    // Test neighbor generation directly here
    console.log('=== DIRECT NEIGHBOR TEST ===');
    if (cells.length > 0) {
      const testCell = cells[0];
      const testSum = testCell.X + testCell.Y + testCell.Z;
      console.log('Test cell:', testCell, `sum=${testSum}, sum%2=${testSum%2}`);
      
      const directNeighbors = getDirectNeighbors(testCell);
      console.log('Direct neighbors:', directNeighbors);
      
      directNeighbors.forEach((neighbor: WorldCell) => {
        const isValid = isValidWorldCell(neighbor.X, neighbor.Y, neighbor.Z);
        const exists = cells.some(existing => 
          existing.X === neighbor.X && existing.Y === neighbor.Y && existing.Z === neighbor.Z
        );
        const sum = neighbor.X + neighbor.Y + neighbor.Z;
        console.log(`Neighbor ${neighbor.X},${neighbor.Y},${neighbor.Z}: sum=${sum}, sum%2=${sum%2}, valid=${isValid}, exists=${exists}`);
        
        if (isValid && !exists) {
          console.log('*** SHOULD BE VALID NEIGHBOR ***');
        }
      });
    }
    
    const validNeighbors = getValidNeighborPositions(cells);
    console.log('Valid neighbors count:', validNeighbors.length);
    console.log('Valid neighbors:', validNeighbors);
    
    console.log('Mouse world position:', { x: mouseRef.current.x, y: mouseRef.current.y, z: 0 });
    console.log('Target cell found:', targetCell);
    console.log('Is add operation:', isAddOperation);
    
    // Debug neighbor distances
    for (const neighbor of validNeighbors) {
      const neighborWorldPos = new THREE.Vector3(neighbor.X * scale, neighbor.Y * scale, neighbor.Z * scale);
      const mousePos = new THREE.Vector3(mouseRef.current.x, mouseRef.current.y, 0);
      const distance = neighborWorldPos.distanceTo(mousePos);
      console.log(`Neighbor ${neighbor.X},${neighbor.Y},${neighbor.Z}: distance = ${distance.toFixed(3)}, threshold = 1.5`);
    }
  }, [scene, camera, hoveredCell, onHover, scale, cells]);

  // Check if a neighbor position is facing the camera (visible from current viewpoint)
  const isNeighborFacingCamera = useCallback((neighbor: WorldCell, existingCells: WorldCell[], camera: THREE.PerspectiveCamera | null): boolean => {
    // Temporarily disable camera facing check to debug neighbor detection
    return true;
  }, [scale]);

  const handleClick = useCallback((event: MouseEvent) => {
    if (!hoveredCell) return;

    // Auto-detect operation based on whether cell exists
    const cellExists = cells.some(cell => keyW(cell.X, cell.Y, cell.Z) === keyW(hoveredCell.X, hoveredCell.Y, hoveredCell.Z));

    if (cellExists) {
      // Cell exists, remove it
      onRemove?.(hoveredCell);
    } else if (isValidWorldCell(hoveredCell.X, hoveredCell.Y, hoveredCell.Z) && 
               (cells.length === 0 || isAdjacentToExistingCells(hoveredCell, cells))) {
      // Cell doesn't exist, is valid FCC, and is adjacent to existing cells (or first cell)
      onAdd?.(hoveredCell);
    }
  }, [hoveredCell, cells, onAdd, onRemove]);

  // Set up instanced mesh and highlight
  useEffect(() => {
    if (!scene) return;
    
    // Remove old mesh if it exists
    if (meshRef.current) {
      scene.remove(meshRef.current);
      meshRef.current = null;
    }
    
    // Create highlight mesh (always create for neighbor highlighting)
    if (highlightMeshRef.current) {
      scene.remove(highlightMeshRef.current);
    }
    
    const highlightGeometry = new THREE.SphereGeometry(radius * 1.2, 16, 12);
    const highlightMaterial = new THREE.MeshStandardMaterial({
      color: 0x00ff00, // Default to green for adding
      metalness: 0.0,
      roughness: 0.3,
      transparent: true,
      opacity: 0.6,
    });
    
    const highlightMesh = new THREE.Mesh(highlightGeometry, highlightMaterial);
    highlightMesh.visible = false;
    highlightMeshRef.current = highlightMesh;
    scene.add(highlightMesh);
    
    // If no cells, just return (highlight mesh is ready for first cell)
    if (cells.length === 0) {
      return;
    }

    // Create geometry and material for existing cells
    const geometry = new THREE.SphereGeometry(radius, 16, 12);
    const material = new THREE.MeshStandardMaterial({
      color: 0x00a0db, // R0, G160, B219
      metalness: 0.1,
      roughness: 0.4,
    });

    // Create new instanced mesh
    const mesh = new THREE.InstancedMesh(geometry, material, cells.length);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    meshRef.current = mesh;

    // Update instance matrices
    const matrix = new THREE.Matrix4();
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      matrix.setPosition(cell.X * scale, cell.Y * scale, cell.Z * scale);
      mesh.setMatrixAt(i, matrix);
    }
    mesh.instanceMatrix.needsUpdate = true;

    scene.add(mesh);

    // Cleanup
    return () => {
      if (meshRef.current) {
        scene.remove(meshRef.current);
        geometry.dispose();
        material.dispose();
      }
      if (highlightMeshRef.current) {
        scene.remove(highlightMeshRef.current);
        highlightGeometry.dispose();
        highlightMaterial.dispose();
      }
    };
  }, [scene, cells, radius, scale]);

  // Set up mouse event listeners
  useEffect(() => {
    if (!scene) return;

    const canvas = scene.userData?.canvas || document.querySelector('canvas');
    if (!canvas) return;

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('click', handleClick);

    return () => {
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('click', handleClick);
    };
  }, [handleMouseMove, handleClick, scene]);

  return null; // This component manages Three.js objects directly
};
