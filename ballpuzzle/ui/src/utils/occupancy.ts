import * as THREE from 'three';
import { useAppStore } from '../store';

/**
 * Get all currently occupied cells from placed pieces
 */
export function getOccupiedCells(): THREE.Vector3[] {
  const state = useAppStore.getState();
  return state.placedPieces.flatMap(p => p.occupiedCells);
}

/**
 * Check if a cell is occupied by any placed piece
 */
export function isCellOccupied(cell: THREE.Vector3, tolerance = 0.1): boolean {
  const occupiedCells = getOccupiedCells();
  return occupiedCells.some(occupied => 
    Math.abs(occupied.x - cell.x) < tolerance &&
    Math.abs(occupied.y - cell.y) < tolerance &&
    Math.abs(occupied.z - cell.z) < tolerance
  );
}

/**
 * Calculate which cells a piece would occupy at a given position and rotation
 */
export function calculatePieceOccupancy(
  piece: any, 
  position: THREE.Vector3, 
  rotation: THREE.Euler
): THREE.Vector3[] {
  if (!piece || !piece.spheres) return [];
  
  const occupiedCells: THREE.Vector3[] = [];
  
  // Create transformation matrix
  const matrix = new THREE.Matrix4();
  matrix.makeRotationFromEuler(rotation);
  matrix.setPosition(position);
  
  // Transform each sphere position to world coordinates
  piece.spheres.forEach((sphere: any) => {
    const localPos = new THREE.Vector3(sphere.x, sphere.y, sphere.z);
    const worldPos = localPos.clone().applyMatrix4(matrix);
    occupiedCells.push(worldPos);
  });
  
  return occupiedCells;
}

/**
 * Check if placing a piece at a position would cause collision
 */
export function wouldCauseCollision(
  piece: any,
  position: THREE.Vector3,
  rotation: THREE.Euler,
  excludePieceId?: string
): boolean {
  const pieceOccupancy = calculatePieceOccupancy(piece, position, rotation);
  const state = useAppStore.getState();
  
  // Get occupied cells excluding the specified piece
  const occupiedCells = state.placedPieces
    .filter(p => p.id !== excludePieceId)
    .flatMap(p => p.occupiedCells);
  
  return pieceOccupancy.some(pieceCell =>
    occupiedCells.some(occupied =>
      Math.abs(occupied.x - pieceCell.x) < 0.1 &&
      Math.abs(occupied.y - pieceCell.y) < 0.1 &&
      Math.abs(occupied.z - pieceCell.z) < 0.1
    )
  );
}
