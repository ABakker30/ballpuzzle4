import React, { useState } from "react";
import * as THREE from "three";
import { useAppStore } from "../store";
import { fccToWorld } from '../lib/fcc';
import PuzzleViewer3D from "../components/PuzzleViewer3D";
import SaveLoadPanel from "../components/SaveLoadPanel";
import SessionStatsPanel from "../components/SessionStatsPanel";
import UndoRedoControls from "../components/UndoRedoControls";
import CompletionModal from "../components/CompletionModal";
import ProgressIndicator from "../components/ProgressIndicator";
import { computeConvexHull, calculateOrientationMatrix, orientPoints } from '../utils/convexHull';
import { PieceHoverPreview } from "../components/PieceHoverPreview";

// Generate distinct color for each piece (same function as in PiecePreview)
function getPieceColor(piece: string): string {
  const colors = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
    "#F8C471", "#82E0AA", "#F1948A", "#85C1E9", "#D7BDE2",
    "#A3E4D7", "#F9E79F", "#D5A6BD", "#AED6F1", "#A9DFBF",
    "#F5B7B1", "#D2B4DE", "#A9CCE3", "#A3E4D7", "#F7DC6F"
  ];
  const index = piece.charCodeAt(0) - 65; // A=0, B=1, etc.
  return colors[index % colors.length];
}

interface InventoryPanelProps {
  pieces: string[];
  pieceData: { [key: string]: number[][] } | null;
  onPieceSelect: (piece: string) => void;
  selectedPiece: string | null;
}

function InventoryPanel({ pieces, pieceData, onPieceSelect, selectedPiece }: InventoryPanelProps) {
  if (!pieceData) {
    return <div>Loading pieces...</div>;
  }

  const handlePieceClick = (piece: string, coordinates: number[][]) => {
    // Directly select the piece, bringing it into the 3D viewer
    onPieceSelect(piece);
  };

  return (
    <div style={{ padding: "16px", backgroundColor: "var(--bg-secondary)", borderRadius: "8px" }}>
      <h3 style={{ margin: "0 0 16px 0" }}>Piece Inventory</h3>
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(80px, 1fr))",
        gap: "8px",
        maxHeight: "400px",
        overflowY: "auto"
      }}>
        {pieces.map(piece => {
          const coordinates = pieceData[piece];
          if (!coordinates) return null;
          
          return (
            <PiecePreview
              key={piece}
              piece={piece}
              coordinates={coordinates}
              isSelected={selectedPiece === piece}
              onClick={() => handlePieceClick(piece, coordinates)}
            />
          );
        })}
      </div>
      
    </div>
  );
}

