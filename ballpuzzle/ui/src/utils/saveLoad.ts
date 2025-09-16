import * as THREE from 'three';
import { useAppStore } from '../store';

export interface SaveSlot {
  id: string;
  name: string;
  timestamp: number;
  boardState: {
    placedPieces: Array<{
      piece: string;
      position: { x: number; y: number; z: number };
      rotation: { x: number; y: number; z: number };
      id: string;
      occupiedCells: Array<{ x: number; y: number; z: number }>;
    }>;
    selectedPiece: string | null;
    containerPoints: Array<{ x: number; y: number; z: number }>;
  };
  sessionStats: {
    startTime: number;
    totalMoves: number;
    totalRotations: number;
    totalUndos: number;
    totalRedos: number;
    playTime: number;
  };
  cameraState?: {
    position: { x: number; y: number; z: number };
    target: { x: number; y: number; z: number };
    zoom: number;
  };
  puzzleMetadata: {
    containerName?: string;
    pieceLibrary?: string;
    difficulty?: string;
  };
}

class SaveLoadManager {
  private readonly STORAGE_KEY = 'ballpuzzle_saves';
  private readonly AUTOSAVE_KEY = 'ballpuzzle_autosave';
  private readonly MAX_SAVES = 10;
  private autosaveInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.startAutosave();
  }

  /**
   * Start autosave functionality - saves every 30 seconds
   */
  startAutosave() {
    if (this.autosaveInterval) {
      clearInterval(this.autosaveInterval);
    }
    
    this.autosaveInterval = setInterval(() => {
      this.autosave();
    }, 30000); // 30 seconds
  }

  /**
   * Stop autosave functionality
   */
  stopAutosave() {
    if (this.autosaveInterval) {
      clearInterval(this.autosaveInterval);
      this.autosaveInterval = null;
    }
  }

  /**
   * Create a save slot from current game state
   */
  createSaveSlot(
    name: string,
    containerPoints: THREE.Vector3[],
    sessionStats: any,
    cameraState?: any
  ): SaveSlot {
    const store = useAppStore.getState();
    
    return {
      id: `save_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name,
      timestamp: Date.now(),
      boardState: {
        placedPieces: store.placedPieces.map(piece => ({
          piece: piece.piece,
          position: {
            x: piece.position.x,
            y: piece.position.y,
            z: piece.position.z
          },
          rotation: {
            x: piece.rotation.x,
            y: piece.rotation.y,
            z: piece.rotation.z
          },
          id: piece.id,
          occupiedCells: piece.occupiedCells.map(cell => ({
            x: cell.x,
            y: cell.y,
            z: cell.z
          }))
        })),
        selectedPiece: store.selectedPiece,
        containerPoints: containerPoints.map(point => ({
          x: point.x,
          y: point.y,
          z: point.z
        }))
      },
      sessionStats: {
        startTime: sessionStats.startTime,
        totalMoves: sessionStats.totalMoves,
        totalRotations: sessionStats.totalRotations,
        totalUndos: sessionStats.totalUndos,
        totalRedos: sessionStats.totalRedos,
        playTime: Date.now() - sessionStats.startTime
      },
      cameraState,
      puzzleMetadata: {
        containerName: store.puzzleContainer?.name || 'Unknown',
        pieceLibrary: 'Default A-Y',
        difficulty: 'Normal'
      }
    };
  }

  /**
   * Save game state to a named slot
   */
  saveGame(
    name: string,
    containerPoints: THREE.Vector3[],
    sessionStats: any,
    cameraState?: any
  ): SaveSlot {
    const saveSlot = this.createSaveSlot(name, containerPoints, sessionStats, cameraState);
    const saves = this.getAllSaves();
    
    // Add new save and limit to MAX_SAVES
    saves.unshift(saveSlot);
    if (saves.length > this.MAX_SAVES) {
      saves.splice(this.MAX_SAVES);
    }
    
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(saves));
    return saveSlot;
  }

  /**
   * Autosave current state
   */
  autosave() {
    try {
      const store = useAppStore.getState();
      
      // Only autosave if there are placed pieces
      if (store.placedPieces.length === 0) {
        return;
      }

      const autosaveSlot = this.createSaveSlot(
        'Autosave',
        [], // We'll need to get container points from somewhere
        {
          startTime: Date.now() - 300000, // Placeholder
          totalMoves: 0,
          totalRotations: 0,
          totalUndos: 0,
          totalRedos: 0
        }
      );
      
      localStorage.setItem(this.AUTOSAVE_KEY, JSON.stringify(autosaveSlot));
    } catch (error) {
      console.warn('Autosave failed:', error);
    }
  }

  /**
   * Load game state from a save slot
   */
  loadGame(saveSlot: SaveSlot): boolean {
    try {
      const store = useAppStore.getState();
      
      // Restore placed pieces
      const restoredPieces = saveSlot.boardState.placedPieces.map(piece => ({
        piece: piece.piece,
        position: new THREE.Vector3(piece.position.x, piece.position.y, piece.position.z),
        rotation: new THREE.Euler(piece.rotation.x, piece.rotation.y, piece.rotation.z),
        id: piece.id,
        occupiedCells: piece.occupiedCells.map(cell => 
          new THREE.Vector3(cell.x, cell.y, cell.z)
        )
      }));
      
      store.setPlacedPieces(restoredPieces);
      store.setSelectedPiece(saveSlot.boardState.selectedPiece);
      
      return true;
    } catch (error) {
      console.error('Failed to load game:', error);
      return false;
    }
  }

  /**
   * Get all saved games
   */
  getAllSaves(): SaveSlot[] {
    try {
      const saves = localStorage.getItem(this.STORAGE_KEY);
      return saves ? JSON.parse(saves) : [];
    } catch (error) {
      console.error('Failed to load saves:', error);
      return [];
    }
  }

  /**
   * Get autosave if it exists
   */
  getAutosave(): SaveSlot | null {
    try {
      const autosave = localStorage.getItem(this.AUTOSAVE_KEY);
      return autosave ? JSON.parse(autosave) : null;
    } catch (error) {
      console.error('Failed to load autosave:', error);
      return null;
    }
  }

  /**
   * Delete a save slot
   */
  deleteSave(saveId: string): boolean {
    try {
      const saves = this.getAllSaves();
      const filteredSaves = saves.filter(save => save.id !== saveId);
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(filteredSaves));
      return true;
    } catch (error) {
      console.error('Failed to delete save:', error);
      return false;
    }
  }

  /**
   * Clear all saves
   */
  clearAllSaves(): boolean {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
      localStorage.removeItem(this.AUTOSAVE_KEY);
      return true;
    } catch (error) {
      console.error('Failed to clear saves:', error);
      return false;
    }
  }

  /**
   * Export save to file
   */
  exportSave(saveSlot: SaveSlot): void {
    try {
      const dataStr = JSON.stringify(saveSlot, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      
      const link = document.createElement('a');
      link.href = URL.createObjectURL(dataBlob);
      link.download = `ballpuzzle_${saveSlot.name}_${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      
      URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error('Failed to export save:', error);
    }
  }

  /**
   * Import save from file
   */
  async importSave(file: File): Promise<SaveSlot | null> {
    try {
      const text = await file.text();
      const saveSlot: SaveSlot = JSON.parse(text);
      
      // Validate save structure
      if (!saveSlot.id || !saveSlot.boardState || !saveSlot.sessionStats) {
        throw new Error('Invalid save file format');
      }
      
      // Add to saves list
      const saves = this.getAllSaves();
      saves.unshift(saveSlot);
      if (saves.length > this.MAX_SAVES) {
        saves.splice(this.MAX_SAVES);
      }
      
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(saves));
      return saveSlot;
    } catch (error) {
      console.error('Failed to import save:', error);
      return null;
    }
  }
}

// Global instance
export const saveLoadManager = new SaveLoadManager();
