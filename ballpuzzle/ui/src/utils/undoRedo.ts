import * as THREE from 'three';
import { useAppStore } from '../store';

export interface UndoRedoAction {
  type: 'PLACE_PIECE' | 'REMOVE_PIECE' | 'ROTATE_PIECE' | 'MOVE_PIECE';
  timestamp: number;
  pieceId?: string;
  pieceName?: string;
  beforeState?: {
    position?: THREE.Vector3;
    rotation?: THREE.Euler;
    occupiedCells?: THREE.Vector3[];
  };
  afterState?: {
    position?: THREE.Vector3;
    rotation?: THREE.Euler;
    occupiedCells?: THREE.Vector3[];
  };
  placedPiece?: {
    piece: string;
    position: any;
    rotation: any;
    id: string;
    occupiedCells: THREE.Vector3[];
  };
}

class UndoRedoManager {
  private undoStack: UndoRedoAction[] = [];
  private redoStack: UndoRedoAction[] = [];
  private maxStackSize = 50;

  addAction(action: UndoRedoAction) {
    // Clear redo stack when new action is added
    this.redoStack = [];
    
    // Add to undo stack
    this.undoStack.push(action);
    
    // Limit stack size
    if (this.undoStack.length > this.maxStackSize) {
      this.undoStack.shift();
    }
  }

  canUndo(): boolean {
    return this.undoStack.length > 0;
  }

  canRedo(): boolean {
    return this.redoStack.length > 0;
  }

  undo(): boolean {
    if (!this.canUndo()) return false;

    const action = this.undoStack.pop()!;
    const store = useAppStore.getState();

    switch (action.type) {
      case 'PLACE_PIECE':
        // Remove the placed piece
        if (action.pieceId) {
          store.removePlacedPiece(action.pieceId);
        }
        break;

      case 'REMOVE_PIECE':
        // Restore the removed piece
        if (action.placedPiece) {
          store.addPlacedPiece(action.placedPiece);
        }
        break;

      case 'ROTATE_PIECE':
      case 'MOVE_PIECE':
        // Restore previous position/rotation
        if (action.pieceId && action.beforeState) {
          const placedPieces = store.placedPieces;
          const pieceIndex = placedPieces.findIndex(p => p.id === action.pieceId);
          
          if (pieceIndex !== -1) {
            const updatedPieces = [...placedPieces];
            updatedPieces[pieceIndex] = {
              ...updatedPieces[pieceIndex],
              position: action.beforeState.position || updatedPieces[pieceIndex].position,
              rotation: action.beforeState.rotation || updatedPieces[pieceIndex].rotation,
              occupiedCells: action.beforeState.occupiedCells || updatedPieces[pieceIndex].occupiedCells
            };
            store.setPlacedPieces(updatedPieces);
          }
        }
        break;
    }

    // Move action to redo stack
    this.redoStack.push(action);
    return true;
  }

  redo(): boolean {
    if (!this.canRedo()) return false;

    const action = this.redoStack.pop()!;
    const store = useAppStore.getState();

    switch (action.type) {
      case 'PLACE_PIECE':
        // Re-place the piece
        if (action.placedPiece) {
          store.addPlacedPiece(action.placedPiece);
        }
        break;

      case 'REMOVE_PIECE':
        // Re-remove the piece
        if (action.pieceId) {
          store.removePlacedPiece(action.pieceId);
        }
        break;

      case 'ROTATE_PIECE':
      case 'MOVE_PIECE':
        // Restore after state
        if (action.pieceId && action.afterState) {
          const placedPieces = store.placedPieces;
          const pieceIndex = placedPieces.findIndex(p => p.id === action.pieceId);
          
          if (pieceIndex !== -1) {
            const updatedPieces = [...placedPieces];
            updatedPieces[pieceIndex] = {
              ...updatedPieces[pieceIndex],
              position: action.afterState.position || updatedPieces[pieceIndex].position,
              rotation: action.afterState.rotation || updatedPieces[pieceIndex].rotation,
              occupiedCells: action.afterState.occupiedCells || updatedPieces[pieceIndex].occupiedCells
            };
            store.setPlacedPieces(updatedPieces);
          }
        }
        break;
    }

    // Move action back to undo stack
    this.undoStack.push(action);
    return true;
  }

  clear() {
    this.undoStack = [];
    this.redoStack = [];
  }

  getUndoStackSize(): number {
    return this.undoStack.length;
  }

  getRedoStackSize(): number {
    return this.redoStack.length;
  }
}

// Global instance
export const undoRedoManager = new UndoRedoManager();

// Helper functions for common actions
export function recordPiecePlacement(placedPiece: {
  piece: string;
  position: any;
  rotation: any;
  id: string;
  occupiedCells: THREE.Vector3[];
}) {
  undoRedoManager.addAction({
    type: 'PLACE_PIECE',
    timestamp: Date.now(),
    pieceId: placedPiece.id,
    pieceName: placedPiece.piece,
    placedPiece
  });
}

export function recordPieceRemoval(removedPiece: {
  piece: string;
  position: any;
  rotation: any;
  id: string;
  occupiedCells: THREE.Vector3[];
}) {
  undoRedoManager.addAction({
    type: 'REMOVE_PIECE',
    timestamp: Date.now(),
    pieceId: removedPiece.id,
    pieceName: removedPiece.piece,
    placedPiece: removedPiece
  });
}

export function recordPieceRotation(
  pieceId: string,
  pieceName: string,
  beforeState: { position: THREE.Vector3; rotation: THREE.Euler; occupiedCells: THREE.Vector3[] },
  afterState: { position: THREE.Vector3; rotation: THREE.Euler; occupiedCells: THREE.Vector3[] }
) {
  undoRedoManager.addAction({
    type: 'ROTATE_PIECE',
    timestamp: Date.now(),
    pieceId,
    pieceName,
    beforeState,
    afterState
  });
}

export function recordPieceMovement(
  pieceId: string,
  pieceName: string,
  beforeState: { position: THREE.Vector3; rotation: THREE.Euler; occupiedCells: THREE.Vector3[] },
  afterState: { position: THREE.Vector3; rotation: THREE.Euler; occupiedCells: THREE.Vector3[] }
) {
  undoRedoManager.addAction({
    type: 'MOVE_PIECE',
    timestamp: Date.now(),
    pieceId,
    pieceName,
    beforeState,
    afterState
  });
}
