import React from 'react';
import { getCompletionStats } from '../utils/solutionDetection';
import * as THREE from 'three';

interface ProgressIndicatorProps {
  containerPoints: THREE.Vector3[];
  placedPieces: Array<{ piece: string; position: any; rotation: any; id: string; occupiedCells: THREE.Vector3[] }>;
  className?: string;
}

export default function ProgressIndicator({ containerPoints, placedPieces, className = '' }: ProgressIndicatorProps) {
  const stats = getCompletionStats(containerPoints, placedPieces);

  return (
    <div className={`bg-white border rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-700">Progress</h3>
        <span className="text-sm font-semibold text-gray-900">
          {stats.percentage}%
        </span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
        <div 
          className={`h-2 rounded-full transition-all duration-300 ${
            stats.isComplete 
              ? 'bg-green-500' 
              : stats.percentage > 75 
                ? 'bg-blue-500' 
                : stats.percentage > 50 
                  ? 'bg-yellow-500' 
                  : 'bg-gray-400'
          }`}
          style={{ width: `${stats.percentage}%` }}
        />
      </div>
      
      <div className="flex justify-between text-xs text-gray-500">
        <span>{stats.filled} / {stats.total} cells</span>
        {stats.remaining > 0 && (
          <span>{stats.remaining} remaining</span>
        )}
        {stats.isComplete && (
          <span className="text-green-600 font-medium">Complete!</span>
        )}
      </div>
    </div>
  );
}
