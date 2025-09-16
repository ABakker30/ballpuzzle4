import React from 'react';
import { SolutionValidationResult } from '../utils/solutionDetection';

interface CompletionModalProps {
  isOpen: boolean;
  onClose: () => void;
  validationResult: SolutionValidationResult;
  sessionStats?: {
    startTime: number;
    totalMoves: number;
    totalRotations: number;
    totalUndos: number;
    totalRedos: number;
  };
}

export default function CompletionModal({ 
  isOpen, 
  onClose, 
  validationResult, 
  sessionStats 
}: CompletionModalProps) {
  if (!isOpen) return null;

  const playTime = sessionStats ? Math.round((Date.now() - sessionStats.startTime) / 1000) : 0;
  const minutes = Math.floor(playTime / 60);
  const seconds = playTime % 60;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-2xl">
        <div className="text-center">
          {validationResult.isCorrect ? (
            <>
              <div className="text-6xl mb-4">🎉</div>
              <h2 className="text-2xl font-bold text-green-600 mb-2">
                Puzzle Completed!
              </h2>
              <p className="text-gray-600 mb-6">
                Congratulations! You've successfully solved the puzzle.
              </p>
            </>
          ) : (
            <>
              <div className="text-6xl mb-4">🧩</div>
              <h2 className="text-2xl font-bold text-blue-600 mb-2">
                Puzzle Filled!
              </h2>
              <p className="text-gray-600 mb-6">
                All cells are filled, but the solution may not be optimal.
              </p>
            </>
          )}

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="font-semibold mb-3">Solution Statistics</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-500">Completion</div>
                <div className="font-medium">{Math.round(validationResult.completionPercentage)}%</div>
              </div>
              <div>
                <div className="text-gray-500">Filled Cells</div>
                <div className="font-medium">
                  {validationResult.stats.filledCells} / {validationResult.stats.totalCells}
                </div>
              </div>
              {sessionStats && (
                <>
                  <div>
                    <div className="text-gray-500">Time</div>
                    <div className="font-medium">
                      {minutes}:{seconds.toString().padStart(2, '0')}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500">Moves</div>
                    <div className="font-medium">{sessionStats.totalMoves}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Rotations</div>
                    <div className="font-medium">{sessionStats.totalRotations}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Undos</div>
                    <div className="font-medium">{sessionStats.totalUndos}</div>
                  </div>
                </>
              )}
            </div>
          </div>

          {validationResult.incorrectPlacements.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <h4 className="font-medium text-yellow-800 mb-2">
                Potential Issues
              </h4>
              <p className="text-sm text-yellow-700">
                {validationResult.incorrectPlacements.length} piece(s) may not be in optimal positions.
              </p>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Continue Editing
            </button>
            <button
              onClick={() => {
                // Reset puzzle functionality can be added here
                onClose();
              }}
              className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              New Puzzle
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
