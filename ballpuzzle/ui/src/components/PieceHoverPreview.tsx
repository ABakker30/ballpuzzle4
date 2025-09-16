import React, { useRef, useEffect } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { fccToWorld } from "../lib/fcc";

// Use analytic FCC sphere radius calculation
function calculateSphereRadius(a: number = 1): number {
  // For FCC lattice with spacing 'a', nearest neighbor distance is a/√2
  // Sphere radius for touching spheres is half that: a/(2√2)
  return a / (2 * Math.sqrt(2));
}

// Calculate the minimum distance between adjacent FCC neighbors in world coordinates
function calculateMinDistance(coordinates: number[][]): number {
  const worldPoints = coordinates.map(([i, j, k]) => fccToWorld(i, j, k, 1));
  let minDistance = Infinity;
  
  // Check only FCC-adjacent pairs, not all pairs
  for (let i = 0; i < coordinates.length; i++) {
    for (let j = i + 1; j < coordinates.length; j++) {
      const [i1, j1, k1] = coordinates[i];
      const [i2, j2, k2] = coordinates[j];
      
      // Check if coordinates are adjacent in FCC lattice
      const di = Math.abs(i1 - i2);
      const dj = Math.abs(j1 - j2);
      const dk = Math.abs(k1 - k2);
      
      // FCC adjacency: exactly one coordinate differs by 1, others same OR
      // all three coordinates differ by 1 (diagonal neighbor)
      const isAdjacent = (di === 1 && dj === 0 && dk === 0) ||
                        (di === 0 && dj === 1 && dk === 0) ||
                        (di === 0 && dj === 0 && dk === 1) ||
                        (di === 1 && dj === 1 && dk === 1);
      
      if (isAdjacent) {
        const p1 = worldPoints[i];
        const p2 = worldPoints[j];
        const distance = Math.sqrt(
          Math.pow(p1.x - p2.x, 2) + 
          Math.pow(p1.y - p2.y, 2) + 
          Math.pow(p1.z - p2.z, 2)
        );
        minDistance = Math.min(minDistance, distance);
      }
    }
  }
  
  // If no adjacent pairs found, use a default FCC distance
  if (minDistance === Infinity) {
    minDistance = 1.0; // Default FCC nearest neighbor distance
  }
  
  return minDistance;
}

interface PieceHoverPreviewProps {
  piece: string;
  coordinates: number[][];
  color: string;
  onClose: () => void;
  onSelect: () => void;
}

export function PieceHoverPreview({ piece, coordinates, color, onClose, onSelect }: PieceHoverPreviewProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const cameraRef = useRef<THREE.PerspectiveCamera>();
  const controlsRef = useRef<OrbitControls>();

  useEffect(() => {
    if (!mountRef.current) return;

    const mount = mountRef.current;
    const width = 600;
    const height = 600;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8f9fa);
    
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(3, 3, 3);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enableZoom = true;
    controls.enablePan = false;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(5, 5, 5);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Convert coordinates to world positions
    const worldPoints = coordinates.map(([i, j, k]) => fccToWorld(i, j, k, 1));
    
    // Use analytic sphere radius for FCC lattice (a=1)
    const sphereRadius = calculateSphereRadius(1);
    
    // Calculate center for positioning
    const center = new THREE.Vector3();
    worldPoints.forEach(point => {
      center.add(new THREE.Vector3(point.x, point.y, point.z));
    });
    center.divideScalar(worldPoints.length);

    // Create spheres for each coordinate with calculated radius and higher quality
    const sphereGeometry = new THREE.SphereGeometry(sphereRadius, 32, 32);
    const sphereMaterial = new THREE.MeshStandardMaterial({ 
      color: new THREE.Color(color),
      metalness: 0.1,
      roughness: 0.4
    });

    worldPoints.forEach(point => {
      const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
      sphere.position.set(
        point.x - center.x,
        point.y - center.y,
        point.z - center.z
      );
      sphere.castShadow = true;
      sphere.receiveShadow = true;
      scene.add(sphere);
    });

    // Auto-fit camera to piece
    const box = new THREE.Box3();
    worldPoints.forEach(point => {
      box.expandByPoint(new THREE.Vector3(
        point.x - center.x,
        point.y - center.y,
        point.z - center.z
      ));
    });
    
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    camera.position.set(maxDim * 1.5, maxDim * 1.5, maxDim * 1.5);
    controls.target.set(0, 0, 0);
    controls.update();

    // Store refs
    sceneRef.current = scene;
    rendererRef.current = renderer;
    cameraRef.current = camera;
    controlsRef.current = controls;

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
      controls.dispose();
      renderer.dispose();
      if (mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [coordinates, color]);

  return (
    <div
      style={{
        position: "fixed",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        backgroundColor: "white",
        border: "2px solid var(--border)",
        borderRadius: "12px",
        padding: "16px",
        boxShadow: "0 8px 24px rgba(0, 0, 0, 0.2)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "12px"
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
        <h3 style={{ margin: 0, fontSize: "18px", fontWeight: "bold" }}>Piece {piece}</h3>
        <button
          onClick={onClose}
          style={{
            background: "none",
            border: "none",
            fontSize: "20px",
            cursor: "pointer",
            padding: "4px",
            color: "var(--text-muted)"
          }}
        >
          ×
        </button>
      </div>
      
      <div
        ref={mountRef}
        onDoubleClick={onSelect}
        style={{
          width: "600px",
          height: "600px",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          overflow: "hidden",
          cursor: "grab"
        }}
      />
      
      <div style={{ textAlign: "center", fontSize: "14px", color: "var(--text-muted)" }}>
        <p style={{ margin: 0, fontSize: "12px" }}>Click and drag to rotate • Double-click to select</p>
      </div>
    </div>
  );
}
