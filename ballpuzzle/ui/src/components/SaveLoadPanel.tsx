import React, { useState, useEffect } from 'react';
import { saveLoadManager, SaveSlot } from '../utils/saveLoad';

interface SaveLoadPanelProps {
  containerPoints: any[];
  sessionStats: any;
  onLoad?: (saveSlot: SaveSlot) => void;
  className?: string;
}

export default function SaveLoadPanel({ 
  containerPoints, 
  sessionStats, 
  onLoad, 
  className = '' 
}: SaveLoadPanelProps) {
  const [saves, setSaves] = useState<SaveSlot[]>([]);
  const [autosave, setAutosave] = useState<SaveSlot | null>(null);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadSaves();
  }, []);

  const loadSaves = () => {
    setSaves(saveLoadManager.getAllSaves());
    setAutosave(saveLoadManager.getAutosave());
  };

  const handleSave = async () => {
    if (!saveName.trim()) return;
    
    setIsLoading(true);
    try {
      await saveLoadManager.saveGame(saveName.trim(), containerPoints, sessionStats);
      setSaveName('');
      setShowSaveDialog(false);
      loadSaves();
    } catch (error) {
      console.error('Save failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoad = (saveSlot: SaveSlot) => {
    if (saveLoadManager.loadGame(saveSlot)) {
      onLoad?.(saveSlot);
    }
  };

  const handleDelete = (saveId: string) => {
    if (confirm('Are you sure you want to delete this save?')) {
      saveLoadManager.deleteSave(saveId);
      loadSaves();
    }
  };

  const handleExport = (saveSlot: SaveSlot) => {
    saveLoadManager.exportSave(saveSlot);
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    try {
      const importedSave = await saveLoadManager.importSave(file);
      if (importedSave) {
        loadSaves();
      } else {
        alert('Failed to import save file. Please check the file format.');
      }
    } catch (error) {
      console.error('Import failed:', error);
      alert('Failed to import save file.');
    } finally {
      setIsLoading(false);
      event.target.value = '';
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatPlayTime = (playTime: number) => {
    const minutes = Math.floor(playTime / 60000);
    const seconds = Math.floor((playTime % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`bg-white border rounded-lg p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Save & Load</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setShowSaveDialog(true)}
            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition-colors"
            disabled={isLoading}
          >
            Save Game
          </button>
          <label className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600 transition-colors cursor-pointer">
            Import
            <input
              type="file"
              accept=".json"
              onChange={handleImport}
              className="hidden"
              disabled={isLoading}
            />
          </label>
        </div>
      </div>

      {/* Autosave Section */}
      {autosave && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-yellow-800">🔄 Autosave</div>
              <div className="text-sm text-yellow-600">
                {formatDate(autosave.timestamp)} • {autosave.boardState.placedPieces.length} pieces
              </div>
            </div>
            <button
              onClick={() => handleLoad(autosave)}
              className="px-2 py-1 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600 transition-colors"
              disabled={isLoading}
            >
              Load
            </button>
          </div>
        </div>
      )}

      {/* Save Slots */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {saves.length === 0 ? (
          <div className="text-center text-gray-500 py-4">
            No saved games yet
          </div>
        ) : (
          saves.map((save) => (
            <div key={save.id} className="p-3 border rounded hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-medium">{save.name}</div>
                  <div className="text-sm text-gray-500">
                    {formatDate(save.timestamp)} • 
                    {save.boardState.placedPieces.length} pieces • 
                    {formatPlayTime(save.sessionStats.playTime)} played
                  </div>
                  {save.puzzleMetadata.containerName && (
                    <div className="text-xs text-gray-400">
                      Container: {save.puzzleMetadata.containerName}
                    </div>
                  )}
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleLoad(save)}
                    className="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 transition-colors"
                    disabled={isLoading}
                  >
                    Load
                  </button>
                  <button
                    onClick={() => handleExport(save)}
                    className="px-2 py-1 bg-gray-500 text-white rounded text-xs hover:bg-gray-600 transition-colors"
                    disabled={isLoading}
                  >
                    Export
                  </button>
                  <button
                    onClick={() => handleDelete(save.id)}
                    className="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600 transition-colors"
                    disabled={isLoading}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h4 className="text-lg font-semibold mb-4">Save Game</h4>
            <input
              type="text"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              placeholder="Enter save name..."
              className="w-full px-3 py-2 border rounded mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
              onKeyPress={(e) => e.key === 'Enter' && handleSave()}
            />
            <div className="flex gap-3">
              <button
                onClick={() => setShowSaveDialog(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors"
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors disabled:opacity-50"
                disabled={!saveName.trim() || isLoading}
              >
                {isLoading ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
