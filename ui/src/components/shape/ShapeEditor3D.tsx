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
  const [isCameraMoving, setIsCameraMoving] = useState<boolean>(false);
  const cellIndexMapRef = useRef<Map<number, WorldCell>>(new Map());
  const validNeighborsRef = useRef<WorldCell[]>([]);
  const debounceTimeoutRef = useRef<number | null>(null);
  const mouseDownCameraPositionRef = useRef<THREE.Vector3 | null>(null);
  const mouseDownCameraRotationRef = useRef<THREE.Euler | null>(null);
  const mouseDownButtonRef = useRef<number | null>(null);

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
    console.log('isCameraMoving:', isCameraMoving);

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

    // Reset all sphere colors to blue first
    if (meshRef.current && meshRef.current.instanceColor) {
      const blueColor = new THREE.Color(0x4da6ff);
      const colors = meshRef.current.instanceColor.array as Float32Array;
      for (let i = 0; i < cells.length; i++) {
        colors[i * 3] = blueColor.r;     // Red component
        colors[i * 3 + 1] = blueColor.g; // Green component
        colors[i * 3 + 2] = blueColor.b; // Blue component
      }
      meshRef.current.instanceColor.needsUpdate = true;
    }

    // Update hover state and highlight
    console.log('Processing targetCell:', targetCell, 'isCameraMoving:', isCameraMoving);
    if (targetCell) {
      setHoveredCell(targetCell);
      setWillAdd(isAddOperation);
      onHover?.(targetCell);
      
      if (isAddOperation) {
        // Show green highlight for add operation
        if (highlightMeshRef.current) {
          highlightMeshRef.current.position.set(targetCell.X * scale, targetCell.Y * scale, targetCell.Z * scale);
          const material = highlightMeshRef.current.material as THREE.MeshStandardMaterial;
          material.color.setHex(0x00ff00); // Green for add
          highlightMeshRef.current.visible = true;
        }
      } else {
        // For delete operation, show red highlight at the same position as the sphere
        if (highlightMeshRef.current) {
          highlightMeshRef.current.position.set(targetCell.X * scale, targetCell.Y * scale, targetCell.Z * scale);
          const material = highlightMeshRef.current.material as THREE.MeshStandardMaterial;
          material.color.setHex(0xff0000); // Red for delete
          highlightMeshRef.current.visible = true;
        }
      }
    } else {
      // Clear hover state when not hovering
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
  }, [scene, camera, hoveredCell, onHover, scale, cells, isCameraMoving]);

  // Check if a neighbor position is facing the camera (visible from current viewpoint)
  const isNeighborFacingCamera = useCallback((neighbor: WorldCell, existingCells: WorldCell[], camera: THREE.PerspectiveCamera | null): boolean => {
    // Temporarily disable camera facing check to debug neighbor detection
    return true;
  }, [scale]);

  // Check if camera moved during mouse interaction
  const hasCameraMoved = useCallback((): boolean => {
    if (!camera || !mouseDownCameraPositionRef.current || !mouseDownCameraRotationRef.current) {
      console.log('Camera movement check: missing camera or stored positions');
      return false;
    }
    
    const positionThreshold = 0.01; // Increased threshold - was too sensitive
    const rotationThreshold = 0.01; // Increased threshold - was too sensitive
    
    const positionDistance = camera.position.distanceTo(mouseDownCameraPositionRef.current);
    const positionMoved = positionDistance > positionThreshold;
    
    const rotationDiffX = Math.abs(camera.rotation.x - mouseDownCameraRotationRef.current.x);
    const rotationDiffY = Math.abs(camera.rotation.y - mouseDownCameraRotationRef.current.y);
    const rotationDiffZ = Math.abs(camera.rotation.z - mouseDownCameraRotationRef.current.z);
    const rotationMoved = rotationDiffX > rotationThreshold || rotationDiffY > rotationThreshold || rotationDiffZ > rotationThreshold;
    
    console.log('Camera position distance:', positionDistance, 'threshold:', positionThreshold, 'moved:', positionMoved);
    console.log('Camera rotation diffs:', rotationDiffX, rotationDiffY, rotationDiffZ, 'threshold:', rotationThreshold, 'moved:', rotationMoved);
    
    return positionMoved || rotationMoved;
  }, [camera]);

  const handleClick = useCallback((event: MouseEvent) => {
    console.log('=== CLICK HANDLER CALLED ===');
    console.log('hoveredCell:', hoveredCell);
    console.log('isCameraMoving:', isCameraMoving);
    console.log('onAdd function:', onAdd);
    console.log('onRemove function:', onRemove);
    
    if (!hoveredCell) {
      console.log('Click ignored: no hovered cell');
      return;
    }
    
    if (isCameraMoving) {
      console.log('Click ignored: camera is moving');
      return;
    }
    
    // Check if camera moved during ANY mouse interaction (including left button)
    if (hasCameraMoved()) {
      console.log('Click ignored: camera moved during mouse interaction (button:', mouseDownButtonRef.current, ')');
      return;
    }

    // Auto-detect operation based on whether cell exists
    const cellExists = cells.some(cell => keyW(cell.X, cell.Y, cell.Z) === keyW(hoveredCell.X, hoveredCell.Y, hoveredCell.Z));
    console.log('Cell exists:', cellExists);

    if (cellExists) {
      // Cell exists, remove it
      console.log('Calling onRemove with:', hoveredCell);
      onRemove?.(hoveredCell);
    } else if (isValidWorldCell(hoveredCell.X, hoveredCell.Y, hoveredCell.Z) && 
               (cells.length === 0 || isAdjacentToExistingCells(hoveredCell, cells))) {
      // Cell doesn't exist, is valid FCC, and is adjacent to existing cells (or first cell)
      console.log('Calling onAdd with:', hoveredCell);
      onAdd?.(hoveredCell);
    } else {
      console.log('Add operation blocked - invalid cell or not adjacent');
      console.log('isValidWorldCell:', isValidWorldCell(hoveredCell.X, hoveredCell.Y, hoveredCell.Z));
      console.log('cells.length:', cells.length);
      console.log('isAdjacentToExistingCells:', cells.length > 0 ? isAdjacentToExistingCells(hoveredCell, cells) : 'N/A (first cell)');
    }
  }, [hoveredCell, cells, onAdd, onRemove, isCameraMoving]);

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
    
    const highlightGeometry = new THREE.SphereGeometry(radius * 1.05, 32, 24);
    const highlightMaterial = new THREE.MeshStandardMaterial({
      color: 0x00ff00, // Default to green for adding
      metalness: 0.3,
      roughness: 0.4,
      emissive: 0x111111,
      emissiveIntensity: 0.1,
      transparent: false,
      opacity: 1.0,
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
    const geometry = new THREE.SphereGeometry(radius, 32, 24);
    const material = new THREE.MeshStandardMaterial({
      color: 0x4da6ff, // Lighter, brighter blue color for shape spheres
      metalness: 0.3,
      roughness: 0.4,
      emissive: 0x111111,
      emissiveIntensity: 0.1,
    });

    // Create new instanced mesh
    const mesh = new THREE.InstancedMesh(geometry, material, cells.length);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    meshRef.current = mesh;

    // Initialize instance colors (all blue by default)
    const blueColor = new THREE.Color(0x4da6ff);
    const colors = new Float32Array(cells.length * 3);
    for (let i = 0; i < cells.length; i++) {
      colors[i * 3] = blueColor.r;
      colors[i * 3 + 1] = blueColor.g;
      colors[i * 3 + 2] = blueColor.b;
    }
    mesh.instanceColor = new THREE.InstancedBufferAttribute(colors, 3);

    // Update instance matrices
    const matrix = new THREE.Matrix4();
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      matrix.setPosition(cell.X * scale, cell.Y * scale, cell.Z * scale);
      mesh.setMatrixAt(i, matrix);
    }
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) {
      mesh.instanceColor.needsUpdate = true;
    }

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

  // Camera movement detection handlers
  const handleMouseDown = useCallback((event: MouseEvent) => {
    console.log('=== MOUSE DOWN ===', 'button:', event.button);
    
    // Store mouse button and camera state
    mouseDownButtonRef.current = event.button;
    
    if (camera) {
      mouseDownCameraPositionRef.current = camera.position.clone();
      mouseDownCameraRotationRef.current = camera.rotation.clone();
      console.log('Stored camera position for button', event.button);
    }
    
    // Only track camera movement for right mouse button (orbit) and middle mouse button (pan)
    if (event.button === 1 || event.button === 2) {
      console.log('Setting camera moving to TRUE');
      setIsCameraMoving(true);
      
      // Clear any existing debounce timeout
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
        debounceTimeoutRef.current = null;
      }
    }
  }, [camera]);

  const handleMouseUp = useCallback((event: MouseEvent) => {
    console.log('=== MOUSE UP ===', 'button:', event.button);
    if (event.button === 1 || event.button === 2) {
      console.log('Starting debounce timer to set camera moving to FALSE');
      // Debounce the re-enable of interactions
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
      }
      
      debounceTimeoutRef.current = window.setTimeout(() => {
        console.log('Debounce timer fired - setting camera moving to FALSE');
        setIsCameraMoving(false);
        debounceTimeoutRef.current = null;
      }, 100); // 100ms delay after camera movement stops
    }
  }, []);

  // Additional camera movement detection via wheel events
  const handleWheel = useCallback((event: WheelEvent) => {
    setIsCameraMoving(true);
    
    // Clear any existing debounce timeout
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }
    
    // Debounce the re-enable of interactions
    debounceTimeoutRef.current = window.setTimeout(() => {
      setIsCameraMoving(false);
      debounceTimeoutRef.current = null;
    }, 100); // 100ms delay after wheel zoom stops
  }, []);

  // Set up mouse event listeners
  useEffect(() => {
    if (!scene) return;

    const canvas = scene.userData?.canvas || document.querySelector('canvas');
    if (!canvas) return;

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('click', handleClick);
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('wheel', handleWheel);

    return () => {
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('click', handleClick);
      canvas.removeEventListener('mousedown', handleMouseDown);
      canvas.removeEventListener('mouseup', handleMouseUp);
      canvas.removeEventListener('wheel', handleWheel);
      
      // Clean up debounce timeout
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current);
        debounceTimeoutRef.current = null;
      }
    };
  }, [handleMouseMove, handleClick, handleMouseDown, handleMouseUp, handleWheel, scene]);

  return null; // This component manages Three.js objects directly
};
