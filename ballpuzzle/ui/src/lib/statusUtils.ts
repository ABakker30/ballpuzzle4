import { StatusData, Cell, PlacedPiece } from '../types/status';

/**
 * Flatten all active cells from status stack for 3D rendering
 */
export function flattenActiveCells(status: StatusData): Cell[] {
  const cells: Cell[] = [];
  
  status.stack.forEach((piece: PlacedPiece) => {
    piece.cells.forEach((cell: Cell) => {
      cells.push(cell);
    });
  });
  
  return cells;
}

/**
 * Get cell count for display purposes
 */
export function getActiveCellCount(status: StatusData): number {
  return status.stack.reduce((count: number, piece: PlacedPiece) => count + piece.cells.length, 0);
}

/**
 * Get piece count for display purposes
 */
export function getActivePieceCount(status: StatusData): number {
  return status.stack.length;
}

/**
 * Create a color map for consistent piece coloring based on instance IDs
 */
export function createPieceColorMap(status: StatusData): Map<number, string> {
  const colorMap = new Map<number, string>();
  
  status.stack.forEach((piece: PlacedPiece) => {
    // Use golden angle for good color distribution
    const hue = (piece.instance_id * 137.5) % 360;
    const color = `hsl(${hue}, 70%, 60%)`;
    colorMap.set(piece.instance_id, color);
  });
  
  return colorMap;
}

/**
 * Get cells with their associated piece instance IDs for rendering
 */
export interface CellWithPiece extends Cell {
  instance_id: number;
  piece_label: string;
}

export function getCellsWithPieceInfo(status: StatusData): CellWithPiece[] {
  const cellsWithPiece: CellWithPiece[] = [];
  
  status.stack.forEach((piece: PlacedPiece) => {
    piece.cells.forEach((cell: Cell) => {
      cellsWithPiece.push({
        ...cell,
        instance_id: piece.instance_id,
        piece_label: piece.piece_label
      });
    });
  });
  
  return cellsWithPiece;
}
