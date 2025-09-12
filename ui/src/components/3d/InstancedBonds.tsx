import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface InstancedBondsProps {
  positions: Float32Array; // [x1, y1, z1, x2, y2, z2, ...] for each bond
  colors: Float32Array;    // [r, g, b, r, g, b, ...] for each bond
  radius: number;
  scene: THREE.Scene;
}

export const InstancedBonds: React.FC<InstancedBondsProps> = ({
  positions,
  colors,
  radius,
  scene
}) => {
  const meshRef = useRef<THREE.InstancedMesh | null>(null);

  useEffect(() => {
    if (!scene || positions.length === 0) return;

    const bondCount = positions.length / 6; // Each bond has 2 points (6 coordinates)
    
    // Create cylinder geometry for bonds - match sphere material with higher quality
    const geometry = new THREE.CylinderGeometry(radius * 0.3, radius * 0.3, 1, 16, 1);
    const material = new THREE.MeshStandardMaterial({
      color: 0xffffff, // White base - colors will be set per instance
      metalness: 0.3,   // More reflective
      roughness: 0.4,   // Smoother surface
      emissive: 0x111111, // Slight glow for brightness
      emissiveIntensity: 0.1,
    });
    
    const mesh = new THREE.InstancedMesh(geometry, material, bondCount);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    meshRef.current = mesh;

    // Create instance matrices and colors
    const instanceMatrix = new THREE.Matrix4();
    
    for (let i = 0; i < bondCount; i++) {
      const startIdx = i * 6;
      
      // Get start and end points
      const start = new THREE.Vector3(
        positions[startIdx],
        positions[startIdx + 1], 
        positions[startIdx + 2]
      );
      const end = new THREE.Vector3(
        positions[startIdx + 3],
        positions[startIdx + 4],
        positions[startIdx + 5]
      );
      
      // Calculate bond center, length, and orientation
      const center = start.clone().add(end).multiplyScalar(0.5);
      const direction = end.clone().sub(start);
      const length = direction.length();
      
      // Create transformation matrix - start with identity
      instanceMatrix.identity();
      
      // Rotate cylinder to align with bond direction first
      if (length > 0) {
        direction.normalize();
        const up = new THREE.Vector3(0, 1, 0);
        
        // Calculate rotation to align cylinder with bond direction
        const quaternion = new THREE.Quaternion();
        quaternion.setFromUnitVectors(up, direction);
        
        const rotationMatrix = new THREE.Matrix4().makeRotationFromQuaternion(quaternion);
        instanceMatrix.multiply(rotationMatrix);
      }
      
      // Scale cylinder to bond length
      const scaleMatrix = new THREE.Matrix4().makeScale(1, length, 1);
      instanceMatrix.multiply(scaleMatrix);
      
      // Translate to bond center
      const translationMatrix = new THREE.Matrix4().makeTranslation(center.x, center.y, center.z);
      instanceMatrix.premultiply(translationMatrix);
      
      mesh.setMatrixAt(i, instanceMatrix);
    }
    
    // Set instance colors using the same approach as InstancedSpheres
    if (colors && colors.length >= bondCount * 3) {
      mesh.instanceColor = new THREE.InstancedBufferAttribute(colors, 3);
      mesh.instanceColor.needsUpdate = true;
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
    };
  }, [scene, positions, colors, radius]);

  return null;
};
