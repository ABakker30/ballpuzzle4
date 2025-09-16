import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
interface PuzzleViewer3DProps {
  containerPoints: THREE.Vector3[];
  placedPieces: Array<{ piece: string; position: any; rotation: any; id: string }>;
  onCellClick?: (position: THREE.Vector3) => void;
  hullFaces?: Array<{
    normal: THREE.Vector3;
    vertices: THREE.Vector3[];
    isLargest: boolean;
  }>;
}

export const PuzzleViewer3D: React.FC<PuzzleViewer3DProps> = ({ 
  containerPoints, 
  placedPieces, 
  onCellClick,
  hullFaces
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const cameraRef = useRef<THREE.PerspectiveCamera>();
  const controlsRef = useRef<OrbitControls>();

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
      child.userData.type === 'hull'
    );
    objectsToRemove.forEach(obj => scene.remove(obj));

    // Add container points
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
        const sphere = new THREE.Mesh(containerGeometry, containerMaterial);
        sphere.position.set(point.x, point.y, point.z);
        sphere.castShadow = true;
        sphere.receiveShadow = true;
        (sphere as any).userData = { type: 'container', index, position: point };
        scene.add(sphere);
      });

      // Auto-fit camera to container
      if (cameraRef.current && controlsRef.current) {
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

  }, [containerPoints, placedPieces, hullFaces]);

  // Handle clicks
  useEffect(() => {
    const renderer = rendererRef.current;
    const camera = cameraRef.current;
    const scene = sceneRef.current;
    
    if (!renderer || !camera || !scene || !onCellClick) return;

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handleClick = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(scene.children);

      if (intersects.length > 0) {
        const intersect = intersects[0];
        const userData = (intersect.object as any).userData;
        
        if (userData?.type === 'container' && userData.position) {
          onCellClick(userData.position);
        }
      }
    };

    renderer.domElement.addEventListener('click', handleClick);
    return () => {
      renderer.domElement.removeEventListener('click', handleClick);
    };
  }, [onCellClick]);

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
