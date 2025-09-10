import { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { Vector3, pieceColor } from '../../lib/fcc';

export interface InstancedSpheresProps {
  positions: Float32Array | Vector3[];
  radius?: number;
  colorByPiece?: boolean;
  pieceIndices?: number[];
  scene?: THREE.Scene | null;
}

export const InstancedSpheres: React.FC<InstancedSpheresProps> = ({
  positions,
  radius = 0.5,
  colorByPiece = false,
  pieceIndices = [],
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
    const geometry = new THREE.SphereGeometry(radius, 16, 12);
    const material = new THREE.MeshStandardMaterial({
      color: 0x00a0db, // R0, G160, B219
      metalness: 0.1,
      roughness: 0.4,
      emissive: 0x000000, // No glow for matte finish
      emissiveIntensity: 0.0,
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

    // Update instance colors if needed
    if (colorByPiece && pieceIndices.length > 0) {
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
  }, [positions, radius, colorByPiece, pieceIndices, scene]);

  return null; // This component manages Three.js objects directly
};
