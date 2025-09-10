import { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { Vector3, pieceColor } from '../../lib/fcc';

export interface InstancedSpheresProps {
  positions: Float32Array | Vector3[];
  radius?: number;
  colorByPiece?: boolean;
  pieceIndices?: number[];
  colors?: Float32Array;
  scene?: THREE.Scene | null;
}

export const InstancedSpheres: React.FC<InstancedSpheresProps> = ({
  positions,
  radius = 0.5,
  colorByPiece = false,
  pieceIndices = [],
  colors,
  scene
}) => {
  const meshRef = useRef<THREE.InstancedMesh | null>(null);

  useEffect(() => {
    if (!scene) {
      console.log('InstancedSpheres: No scene provided');
      return;
    }

    // Calculate instance count
    const instanceCount = positions instanceof Float32Array 
      ? positions.length / 3 
      : positions.length;
    
    console.log(`InstancedSpheres: Processing ${instanceCount} instances, scene:`, scene);

    if (instanceCount === 0) {
      if (meshRef.current) {
        scene.remove(meshRef.current);
        meshRef.current = null;
      }
      return;
    }

    // Create geometry and material
    const geometry = new THREE.SphereGeometry(radius, 32, 24); // Higher resolution for better normals
    const material = new THREE.MeshStandardMaterial({
      color: 0xffffff, // White base - colors will be set per instance
      metalness: 0.3,   // More reflective
      roughness: 0.4,   // Smoother surface
      emissive: 0x111111, // Slight glow for brightness
      emissiveIntensity: 0.1,
    });

    // Remove old mesh if exists
    if (meshRef.current) {
      scene.remove(meshRef.current);
    }

    // Create new instanced mesh
    const mesh = new THREE.InstancedMesh(geometry, material, instanceCount);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    meshRef.current = mesh;

    // Update instance matrices
    const matrix = new THREE.Matrix4();
    for (let i = 0; i < instanceCount; i++) {
      let x, y, z;
      
      if (positions instanceof Float32Array) {
        x = positions[i * 3];
        y = positions[i * 3 + 1];
        z = positions[i * 3 + 2];
      } else {
        const pos = positions[i];
        x = pos.x;
        y = pos.y;
        z = pos.z;
      }

      matrix.setPosition(x, y, z);
      mesh.setMatrixAt(i, matrix);
    }

    // Always set instance colors - this is critical for per-piece coloring
    if (colors && colors.length >= instanceCount * 3) {
      // Use provided colors array
      console.log('InstancedSpheres: Setting instance colors from provided array, length:', colors.length);
      mesh.instanceColor = new THREE.InstancedBufferAttribute(colors, 3);
      mesh.instanceColor.needsUpdate = true;
    } else if (colorByPiece && pieceIndices.length > 0) {
      // Use piece-based coloring
      mesh.instanceColor = new THREE.InstancedBufferAttribute(
        new Float32Array(instanceCount * 3), 
        3
      );

      const color = new THREE.Color();
      for (let i = 0; i < instanceCount; i++) {
        const pieceIndex = pieceIndices[i] || 0;
        const hexColor = pieceColor(pieceIndex);
        color.setHex(parseInt(hexColor.slice(1), 16));
        
        mesh.instanceColor.setXYZ(i, color.r, color.g, color.b);
      }
      mesh.instanceColor.needsUpdate = true;
    } else {
      // Fallback: set default white color for all instances
      console.log('InstancedSpheres: No colors provided, setting default white');
      const defaultColors = new Float32Array(instanceCount * 3);
      for (let i = 0; i < instanceCount * 3; i += 3) {
        defaultColors[i] = 1.0;     // R
        defaultColors[i + 1] = 1.0; // G  
        defaultColors[i + 2] = 1.0; // B
      }
      mesh.instanceColor = new THREE.InstancedBufferAttribute(defaultColors, 3);
      mesh.instanceColor.needsUpdate = true;
    }

    mesh.instanceMatrix.needsUpdate = true;
    scene.add(mesh);
    console.log(`InstancedSpheres: Added mesh with ${instanceCount} instances to scene, mesh:`, mesh);

    // Cleanup
    return () => {
      if (meshRef.current) {
        scene.remove(meshRef.current);
        geometry.dispose();
        material.dispose();
      }
    };
  }, [positions, radius, colorByPiece, pieceIndices, colors, scene]);

  return null; // This component manages Three.js objects directly
};
