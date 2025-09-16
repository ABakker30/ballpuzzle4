import React from "react";
import { fccToWorld, Vector3 } from "../lib/fcc";

// Use analytic FCC sphere radius calculation
function calculateSphereRadius(a: number = 1): number {
  // For FCC lattice with spacing 'a', nearest neighbor distance is a/√2
  // Sphere radius for touching spheres is half that: a/(2√2)
  return a / (2 * Math.sqrt(2));
}

// Generate distinct color for each piece
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

interface PiecePreviewProps {
  piece: string;
  coordinates: number[][];
  isSelected: boolean;
  onClick: () => void;
}

export function PiecePreview({ piece, coordinates, isSelected, onClick }: PiecePreviewProps) {
  // Convert FCC engine coordinates to world positions for preview using the correct conversion
  const worldPoints: Vector3[] = coordinates.map(([i, j, k]) => fccToWorld(i, j, k));
  
  // Use analytic sphere radius for FCC lattice (a=1)
  const sphereRadius = calculateSphereRadius(1);
  
  // Calculate bounding box for SVG viewBox
  let minX = Infinity, maxX = -Infinity;
  let minY = Infinity, maxY = -Infinity;
  
  worldPoints.forEach(point => {
    minX = Math.min(minX, point.x);
    maxX = Math.max(maxX, point.x);
    minY = Math.min(minY, point.y);
    maxY = Math.max(maxY, point.y);
  });
  
  const padding = sphereRadius + 0.1; // Use sphere radius for padding
  const viewBox = `${minX - padding} ${minY - padding} ${maxX - minX + 2 * padding} ${maxY - minY + 2 * padding}`;
  const pieceColor = getPieceColor(piece);
  
  return (
    <button
      onClick={onClick}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "4px",
        padding: "8px",
        border: isSelected ? "2px solid var(--accent)" : "1px solid var(--border)",
        borderRadius: "8px",
        backgroundColor: isSelected ? "var(--accent-bg)" : "var(--bg-secondary)",
        cursor: "pointer",
        transition: "all 0.2s ease",
        minWidth: "60px",
      }}
    >
      <div style={{ fontSize: "12px", fontWeight: "bold" }}>{piece}</div>
      <svg
        width="32"
        height="24"
        viewBox={viewBox}
        style={{ overflow: "visible" }}
      >
        {worldPoints.map((point, index) => (
          <circle
            key={index}
            cx={point.x}
            cy={point.y}
            r={sphereRadius}
            fill={isSelected ? "var(--accent)" : pieceColor}
            stroke={isSelected ? "var(--accent-dark)" : pieceColor}
            strokeWidth="0.05"
          />
        ))}
      </svg>
    </button>
  );
}
