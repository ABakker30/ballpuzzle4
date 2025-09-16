import * as THREE from 'three';
import { useAppStore } from '../store';

export interface SolutionValidationResult {
  isComplete: boolean;
  isCorrect: boolean;
  completionPercentage: number;
  missingCells: THREE.Vector3[];
  incorrectPlacements: string[];
  stats: {
    totalCells: number;
    filledCells: number;
    correctPlacements: number;
  };
}

/**
 * Check if the puzzle is complete and correct
 */
export function validateSolution(
  containerPoints: THREE.Vector3[],
  placedPieces: Array<{ piece: string; position: any; rotation: any; id: string; occupiedCells: THREE.Vector3[] }>
): SolutionValidationResult {
  const totalCells = containerPoints.length;
  const occupiedCells = placedPieces.flatMap(p => p.occupiedCells);
  
  // Find which container cells are filled
  const filledCells: THREE.Vector3[] = [];
  const missingCells: THREE.Vector3[] = [];
  
  containerPoints.forEach(containerCell => {
    const isOccupied = occupiedCells.some(occupiedCell =>
      Math.abs(occupiedCell.x - containerCell.x) < 0.1 &&
      Math.abs(occupiedCell.y - containerCell.y) < 0.1 &&
      Math.abs(occupiedCell.z - containerCell.z) < 0.1
    );
    
    if (isOccupied) {
      filledCells.push(containerCell);
    } else {
      missingCells.push(containerCell);
    }
  });
  
  const completionPercentage = (filledCells.length / totalCells) * 100;
  const isComplete = filledCells.length === totalCells;
  
  // For now, assume correct if complete (can be enhanced with specific solution validation)
  const isCorrect = isComplete;
  const incorrectPlacements: string[] = [];
  
  return {
    isComplete,
    isCorrect,
    completionPercentage,
    missingCells,
    incorrectPlacements,
    stats: {
      totalCells,
      filledCells: filledCells.length,
      correctPlacements: filledCells.length
    }
  };
}

/**
 * Check for symmetry-aware solution validation
 */
export function validateSolutionWithSymmetry(
  containerPoints: THREE.Vector3[],
  placedPieces: Array<{ piece: string; position: any; rotation: any; id: string; occupiedCells: THREE.Vector3[] }>,
  expectedSolution?: Array<{ piece: string; position: THREE.Vector3; rotation: THREE.Euler }>
): SolutionValidationResult {
  const basicValidation = validateSolution(containerPoints, placedPieces);
  
  if (!basicValidation.isComplete) {
    return basicValidation;
  }
  
  // If we have an expected solution, validate against it
  if (expectedSolution) {
    const incorrectPlacements: string[] = [];
    
    placedPieces.forEach(placedPiece => {
      const expectedPiece = expectedSolution.find(exp => exp.piece === placedPiece.piece);
      if (expectedPiece) {
        const positionMatch = Math.abs(placedPiece.position.x - expectedPiece.position.x) < 0.1 &&
                             Math.abs(placedPiece.position.y - expectedPiece.position.y) < 0.1 &&
                             Math.abs(placedPiece.position.z - expectedPiece.position.z) < 0.1;
        
        if (!positionMatch) {
          incorrectPlacements.push(placedPiece.id);
        }
      }
    });
    
    return {
      ...basicValidation,
      isCorrect: incorrectPlacements.length === 0,
      incorrectPlacements
    };
  }
  
  return basicValidation;
}

/**
 * Get completion statistics for display
 */
export function getCompletionStats(
  containerPoints: THREE.Vector3[],
  placedPieces: Array<{ piece: string; position: any; rotation: any; id: string; occupiedCells: THREE.Vector3[] }>
) {
  const validation = validateSolution(containerPoints, placedPieces);
  
  return {
    percentage: Math.round(validation.completionPercentage),
    filled: validation.stats.filledCells,
    total: validation.stats.totalCells,
    remaining: validation.stats.totalCells - validation.stats.filledCells,
    isComplete: validation.isComplete
  };
}
