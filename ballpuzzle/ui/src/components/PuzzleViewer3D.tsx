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
  dragStart: THREE.Vector2;
  dragPlane: THREE.Plane;
  dragOffset: THREE.Vector3;
}

// Snap targeting constants
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
    dragStart: new THREE.Vector2(),
    dragPlane: new THREE.Plane(),
    dragOffset: new THREE.Vector3()
  });
  const [cameraInitialized, setCameraInitialized] = useState(false);

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

    const handleMouseDown = (event: MouseEvent) => {
      if (event.button !== 0) return; // Only left mouse button
      
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(scene.children);

      if (intersects.length > 0) {
        const intersect = intersects[0];
        const userData = (intersect.object as any).userData;
        
        if (userData?.type === 'selectedPiece' && userData.interactive) {
          // Start dragging the selected piece
          event.preventDefault();
          controls.enabled = false;
          
          const selectedMesh = selectedPieceMeshRef.current;
          if (selectedMesh) {
            // Create drag plane perpendicular to camera
            const cameraDirection = new THREE.Vector3();
            camera.getWorldDirection(cameraDirection);
            const dragPlane = new THREE.Plane(cameraDirection, -intersect.distance);
            
            // Calculate offset from piece center to intersection point
            const dragOffset = new THREE.Vector3();
            dragOffset.subVectors(selectedMesh.position, intersect.point);
            
            setDragState({
              isDragging: true,
              dragStart: mouse.clone(),
              dragPlane,
              dragOffset
            });
          }
        } else if (userData?.type === 'container' && userData.position && onCellClick) {
          onCellClick(userData.position);
        }
      }
    };

    const handleMouseMove = (event: MouseEvent) => {
      if (!dragState.isDragging || !selectedPieceMeshRef.current) return;
      
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      
      const intersectPoint = new THREE.Vector3();
      if (raycaster.ray.intersectPlane(dragState.dragPlane, intersectPoint)) {
        const newPosition = intersectPoint.add(dragState.dragOffset);
        selectedPieceMeshRef.current.position.copy(newPosition);
        
        // Check for snapping to container points using active sphere position
        const activeSpherePos = getActiveSpherePosition(selectedPieceMeshRef.current, selectedPieceTransform?.activeSphereIndex || 0);
        const snapResult = findClosestContainerPoint(activeSpherePos);
        
        let candidateTarget = null;
        let snapPoint = null;
        
        if (snapResult && snapResult.distance <= SNAP_RADIUS) {
          // Check if target cell is occupied
          const isTargetOccupied = isCellOccupied(snapResult.point);
          
          if (!isTargetOccupied) {
            candidateTarget = snapResult.point;
            
            // Check for collision with other pieces
            const wouldCollide = selectedPiece && wouldCauseCollision(
              selectedPiece,
              selectedPieceMeshRef.current.position,
              selectedPieceMeshRef.current.rotation
            );
            
            if (!wouldCollide && snapResult.distance <= AUTO_SNAP_RADIUS) {
              snapPoint = snapResult.point;
              // Auto-snap: align active sphere to target cell
              const offset = new THREE.Vector3().subVectors(snapResult.point, activeSpherePos);
              selectedPieceMeshRef.current.position.add(offset);
            }
          }
        }
        
        // Update transform in store
        setSelectedPieceTransform({
          position: selectedPieceMeshRef.current.position.clone(),
          rotation: selectedPieceMeshRef.current.rotation.clone(),
          snappedToContainer: snapPoint,
          activeSphereIndex: selectedPieceTransform?.activeSphereIndex || 0,
          candidateSnapTarget: candidateTarget,
          isSnapped: snapPoint !== null
        });
        
        // If piece is snapped, place it permanently
        if (selectedPieceTransform?.isSnapped && selectedPiece && selectedPieceMeshRef.current) {
          const occupiedCells = calculatePieceOccupancy(
            selectedPiece,
            selectedPieceMeshRef.current.position,
            selectedPieceMeshRef.current.rotation
          );
          
          // Add to placed pieces
          const placedPiece = {
            piece: selectedPiece,
            position: selectedPieceMeshRef.current.position.clone(),
            rotation: selectedPieceMeshRef.current.rotation.clone(),
            id: `placed_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            occupiedCells
          };
          
          useAppStore.getState().addPlacedPiece(placedPiece);
          
          // Record action for undo/redo
          recordUndoPlacement(placedPiece);
          
          // Record session statistics
          recordPiecePlacement(selectedPiece, {
            x: selectedPieceMeshRef.current.position.x,
            y: selectedPieceMeshRef.current.position.y,
            z: selectedPieceMeshRef.current.position.z
          });
          recordSnap(selectedPiece, {
            x: selectedPieceMeshRef.current.position.x,
            y: selectedPieceMeshRef.current.position.y,
            z: selectedPieceMeshRef.current.position.z
          });
          
          // Check for solution completion
          const validationResult = validateSolution(containerPoints, [...useAppStore.getState().placedPieces, placedPiece]);
          if (validationResult.isComplete && onSolutionComplete) {
            onSolutionComplete(validationResult);
          }
          
          // Clear selected piece
          useAppStore.getState().setSelectedPiece(null);
          setSelectedPieceTransform(null);
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
      const rect = renderer.domElement.getBoundingClientRect();
      const mouse = new THREE.Vector2();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
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
            setDragState({
              isDragging: false,
              dragStart: new THREE.Vector2(),
              dragPlane: new THREE.Plane(),
              dragOffset: new THREE.Vector3()
            });
            controls.enabled = true;
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
  );
};