export function PuzzlePage() {
  const { 
    puzzleContainer, 
    puzzlePieces, 
    placedPieces, 
    selectedPiece, 
    setSelectedPiece, 
    puzzleOrientation,
    setPuzzleContainer,
    setPuzzlePieces,
    setPuzzleOrientation
  } = useAppStore();
  const [pieces, setPieces] = useState<string[]>([]);
  const [containerPoints, setContainerPoints] = useState<THREE.Vector3[]>([]);
  const [orientedPoints, setOrientedPoints] = useState<THREE.Vector3[]>([]);
  const [hoveredPiece, setHoveredPiece] = useState<string | null>(null);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [completionResult, setCompletionResult] = useState<any>(null);
  const [sessionStats] = useState({
    startTime: Date.now(),
    totalMoves: 0,
    totalRotations: 0,
    totalUndos: 0,
    totalRedos: 0
  });
  
  // Default piece library A-Y
  const defaultPieces = Array.from({ length: 25 }, (_, i) => String.fromCharCode(65 + i));

  // Load piece library
  React.useEffect(() => {
    const loadPieces = async () => {
      try {
        // Load from authoritative source
        const possiblePaths = [
          '/pieces.json'
        ];
        
        let piecesData = null;
        for (const path of possiblePaths) {
          try {
            const response = await fetch(path);
            if (response.ok) {
              piecesData = await response.json();
              console.log('Loaded piece library from:', path, Object.keys(piecesData).length, 'pieces');
              break;
            }
          } catch (e) {
            // Continue to next path
          }
        }
        
        if (piecesData) {
          setPuzzlePieces(piecesData);
        } else {
          throw new Error('Could not load from any path');
        }
      } catch (error) {
        console.error('Failed to load piece library, using complete fallback:', error);
        // Complete A-Y piece library as fallback
        const fallbackPieces: { [key: string]: number[][] } = {
          "A": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]],
          "B": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],
          "C": [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 0]],
          "D": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [2, 1, 0]],
          "E": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 0, 1]],
          "F": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 0, 1]],
          "G": [[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]],
          "H": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 1, 1]],
          "I": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 1]],
          "J": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [2, 0, 0]],
          "K": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 1, 1]],
          "L": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 1]],
          "M": [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 1, 0]],
          "N": [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 0, 1]],
          "O": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 0, 1]],
          "P": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 2]],
          "Q": [[0, 0, 0], [1, 0, 0], [2, 0, 0], [2, 1, 0]],
          "R": [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 0, 1]],
          "S": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [2, 0, 0]],
          "T": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [2, 1, 0]],
          "U": [[0, 0, 0], [1, 0, 0], [2, 0, 0], [1, 1, 1]],
          "V": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]],
          "W": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 0, 2]],
          "X": [[0, 0, 0], [1, 0, 0], [2, 0, 0], [0, 1, 1]],
          "Y": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 2, 0]]
        };
        setPuzzlePieces(fallbackPieces);
      }
    };
    
    loadPieces();
  }, [setPuzzlePieces]);

  // Load and convert container when containerObj changes
  React.useEffect(() => {
    if (puzzleContainer && (puzzleContainer.coordinates || puzzleContainer.cells)) {
      
      // Convert FCC coordinates to world positions
      const worldPoints: THREE.Vector3[] = [];
      const coordinates = puzzleContainer.coordinates || puzzleContainer.cells || [];
      coordinates.forEach(([i, j, k]: [number, number, number]) => {
        const worldPos = fccToWorld(i, j, k, 1.0);
        worldPoints.push(new THREE.Vector3(worldPos.x, worldPos.y, worldPos.z));
      });
      
      
      setContainerPoints(worldPoints);
      
      // Compute convex hull and orientation for Y-up (table-top)
      if (worldPoints.length >= 4) {
        const hullResult = computeConvexHull(worldPoints);
        if (hullResult) {
          const orientationMatrix = calculateOrientationMatrix(hullResult, 'Y');
          const { points: oriented, groundOffsetY } = orientPoints(worldPoints, orientationMatrix, hullResult.center);
          
          setOrientedPoints(oriented);
          
          // Store orientation in puzzle state
          useAppStore.getState().setPuzzleOrientation({
            rotation: orientationMatrix,
            center: hullResult.center,
            groundOffsetY,
            faces: hullResult.faces
          });
        } else {
          setOrientedPoints(worldPoints);
        }
      } else {
        setOrientedPoints(worldPoints);
      }
      
    } else {
    }
  }, [puzzleContainer, setPuzzleContainer]);

  const handlePieceSelect = (piece: string) => {
    setSelectedPiece(selectedPiece === piece ? null : piece);
  };

  const handleCellClick = (position: THREE.Vector3) => {
    console.log('Cell clicked:', position);
  };

  const handleSolutionComplete = (validationResult: any) => {
    setCompletionResult(validationResult);
    setShowCompletionModal(true);
  };

  const handleCloseCompletionModal = () => {
    setShowCompletionModal(false);
    setCompletionResult(null);
  };

  const handleLoadContainer = async () => {
    try {
      // Use File System Access API if available
      if ('showOpenFilePicker' in window) {
        const [fileHandle] = await (window as any).showOpenFilePicker({
          types: [{
            description: 'Container files',
            accept: { 'application/json': ['.json', '.fcc.json'] }
          }]
        });
        
        const file = await fileHandle.getFile();
        const text = await file.text();
        const containerData = JSON.parse(text);
        
        // Set the container object to trigger the useEffect pipeline
        setPuzzleContainer(containerData);
      } else {
        alert('File picker not supported in this browser. Please use a modern browser like Chrome or Edge.');
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        console.error('Failed to load container:', error);
        alert('Failed to load container file. Please check the file format.');
      }
    }
  };

  return (
    <div style={{ display: "flex", height: "calc(100vh - 80px)" }}>
      {/* Main 3D Viewer */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <PuzzleViewer3D 
          containerPoints={orientedPoints.length > 0 ? orientedPoints : containerPoints}
          placedPieces={placedPieces}
          onCellClick={handleCellClick}
          hullFaces={puzzleOrientation?.faces}
        />
      </div>
      
      {/* Sidebar */}
      <div style={{ width: "300px", padding: "16px", borderLeft: "1px solid var(--border)" }}>
        <div className="card">
          <h3>Interactive Puzzle</h3>
          <p>
            Load a container and start placing pieces to solve the puzzle manually.
          </p>
          <button 
            className="button" 
            onClick={handleLoadContainer}
            style={{ width: "100%", marginBottom: "12px" }}
          >
            Load Container
          </button>
          {!puzzleContainer ? (
            <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
              Click "Load Container" to select a container file, or load one from the "Puzzle Shape" tab.
            </p>
          ) : (
            <div>
              <p style={{ color: "var(--text-success)", fontSize: "14px" }}>
                Container loaded: {orientedPoints.length > 0 ? orientedPoints.length : containerPoints.length} cells
              </p>
              <p style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Pieces placed: {placedPieces.length}
              </p>
            </div>
          )}
        </div>
        
        <InventoryPanel 
          pieces={pieces}
          pieceData={puzzlePieces}
          onPieceSelect={handlePieceSelect}
          selectedPiece={selectedPiece}
        />
        <div className="flex-1 flex flex-col">
          <div className="mb-4 flex justify-between items-start">
            <div className="flex flex-col gap-4">
              <UndoRedoControls />
              <ProgressIndicator 
                containerPoints={containerPoints}
                placedPieces={placedPieces}
              />
              <SaveLoadPanel 
                containerPoints={containerPoints}
                sessionStats={sessionStats}
              />
              <SessionStatsPanel />
            </div>
          </div>
          
          <PuzzleViewer3D
            containerPoints={containerPoints}
            placedPieces={placedPieces}
            onCellClick={handleCellClick}
            onSolutionComplete={handleSolutionComplete}
            hullFaces={puzzleOrientation?.faces}
          />
        </div>
      </div>
      
      <CompletionModal
        isOpen={showCompletionModal}
        onClose={handleCloseCompletionModal}
        validationResult={completionResult}
        sessionStats={sessionStats}
      />
    </div>
  );
