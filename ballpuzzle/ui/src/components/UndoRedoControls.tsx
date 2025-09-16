import React, { useState, useEffect } from 'react';
import { undoRedoManager } from '../utils/undoRedo';

interface UndoRedoControlsProps {
  className?: string;
}

export default function UndoRedoControls({ className = '' }: UndoRedoControlsProps) {
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [undoCount, setUndoCount] = useState(0);
  const [redoCount, setRedoCount] = useState(0);

  // Update state periodically to reflect undo/redo availability
  useEffect(() => {
    const updateState = () => {
      setCanUndo(undoRedoManager.canUndo());
      setCanRedo(undoRedoManager.canRedo());
      setUndoCount(undoRedoManager.getUndoStackSize());
      setRedoCount(undoRedoManager.getRedoStackSize());
    };

    updateState();
    const interval = setInterval(updateState, 100); // Check every 100ms

    return () => clearInterval(interval);
  }, []);

  const handleUndo = () => {
    undoRedoManager.undo();
  };

  const handleRedo = () => {
    undoRedoManager.redo();
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <button
        onClick={handleUndo}
        disabled={!canUndo}
        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
          canUndo
            ? 'bg-blue-500 hover:bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
        }`}
        title={`Undo (Ctrl+Z) - ${undoCount} actions available`}
      >
        ↶ Undo
      </button>
      
      <button
        onClick={handleRedo}
        disabled={!canRedo}
        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
          canRedo
            ? 'bg-green-500 hover:bg-green-600 text-white'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
        }`}
        title={`Redo (Ctrl+Y) - ${redoCount} actions available`}
      >
        ↷ Redo
      </button>
      
      <div className="text-xs text-gray-500 ml-2">
        {undoCount > 0 && (
          <span className="mr-2">
            {undoCount} undo{undoCount !== 1 ? 's' : ''}
          </span>
        )}
        {redoCount > 0 && (
          <span>
            {redoCount} redo{redoCount !== 1 ? 's' : ''}
          </span>
        )}
      </div>
    </div>
  );
}
