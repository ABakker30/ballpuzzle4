import React, { useRef, useEffect, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { useAppStore } from "../store";
import { fccToWorld } from "../lib/fcc";
import { isCellOccupied, calculatePieceOccupancy, wouldCauseCollision } from "../utils/occupancy";
import { undoRedoManager, recordPiecePlacement as recordUndoPlacement } from "../utils/undoRedo";
import { validateSolution, getCompletionStats } from "../utils/solutionDetection";
import { recordPiecePlacement, recordPieceRotation, recordUndo, recordRedo, recordSnap, recordDragStart, recordDragEnd } from "../utils/sessionStats";
interface PuzzleViewer3DProps {
  containerPoints: THREE.Vector3[];
  placedPieces: Array<{ piece: string; position: any; rotation: any; id: string; occupiedCells: THREE.Vector3[] }>;
  onCellClick?: (position: THREE.Vector3) => void;
  onSolutionComplete?: (validationResult: any) => void;
  hullFaces?: Array<{
    normal: THREE.Vector3;
    vertices: THREE.Vector3[];
    isLargest: boolean;
  }>;
}

interface DragState {
  isDragging: boolean;
  initialAnchor: THREE.Vector3 | null;
  activeSphereIndex: number;
  easingStartTime: number;
  preDragTransform: {
    position: THREE.Vector3;
    rotation: THREE.Euler;
  } | null;
}

// Move (Pre-Snap) constants
const EASING_DURATION_MS = 175;
const MOVEMENT_AABB_SCALE = 1.5;

// Debug overlay constants
const DEBUG_PERFORMANCE_BUDGET_MS = 0.2;
const DEBUG_OPACITY_LEVELS = [1.0, 0.6, 0.3];

// Legacy snap constants (will be removed in snap phase)
const SNAP_RADIUS = 1.5;
const AUTO_SNAP_RADIUS = 1.0;

export default function PuzzleViewer3D({ containerPoints, placedPieces, onCellClick, onSolutionComplete, hullFaces }: PuzzleViewer3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const selectedPieceMeshRef = useRef<THREE.Object3D | null>(null);
  
  const { selectedPiece, selectedPieceTransform, setSelectedPieceTransform, puzzlePieces } = useAppStore();
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    initialAnchor: null,
    activeSphereIndex: 0,
    easingStartTime: 0,
    preDragTransform: null
  });
  const [cameraInitialized, setCameraInitialized] = useState(false);
  
  // Debug overlay state
  const [debugMode, setDebugMode] = useState(() => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('debug') === 'puzzle-move=true';
  });
  const [debugOpacityIndex, setDebugOpacityIndex] = useState(0);
  const [debugCursorPos, setDebugCursorPos] = useState({ x: 0, y: 0 });
  const debugHelpersRef = useRef<THREE.Group | null>(null);

  // Initialize Three.js scene
  useEffect(() => {
    const mount = mountRef.current!;
    const width = mount.clientWidth || 800;
    const height = mount.clientHeight || 600;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f5f5);
    
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(10, 10, 10);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 4096;
    directionalLight.shadow.mapSize.height = 4096;
    scene.add(directionalLight);


    // Store refs
    sceneRef.current = scene;
    rendererRef.current = renderer;
    cameraRef.current = camera;
    controlsRef.current = controls;

    // Handle resize
    const handleResize = () => {
      const w = mount.clientWidth || 800;
      const h = mount.clientHeight || 600;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    window.addEventListener('resize', handleResize);

    // Animation loop
    let animationId: number;
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', handleResize);
      controls.dispose();
      renderer.dispose();
      if (mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, []);

  useEffect(() => {
    if (!sceneRef.current || !rendererRef.current || !cameraRef.current) return;

    const scene = sceneRef.current;
    const renderer = rendererRef.current;
    const camera = cameraRef.current;

  
    // Clear existing objects
    const objectsToRemove = scene.children.filter(child => 
      child.userData.type === 'container' || 
      child.userData.type === 'piece' || 
      child.userData.type === 'selectedPiece' || 
      child.userData.type === 'placedPiece' ||
      child.userData.type === 'candidateRing' ||
      child.userData.type === 'snapRing' ||
      child.userData.type === 'hull'
    );
    objectsToRemove.forEach(obj => scene.remove(obj));

    // Add container points with visual feedback for targeting
    if (containerPoints.length > 0) {
      // Calculate optimal sphere radius so spheres just touch
      let minDistance = Infinity;
      for (let i = 0; i < containerPoints.length; i++) {
        for (let j = i + 1; j < containerPoints.length; j++) {
          const p1 = containerPoints[i];
          const p2 = containerPoints[j];
          const distance = Math.sqrt(
            Math.pow(p1.x - p2.x, 2) + 
            Math.pow(p1.y - p2.y, 2) + 
            Math.pow(p1.z - p2.z, 2)
          );
          minDistance = Math.min(minDistance, distance);
        }
      }
      
      const sphereRadius = minDistance !== Infinity ? minDistance / 2.0 : 0.4; // Spheres just touch
      
      const containerGeometry = new THREE.SphereGeometry(sphereRadius, 32, 32); // Higher quality mesh
      const containerMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x00BFFF, // Bright light blue (Deep Sky Blue)
        transparent: true, 
        opacity: 0.3 // More transparent
      });

      containerPoints.forEach((point, index) => {
        // Check if this cell is occupied
        const isOccupied = isCellOccupied(point);
        
        // Use different materials for occupied vs empty cells
        const material = isOccupied 
          ? new THREE.MeshStandardMaterial({ 
              color: 0xFF4444, // Red for occupied
              transparent: true, 
              opacity: 0.6
            })
          : containerMaterial;
        
        const sphere = new THREE.Mesh(containerGeometry, material);
        sphere.position.set(point.x, point.y, point.z);
        sphere.castShadow = true;
        sphere.receiveShadow = true;
        (sphere as any).userData = { type: 'container', index, position: point, occupied: isOccupied };
        scene.add(sphere);
        
        // Add candidate target ring (initially hidden) - only for empty cells
        if (!isOccupied) {
          const ringGeometry = new THREE.RingGeometry(sphereRadius * 1.2, sphereRadius * 1.5, 16);
          const ringMaterial = new THREE.MeshBasicMaterial({ 
            color: 0xFFFF00, // Yellow for candidate
            transparent: true, 
            opacity: 0.0, // Initially hidden
            side: THREE.DoubleSide
          });
          const ring = new THREE.Mesh(ringGeometry, ringMaterial);
          ring.position.copy(sphere.position);
          ring.rotation.x = Math.PI / 2; // Lay flat
          (ring as any).userData = { type: 'candidateRing', cellIndex: index };
          scene.add(ring);
        }
      });
      
      // Add snap target indicator (pulsing ring for active target)
      if (selectedPieceTransform?.candidateSnapTarget) {
        const targetPos = selectedPieceTransform.candidateSnapTarget;
        const snapRingGeometry = new THREE.RingGeometry(sphereRadius * 1.5, sphereRadius * 2.0, 16);
        const snapRingMaterial = new THREE.MeshBasicMaterial({ 
          color: 0x00FF00, // Green for snap target
          transparent: true, 
          opacity: 0.8,
          side: THREE.DoubleSide
        });
        const snapRing = new THREE.Mesh(snapRingGeometry, snapRingMaterial);
        snapRing.position.copy(targetPos);
        snapRing.rotation.x = Math.PI / 2;
        (snapRing as any).userData = { type: 'snapRing' };
        scene.add(snapRing);
        
        // Add pulsing animation
        const time = Date.now() * 0.005;
        snapRing.scale.setScalar(1 + Math.sin(time) * 0.1);
      }
      
      // Show candidate rings for nearby cells when dragging
      if (selectedPieceTransform && dragState.isDragging) {
        containerPoints.forEach((point, index) => {
          if (!isCellOccupied(point)) {
            const distance = selectedPieceTransform.candidateSnapTarget?.distanceTo(point) || Infinity;
            if (distance < SNAP_RADIUS) {
              // Find and show the candidate ring
              const candidateRing = scene.children.find(child => 
                child.userData.type === 'candidateRing' && child.userData.cellIndex === index
              ) as THREE.Mesh;
              
              if (candidateRing) {
                const material = candidateRing.material as THREE.MeshBasicMaterial;
                material.opacity = Math.max(0.3, 1.0 - (distance / SNAP_RADIUS));
              }
            }
          }
        });
      }
      
      // Render placed pieces
      placedPieces.forEach((placedPiece, index) => {
        const pieceData = puzzlePieces?.[placedPiece.piece];
        if (!pieceData || !pieceData.spheres) return;
        
        const pieceGroup = new THREE.Group();
        
        // Create spheres for the placed piece
        pieceData.spheres.forEach((sphere: any, sphereIndex: number) => {
          const sphereGeometry = new THREE.SphereGeometry(0.35, 64, 64);
          
          // Use a different color scheme for placed pieces (more muted)
          const hue = (index * 137.5) % 360; // Golden angle for good distribution
          const saturation = 60; // Lower saturation for placed pieces
          const lightness = 50;
          const color = new THREE.Color().setHSL(hue / 360, saturation / 100, lightness / 100);
          
          const sphereMaterial = new THREE.MeshStandardMaterial({
            color: color,
            metalness: 0.2,
            roughness: 0.6,
            transparent: true,
            opacity: 0.8 // Slightly transparent to distinguish from active piece
          });
          
          const sphereMesh = new THREE.Mesh(sphereGeometry, sphereMaterial);
          sphereMesh.position.set(sphere.x, sphere.y, sphere.z);
          sphereMesh.castShadow = true;
          sphereMesh.receiveShadow = true;
          
          pieceGroup.add(sphereMesh);
        });
        
        // Apply position and rotation from placed piece data
        pieceGroup.position.copy(placedPiece.position);
        pieceGroup.rotation.copy(placedPiece.rotation);
        pieceGroup.castShadow = true;
        pieceGroup.receiveShadow = true;
        (pieceGroup as any).userData = { 
          type: 'placedPiece', 
          pieceId: placedPiece.id,
          pieceName: placedPiece.piece
        };
        
        scene.add(pieceGroup);
      });

      // Auto-fit camera to container only on first load
      if (cameraRef.current && controlsRef.current && !cameraInitialized) {
        const box = new THREE.Box3();
        containerPoints.forEach(point => {
          box.expandByPoint(new THREE.Vector3(point.x, point.y, point.z));
        });
        
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        
        controlsRef.current.target.copy(center);
        cameraRef.current.position.copy(center);
        cameraRef.current.position.add(new THREE.Vector3(maxDim * 1.5, maxDim * 1.5, maxDim * 1.5));
        controlsRef.current.update();
        setCameraInitialized(true);
      }
    }

    // Add placed pieces (placeholder visualization)
    placedPieces.forEach((placedPiece, index) => {
      const pieceGeometry = new THREE.BoxGeometry(0.8, 0.8, 0.8);
      const pieceMaterial = new THREE.MeshStandardMaterial({ 
        color: 0x00BFFF, // Bright light blue (Deep Sky Blue)
        transparent: true,
        opacity: 0.8
      });
      
      const pieceMesh = new THREE.Mesh(pieceGeometry, pieceMaterial);
      if (placedPiece.position) {
        pieceMesh.position.set(
          placedPiece.position.x || 0,
          placedPiece.position.y || 0,
          placedPiece.position.z || 0
        );
      }
      pieceMesh.castShadow = true;
      pieceMesh.receiveShadow = true;
      (pieceMesh as any).userData = { type: 'piece', id: placedPiece.id, piece: placedPiece.piece };
      scene.add(pieceMesh);
    });

    // Add selected piece if one is selected
    if (selectedPiece && puzzlePieces && puzzlePieces[selectedPiece]) {
      const pieceCoordinates = puzzlePieces[selectedPiece];
      
      // Create piece geometry from actual coordinates
      const pieceGroup = new THREE.Group();
      
      // Generate unique color for this piece
      const pieceIndex = Object.keys(puzzlePieces).indexOf(selectedPiece);
      const hue = (pieceIndex * 137.508) % 360; // Golden angle for good color distribution
      const color = new THREE.Color().setHSL(hue / 360, 0.9, 0.7); // Brighter: higher saturation and lightness
      
      const pieceMaterial = new THREE.MeshStandardMaterial({ 
        color: color,
        metalness: 0.3,
        roughness: 0.4,
        envMapIntensity: 0.5,
        transparent: false,
        opacity: 1.0
      });
      
      // Create high-quality sphere for each coordinate in the piece
      const sphereRadius = 0.35; // Slightly smaller than container spheres for distinction
      const sphereGeometry = new THREE.SphereGeometry(sphereRadius, 64, 64); // Much higher quality mesh
      
      pieceCoordinates.forEach(([i, j, k]: [number, number, number]) => {
        // Convert FCC coordinates to world position
        const worldPos = fccToWorld(i, j, k);
        
        const sphere = new THREE.Mesh(sphereGeometry, pieceMaterial);
        sphere.position.set(worldPos.x, worldPos.y, worldPos.z);
        sphere.castShadow = true;
        sphere.receiveShadow = true;
        
        pieceGroup.add(sphere);
      });
      
      const selectedPieceMesh = pieceGroup;
      
      // Set initial position and rotation from store or default
      if (selectedPieceTransform) {
        selectedPieceMesh.position.copy(selectedPieceTransform.position);
        selectedPieceMesh.rotation.copy(selectedPieceTransform.rotation);
        
        // Highlight active sphere
        if (selectedPieceMesh.children[selectedPieceTransform.activeSphereIndex]) {
          const activeSphere = selectedPieceMesh.children[selectedPieceTransform.activeSphereIndex] as THREE.Mesh;
          const material = activeSphere.material as THREE.MeshStandardMaterial;
          material.emissive.setHex(0x444444); // Slight glow for active sphere
        }
      } else {
        // Default position above container center
        const containerCenter = new THREE.Vector3();
        if (containerPoints.length > 0) {
          containerPoints.forEach(point => containerCenter.add(point));
          containerCenter.divideScalar(containerPoints.length);
        }
        selectedPieceMesh.position.set(
          containerCenter.x,
          containerCenter.y + 3,
          containerCenter.z
        );
        
        // Initialize transform in store
        setSelectedPieceTransform({
          position: selectedPieceMesh.position.clone(),
          rotation: selectedPieceMesh.rotation.clone(),
          snappedToContainer: null,
          activeSphereIndex: 0,
          candidateSnapTarget: null,
          isSnapped: false
        });
        
        // Highlight first sphere as active
        if (selectedPieceMesh.children[0]) {
          const activeSphere = selectedPieceMesh.children[0] as THREE.Mesh;
          const material = activeSphere.material as THREE.MeshStandardMaterial;
          material.emissive.setHex(0x444444);
        }
      }
      
      selectedPieceMesh.castShadow = true;
      selectedPieceMesh.receiveShadow = true;
      (selectedPieceMesh as any).userData = { 
        type: 'selectedPiece', 
        piece: selectedPiece,
        interactive: true
      };
      
      scene.add(selectedPieceMesh);
      selectedPieceMeshRef.current = selectedPieceMesh;
    } else {
      selectedPieceMeshRef.current = null;
    }

  }, [containerPoints, placedPieces, hullFaces, selectedPiece, puzzlePieces, selectedPieceTransform, setSelectedPieceTransform]);

  // Mouse interaction handlers
  useEffect(() => {
    const renderer = rendererRef.current;
    const camera = cameraRef.current;
    const scene = sceneRef.current;
    const controls = controlsRef.current;
    
    if (!renderer || !camera || !scene || !controls) return;

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    
    
    // Helper function to find closest container point for snapping
    const findClosestContainerPoint = (position: THREE.Vector3): { point: THREE.Vector3; distance: number } | null => {
      if (containerPoints.length === 0) return null;
      
      let closestPoint = containerPoints[0];
      let minDistance = position.distanceTo(closestPoint);
      
      for (let i = 1; i < containerPoints.length; i++) {
        const distance = position.distanceTo(containerPoints[i]);
        if (distance < minDistance) {
          minDistance = distance;
          closestPoint = containerPoints[i];
        }
      }
      
      // Return closest point with distance info
      return { point: closestPoint, distance: minDistance };
    };
    
    // Helper function to get active sphere position for a piece
    const getActiveSpherePosition = (pieceGroup: THREE.Object3D, sphereIndex: number): THREE.Vector3 => {
      const spheres = pieceGroup.children;
      if (sphereIndex >= 0 && sphereIndex < spheres.length) {
        const worldPos = new THREE.Vector3();
        spheres[sphereIndex].getWorldPosition(worldPos);
        return worldPos;
      }
      // Fallback to piece center
      const worldPos = new THREE.Vector3();
      pieceGroup.getWorldPosition(worldPos);
      return worldPos;
    };

    // Helper function to calculate movement AABB (puzzle shape × 1.5)
    const getMovementAABB = (): THREE.Box3 => {
      const box = new THREE.Box3();
      if (containerPoints.length === 0) {
        return box.setFromCenterAndSize(new THREE.Vector3(), new THREE.Vector3(10, 10, 10));
      }
      
      containerPoints.forEach(point => box.expandByPoint(point));
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      size.multiplyScalar(MOVEMENT_AABB_SCALE);
      return box.setFromCenterAndSize(center, size);
    };

    // Helper function to find closest sphere to cursor (Active Sphere selection)
    const findActiveSphere = (pieceGroup: THREE.Object3D, mousePos: THREE.Vector2): number => {
      if (!cameraRef.current || !rendererRef.current) return 0;
      
      let closestIndex = 0;
      let minDistance = Infinity;
      
      for (let i = 0; i < pieceGroup.children.length; i++) {
        const sphere = pieceGroup.children[i];
        const screenPos = new THREE.Vector3();
        sphere.getWorldPosition(screenPos);
        screenPos.project(cameraRef.current);
        
        // Convert to screen coordinates
        const x = (screenPos.x * 0.5 + 0.5) * rendererRef.current.domElement.clientWidth;
        const y = (screenPos.y * -0.5 + 0.5) * rendererRef.current.domElement.clientHeight;
        
        // Convert mouse from NDC to screen coordinates
        const mouseX = (mousePos.x * 0.5 + 0.5) * rendererRef.current.domElement.clientWidth;
        const mouseY = (mousePos.y * -0.5 + 0.5) * rendererRef.current.domElement.clientHeight;
        
        const distance = Math.sqrt((x - mouseX) ** 2 + (y - mouseY) ** 2);
        if (distance < minDistance) {
          minDistance = distance;
          closestIndex = i;
        }
      }
      
      return closestIndex;
    };

    // Debug overlay helper functions
    const createDebugHelpers = (): THREE.Group => {
      const debugGroup = new THREE.Group();
      debugGroup.name = 'debugHelpers';
      
      // 1. Movement Box (wireframe AABB × 1.5)
      const movementAABB = getMovementAABB();
      const boxGeometry = new THREE.BoxGeometry(
        movementAABB.max.x - movementAABB.min.x,
        movementAABB.max.y - movementAABB.min.y,
        movementAABB.max.z - movementAABB.min.z
      );
      const boxMaterial = new THREE.LineBasicMaterial({ 
        color: 0x00ff00, 
        transparent: true, 
        opacity: DEBUG_OPACITY_LEVELS[debugOpacityIndex] 
      });
      const boxWireframe = new THREE.LineSegments(
        new THREE.EdgesGeometry(boxGeometry), 
        boxMaterial
      );
      const center = movementAABB.getCenter(new THREE.Vector3());
      boxWireframe.position.copy(center);
      boxWireframe.name = 'movementBox';
      debugGroup.add(boxWireframe);
      
      // Label for movement box
      const labelDiv = document.createElement('div');
      labelDiv.textContent = `movementAABB (${movementAABB.min.x.toFixed(1)},${movementAABB.min.y.toFixed(1)},${movementAABB.min.z.toFixed(1)}) to (${movementAABB.max.x.toFixed(1)},${movementAABB.max.y.toFixed(1)},${movementAABB.max.z.toFixed(1)})`;
      labelDiv.style.position = 'absolute';
      labelDiv.style.color = '#00ff00';
      labelDiv.style.fontSize = '10px';
      labelDiv.style.pointerEvents = 'none';
      labelDiv.style.opacity = DEBUG_OPACITY_LEVELS[debugOpacityIndex].toString();
      
      return debugGroup;
    };

    const updateDebugHelpers = () => {
      if (!debugMode || !sceneRef.current) return;
      
      const startTime = performance.now();
      
      // Remove existing debug helpers
      if (debugHelpersRef.current) {
        sceneRef.current.remove(debugHelpersRef.current);
      }
      
      // Create new debug helpers
      const debugGroup = createDebugHelpers();
      
      // 2. Active Sphere marker (world space)
      if (selectedPieceMeshRef.current && dragState.isDragging) {
        const activeSpherePos = getActiveSpherePosition(selectedPieceMeshRef.current, dragState.activeSphereIndex);
        
        const sphereGeometry = new THREE.SphereGeometry(0.1, 8, 8);
        const sphereMaterial = new THREE.MeshBasicMaterial({ 
          color: 0xff0000, 
          transparent: true, 
          opacity: DEBUG_OPACITY_LEVELS[debugOpacityIndex] 
        });
        const sphereMarker = new THREE.Mesh(sphereGeometry, sphereMaterial);
        sphereMarker.position.copy(activeSpherePos);
        sphereMarker.name = 'activeSphereMarker';
        debugGroup.add(sphereMarker);
        
        // Add tag near the piece
        const tagDiv = document.createElement('div');
        tagDiv.textContent = `activeSphere=${dragState.activeSphereIndex}`;
        tagDiv.style.position = 'absolute';
        tagDiv.style.color = '#ff0000';
        tagDiv.style.fontSize = '10px';
        tagDiv.style.pointerEvents = 'none';
        tagDiv.style.opacity = DEBUG_OPACITY_LEVELS[debugOpacityIndex].toString();
        
        // 3. Anchor → Sphere easing line (first 200ms)
        if (dragState.initialAnchor) {
          const currentTime = performance.now();
          const elapsedTime = currentTime - dragState.easingStartTime;
          
          if (elapsedTime <= EASING_DURATION_MS) {
            const lineGeometry = new THREE.BufferGeometry().setFromPoints([
              dragState.initialAnchor,
              activeSpherePos
            ]);
            const lineMaterial = new THREE.LineBasicMaterial({ 
              color: 0xffff00, 
              transparent: true, 
              opacity: DEBUG_OPACITY_LEVELS[debugOpacityIndex] * 0.5 
            });
            const easingLine = new THREE.Line(lineGeometry, lineMaterial);
            easingLine.name = 'easingLine';
            debugGroup.add(easingLine);
          }
        }
        
        // 4. Clamping indicator
        const aabb = getMovementAABB();
        const clampedPos = activeSpherePos.clone().clamp(aabb.min, aabb.max);
        const isClampedX = Math.abs(clampedPos.x - activeSpherePos.x) > 0.001;
        const isClampedY = Math.abs(clampedPos.y - activeSpherePos.y) > 0.001;
        const isClampedZ = Math.abs(clampedPos.z - activeSpherePos.z) > 0.001;
        
        if (isClampedX || isClampedY || isClampedZ) {
          const clampLineGeometry = new THREE.BufferGeometry().setFromPoints([
            activeSpherePos,
            clampedPos
          ]);
          const clampLineMaterial = new THREE.LineBasicMaterial({ 
            color: 0xff8800, 
            transparent: true, 
            opacity: DEBUG_OPACITY_LEVELS[debugOpacityIndex] 
          });
          const clampLine = new THREE.Line(clampLineGeometry, clampLineMaterial);
          clampLine.name = 'clampIndicator';
          debugGroup.add(clampLine);
        }
      }
      
      debugHelpersRef.current = debugGroup;
      sceneRef.current.add(debugGroup);
      
      // Performance check
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      if (renderTime > DEBUG_PERFORMANCE_BUDGET_MS) {
        console.warn(`Debug overlay exceeded performance budget: ${renderTime.toFixed(2)}ms > ${DEBUG_PERFORMANCE_BUDGET_MS}ms`);
      }
    };

    const handleMouseDown = (event: MouseEvent) => {
      if (event.button !== 0) return; // Only left mouse button
      
      if (!rendererRef.current || !cameraRef.current || !sceneRef.current) return;
      
      const rect = rendererRef.current.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, cameraRef.current);
      const intersects = raycaster.intersectObjects(sceneRef.current.children);

      console.log('Mouse down - intersects:', intersects.length, 'selectedPiece:', selectedPiece);

      if (intersects.length > 0) {
        const intersect = intersects[0];
        const userData = (intersect.object as any).userData;
        
        console.log('Intersect userData:', userData);
        
        if (userData?.type === 'selectedPiece' && userData.interactive && selectedPiece) {
          // Start dragging the selected piece using Move (Pre-Snap) behavior
          console.log('Starting drag for piece:', selectedPiece);
          event.preventDefault();
          
          const selectedMesh = selectedPieceMeshRef.current;
          if (selectedMesh) {
            // Record drag start for session stats
            recordDragStart(selectedPiece);
            
            // AC-1: Record exact mesh hit point as initial anchor (no jump)
            const initialAnchor = intersect.point.clone();
            
            // Find initial active sphere based on cursor proximity
            const initialActiveSphere = findActiveSphere(selectedMesh, mouse);
            
            // Store pre-drag transform for potential Esc cancel (AC-8)
            const preDragTransform = {
              position: selectedMesh.position.clone(),
              rotation: selectedMesh.rotation.clone()
            };
            
            // AC-3: Disable camera controls during drag
            if (controlsRef.current) {
              controlsRef.current.enabled = false;
            }
            
            setDragState({
              isDragging: true,
              initialAnchor,
              activeSphereIndex: initialActiveSphere,
              easingStartTime: performance.now(),
              preDragTransform
            });
          }
        } else if (userData?.type === 'container' && userData.position && onCellClick) {
          onCellClick(userData.position);
        }
      }
    };

    const handleMouseMove = (event: MouseEvent) => {
      if (!dragState.isDragging || !selectedPieceMeshRef.current || !cameraRef.current || !rendererRef.current) {
        return;
      }
      
      console.log('Mouse move during drag - easingProgress will be calculated');
      
      const rect = rendererRef.current.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      // Update debug cursor position
      if (debugMode) {
        setDebugCursorPos({
          x: event.clientX - rect.left,
          y: event.clientY - rect.top
        });
        updateDebugHelpers();
      }

      // AC-4: Update Active Sphere selection each frame based on cursor proximity
      const newActiveSphere = findActiveSphere(selectedPieceMeshRef.current, mouse);
      
      // Get current time for easing calculation
      const currentTime = performance.now();
      const elapsedTime = currentTime - dragState.easingStartTime;
      const easingProgress = Math.min(elapsedTime / EASING_DURATION_MS, 1.0);
      
      // Calculate target position for Active Sphere center to align with cursor
      const activeSpherePos = getActiveSpherePosition(selectedPieceMeshRef.current, newActiveSphere);
      
      // Project cursor to world space at the Active Sphere's current depth
      const cursorWorldPos = new THREE.Vector3(mouse.x, mouse.y, 0.5);
      cursorWorldPos.unproject(cameraRef.current);
      
      // Get direction from camera to cursor
      const cameraPos = cameraRef.current.position;
      const direction = cursorWorldPos.sub(cameraPos).normalize();
      
      // Calculate distance from camera to Active Sphere
      const sphereDistance = cameraPos.distanceTo(activeSpherePos);
      
      // Target position where cursor points at the sphere's distance
      const targetCursorWorld = cameraPos.clone().add(direction.multiplyScalar(sphereDistance));
      
      if (easingProgress < 1.0) {
        // AC-1: Hybrid easing phase - smooth transition from initial anchor to cursor alignment
        const initialOffset = dragState.initialAnchor!.clone().sub(activeSpherePos);
        const targetOffset = targetCursorWorld.clone().sub(activeSpherePos);
        
        // Smooth easing function (ease-out cubic)
        const t = 1 - Math.pow(1 - easingProgress, 3);
        const currentOffset = initialOffset.lerp(targetOffset, t);
        
        // AC-5: Clamp to movement AABB
        const aabb = getMovementAABB();
        const clampedActiveSpherePos = activeSpherePos.clone().add(currentOffset);
        clampedActiveSpherePos.clamp(aabb.min, aabb.max);
        
        // Adjust piece position to keep Active Sphere at clamped position
        const adjustment = clampedActiveSpherePos.clone().sub(activeSpherePos);
        selectedPieceMeshRef.current.position.add(adjustment);
      } else {
        // AC-2: After easing, cursor coincides with Active Sphere center (≤1px)
        // Calculate offset needed to align Active Sphere center with cursor world position
        const offset = targetCursorWorld.clone().sub(activeSpherePos);
        
        // AC-5: Clamp Active Sphere position to movement AABB
        const newActiveSpherePos = activeSpherePos.clone().add(offset);
        const aabb = getMovementAABB();
        const clampedActiveSpherePos = newActiveSpherePos.clone().clamp(aabb.min, aabb.max);
        
        // Apply the clamped offset to the piece
        const clampedOffset = clampedActiveSpherePos.clone().sub(activeSpherePos);
        selectedPieceMeshRef.current.position.add(clampedOffset);
      }
      
      // Update drag state with new active sphere
      setDragState(prev => ({
        ...prev,
        activeSphereIndex: newActiveSphere
      }));
      
      // Update transform in store (no snapping in this phase - AC-6)
      setSelectedPieceTransform({
        position: selectedPieceMeshRef.current.position.clone(),
        rotation: selectedPieceMeshRef.current.rotation.clone(),
        snappedToContainer: null,
        activeSphereIndex: newActiveSphere,
        candidateSnapTarget: null,
        isSnapped: false
      });
    };

    const handleMouseUp = (event: MouseEvent) => {
      if (event.button !== 0) return; // Only left mouse button
      
      if (dragState.isDragging) {
        // Record drag end for session stats
        if (selectedPiece) {
          recordDragEnd(selectedPiece);
        }
        
        // AC-7: Piece remains at final position on LMB release
        // AC-3: Re-enable camera controls
        setDragState({
          isDragging: false,
          initialAnchor: null,
          activeSphereIndex: 0,
          easingStartTime: 0,
          preDragTransform: null
        });
        
        if (controlsRef.current) {
          controlsRef.current.enabled = true;
        }
      }
    };

    const handleContextMenu = (event: MouseEvent) => {
      event.preventDefault();
    };

    const handleWheel = (event: WheelEvent) => {
      // Only handle wheel events for piece rotation if a piece is selected and mouse is over the piece
      if (!selectedPieceMeshRef.current || !selectedPieceTransform) {
        // No piece selected, allow normal camera zoom
        return;
      }
      
      // Check if mouse is over the selected piece by raycasting
      if (!rendererRef.current || !cameraRef.current) return;
      
      const rect = rendererRef.current.domElement.getBoundingClientRect();
      const wheelMouse = new THREE.Vector2();
      wheelMouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      wheelMouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(wheelMouse, cameraRef.current);
      const intersects = raycaster.intersectObject(selectedPieceMeshRef.current, true);
      
      if (intersects.length === 0) {
        // Mouse not over piece, allow normal camera zoom
        return;
      }
      
      // Mouse is over the piece, handle piece rotation and prevent camera zoom
      event.preventDefault();
      
      // Determine rotation direction
      const rotationDirection = event.deltaY > 0 ? 1 : -1;
      const rotationAngle = (Math.PI / 2) * rotationDirection; // 90 degrees
      
      // Determine rotation pivot point
      const pivotPoint = selectedPieceTransform.snappedToContainer 
        ? selectedPieceTransform.snappedToContainer.clone()
        : selectedPieceMeshRef.current.position.clone();
      
      // Apply lattice rotation around Y-axis at pivot point
      const mesh = selectedPieceMeshRef.current;
      
      // Translate to pivot
      mesh.position.sub(pivotPoint);
      
      // Rotate around Y-axis
      const rotationMatrix = new THREE.Matrix4().makeRotationY(rotationAngle);
      mesh.position.applyMatrix4(rotationMatrix);
      mesh.rotation.y += rotationAngle;
      
      // Translate back
      mesh.position.add(pivotPoint);
      
      // Update transform in store
      setSelectedPieceTransform({
        position: mesh.position.clone(),
        rotation: mesh.rotation.clone(),
        snappedToContainer: selectedPieceTransform.snappedToContainer,
        activeSphereIndex: selectedPieceTransform.activeSphereIndex,
        candidateSnapTarget: selectedPieceTransform.candidateSnapTarget,
        isSnapped: selectedPieceTransform.isSnapped
      });
    };

    // Keyboard event handlers
    const handleKeyDown = (event: KeyboardEvent) => {
      // Debug mode toggles (work regardless of piece selection)
      if (event.altKey && event.key.toLowerCase() === 'd') {
        event.preventDefault();
        if (event.shiftKey) {
          // Alt+Shift+D: cycle opacity
          setDebugOpacityIndex((prev) => (prev + 1) % DEBUG_OPACITY_LEVELS.length);
          if (debugMode) {
            updateDebugHelpers();
          }
        } else {
          // Alt+D: toggle debug mode
          setDebugMode((prev) => {
            const newMode = !prev;
            if (!newMode && debugHelpersRef.current && sceneRef.current) {
              // Clean up debug helpers when turning off
              sceneRef.current.remove(debugHelpersRef.current);
              debugHelpersRef.current = null;
            }
            return newMode;
          });
        }
        return;
      }
      
      if (!selectedPieceMeshRef.current || !selectedPieceTransform) return;
      
      switch (event.key.toLowerCase()) {
        case 'r':
          // Rotate piece (same as wheel)
          event.preventDefault();
          const rotationAngle = Math.PI / 2; // 90 degrees
          const pivotPoint = selectedPieceTransform.snappedToContainer 
            ? selectedPieceTransform.snappedToContainer.clone()
            : selectedPieceMeshRef.current.position.clone();
          
          const mesh = selectedPieceMeshRef.current;
          mesh.position.sub(pivotPoint);
          const rotationMatrix = new THREE.Matrix4().makeRotationY(rotationAngle);
          mesh.position.applyMatrix4(rotationMatrix);
          mesh.rotation.y += rotationAngle;
          mesh.position.add(pivotPoint);
          
          setSelectedPieceTransform({
            position: mesh.position.clone(),
            rotation: mesh.rotation.clone(),
            snappedToContainer: selectedPieceTransform.snappedToContainer,
            activeSphereIndex: selectedPieceTransform.activeSphereIndex,
            candidateSnapTarget: selectedPieceTransform.candidateSnapTarget,
            isSnapped: selectedPieceTransform.isSnapped
          });
          break;
          
        case 'escape':
          // Cancel drag or deselect piece
          event.preventDefault();
          if (dragState.isDragging) {
            // AC-8: Esc reverts to pre-drag state
            if (dragState.preDragTransform && selectedPieceMeshRef.current) {
              selectedPieceMeshRef.current.position.copy(dragState.preDragTransform.position);
              selectedPieceMeshRef.current.rotation.copy(dragState.preDragTransform.rotation);
              
              // Update transform in store
              setSelectedPieceTransform({
                position: dragState.preDragTransform.position.clone(),
                rotation: dragState.preDragTransform.rotation.clone(),
                snappedToContainer: null,
                activeSphereIndex: 0,
                candidateSnapTarget: null,
                isSnapped: false
              });
            }
            
            setDragState({
              isDragging: false,
              initialAnchor: null,
              activeSphereIndex: 0,
              easingStartTime: 0,
              preDragTransform: null
            });
            
            if (controlsRef.current) {
              controlsRef.current.enabled = true;
            }
          } else {
            // Deselect piece
            useAppStore.getState().setSelectedPiece(null);
            setSelectedPieceTransform(null);
          }
          break;
          
        case 'delete':
        case 'backspace':
          // Delete selected piece
          event.preventDefault();
          useAppStore.getState().setSelectedPiece(null);
          setSelectedPieceTransform(null);
          break;
          
        case 'z':
          if (event.ctrlKey || event.metaKey) {
            event.preventDefault();
            if (event.shiftKey) {
              // Ctrl+Shift+Z or Cmd+Shift+Z for redo
              undoRedoManager.redo();
            } else {
              // Ctrl+Z or Cmd+Z for undo
              undoRedoManager.undo();
            }
          }
          break;
          
        case 'y':
          if (event.ctrlKey || event.metaKey) {
            // Ctrl+Y or Cmd+Y for redo (alternative)
            event.preventDefault();
            undoRedoManager.redo();
          }
          break;
      }
    };

    // Add event listeners
    renderer.domElement.addEventListener('mousedown', handleMouseDown);
    renderer.domElement.addEventListener('mousemove', handleMouseMove);
    renderer.domElement.addEventListener('mouseup', handleMouseUp);
    renderer.domElement.addEventListener('contextmenu', handleContextMenu);
    renderer.domElement.addEventListener('wheel', handleWheel);
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      renderer.domElement.removeEventListener('mousedown', handleMouseDown);
      renderer.domElement.removeEventListener('mousemove', handleMouseMove);
      renderer.domElement.removeEventListener('mouseup', handleMouseUp);
      renderer.domElement.removeEventListener('contextmenu', handleContextMenu);
      renderer.domElement.removeEventListener('wheel', handleWheel);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [dragState, selectedPieceTransform, setSelectedPieceTransform, containerPoints, onCellClick, placedPieces]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div 
        ref={mountRef} 
        style={{ 
          width: "100%", 
          height: "100%", 
          minHeight: "400px",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          overflow: "hidden"
        }} 
      />
      
      {/* Debug HUD */}
      {debugMode && (
        <div
          style={{
            position: "absolute",
            top: "10px",
            left: "10px",
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            color: "#00ff00",
            padding: "8px",
            borderRadius: "4px",
            fontFamily: "monospace",
            fontSize: "11px",
            pointerEvents: "none",
            opacity: DEBUG_OPACITY_LEVELS[debugOpacityIndex],
            zIndex: 1000
          }}
        >
          <div>🐛 DEBUG MODE</div>
          <div>drag={dragState.isDragging ? "ON" : "OFF"}</div>
          <div>cursor=({debugCursorPos.x.toFixed(0)},{debugCursorPos.y.toFixed(0)})</div>
          {selectedPieceMeshRef.current && dragState.isDragging && (
            <>
              <div>activeSphere={dragState.activeSphereIndex}</div>
              <div>cameraLocked={controlsRef.current ? !controlsRef.current.enabled : false}</div>
              <div>easingProgress={Math.min((performance.now() - dragState.easingStartTime) / EASING_DURATION_MS, 1.0).toFixed(2)}</div>
            </>
          )}
          <div style={{ marginTop: "4px", fontSize: "9px", opacity: 0.7 }}>
            Alt+D: toggle | Alt+Shift+D: opacity
          </div>
        </div>
      )}
    </div>
  );
};
