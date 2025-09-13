import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface UnifiedPieceProps {
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
  scene: THREE.Scene;
}

export const UnifiedPiece: React.FC<UnifiedPieceProps> = ({
  piece,
  spheres,
  bonds,
  scene
}) => {
  const groupRef = useRef<THREE.Group | null>(null);

  useEffect(() => {
    if (!scene) return;

    console.log(`UnifiedPiece: Creating piece ${piece} with ${spheres.positions.length / 3} spheres and ${bonds.positions.length / 6} bonds`);
    console.log(`UnifiedPiece: Sphere radius: ${spheres.radius}, Bond radius: ${bonds.radius}`);

    // Create a group to hold both spheres and bonds
    const pieceGroup = new THREE.Group();
    pieceGroup.userData = {
      type: 'UnifiedPiece',
      piece: piece
    };

    // Create sphere instances
    if (spheres.positions.length > 0) {
      const sphereCount = spheres.positions.length / 3;
      const sphereGeometry = new THREE.SphereGeometry(spheres.radius, 16, 12);
      const sphereMaterial = new THREE.MeshStandardMaterial({
        metalness: 0.3,
        roughness: 0.4,
        envMapIntensity: 0.8
      });
      
      const sphereInstancedMesh = new THREE.InstancedMesh(
        sphereGeometry,
        sphereMaterial,
        sphereCount
      );
      
      // Set up sphere instances
      const matrix = new THREE.Matrix4();
      const color = new THREE.Color();
      
      for (let i = 0; i < sphereCount; i++) {
        const x = spheres.positions[i * 3];
        const y = spheres.positions[i * 3 + 1];
        const z = spheres.positions[i * 3 + 2];
        
        matrix.setPosition(x, y, z);
        sphereInstancedMesh.setMatrixAt(i, matrix);
        
        color.setRGB(
          spheres.colors[i * 3],
          spheres.colors[i * 3 + 1],
          spheres.colors[i * 3 + 2]
        );
        sphereInstancedMesh.setColorAt(i, color);
      }
      
      sphereInstancedMesh.instanceMatrix.needsUpdate = true;
      if (sphereInstancedMesh.instanceColor) {
        sphereInstancedMesh.instanceColor.needsUpdate = true;
      }
      
      sphereInstancedMesh.userData = {
        type: 'InstancedSpheres',
        piece: piece
      };
      
      pieceGroup.add(sphereInstancedMesh);
    }

    // Create bond instances
    if (bonds.positions.length > 0) {
      const bondCount = bonds.positions.length / 6; // 2 points per bond
      const bondGeometry = new THREE.CylinderGeometry(bonds.radius, bonds.radius, 1, 8);
      const bondMaterial = new THREE.MeshStandardMaterial({
        metalness: 0.3,
        roughness: 0.4,
        envMapIntensity: 0.8
      });
      
      const bondInstancedMesh = new THREE.InstancedMesh(
        bondGeometry,
        bondMaterial,
        bondCount
      );
      
      // Set up bond instances
      const matrix = new THREE.Matrix4();
      const color = new THREE.Color();
      const start = new THREE.Vector3();
      const end = new THREE.Vector3();
      const direction = new THREE.Vector3();
      const quaternion = new THREE.Quaternion();
      const up = new THREE.Vector3(0, 1, 0);
      
      for (let i = 0; i < bondCount; i++) {
        start.set(
          bonds.positions[i * 6],
          bonds.positions[i * 6 + 1],
          bonds.positions[i * 6 + 2]
        );
        end.set(
          bonds.positions[i * 6 + 3],
          bonds.positions[i * 6 + 4],
          bonds.positions[i * 6 + 5]
        );
        
        // Calculate bond center, length, and orientation
        const center = start.clone().add(end).multiplyScalar(0.5);
        const length = start.distanceTo(end);
        direction.subVectors(end, start).normalize();
        
        // Create rotation quaternion to align cylinder with bond direction
        quaternion.setFromUnitVectors(up, direction);
        
        // Set matrix with position, rotation, and scale
        matrix.compose(center, quaternion, new THREE.Vector3(1, length, 1));
        bondInstancedMesh.setMatrixAt(i, matrix);
        
        color.setRGB(
          bonds.colors[i * 3],
          bonds.colors[i * 3 + 1],
          bonds.colors[i * 3 + 2]
        );
        bondInstancedMesh.setColorAt(i, color);
      }
      
      bondInstancedMesh.instanceMatrix.needsUpdate = true;
      if (bondInstancedMesh.instanceColor) {
        bondInstancedMesh.instanceColor.needsUpdate = true;
      }
      
      bondInstancedMesh.userData = {
        type: 'InstancedBonds',
        piece: piece
      };
      
      pieceGroup.add(bondInstancedMesh);
    }

    // Add the unified piece group to the scene
    scene.add(pieceGroup);
    groupRef.current = pieceGroup;

    // Cleanup function
    return () => {
      if (groupRef.current) {
        scene.remove(groupRef.current);
        
        // Dispose of geometries and materials
        groupRef.current.traverse((child) => {
          if (child instanceof THREE.InstancedMesh) {
            child.geometry.dispose();
            if (Array.isArray(child.material)) {
              child.material.forEach(material => material.dispose());
            } else {
              child.material.dispose();
            }
          }
        });
        
        groupRef.current = null;
      }
    };
  }, [scene, piece, spheres, bonds]);

  return null; // This component doesn't render anything directly
};
