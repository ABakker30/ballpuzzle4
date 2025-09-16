import React, { useState, useEffect } from 'react';
import { sessionStatsManager, SessionStats } from '../utils/sessionStats';

interface SessionStatsPanelProps {
  className?: string;
}

export default function SessionStatsPanel({ className = '' }: SessionStatsPanelProps) {
  const [sessionStats, setSessionStats] = useState<SessionStats | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    const updateStats = () => {
      setSessionStats(sessionStatsManager.getCurrentSession());
    };

    updateStats();
    const interval = setInterval(updateStats, 1000); // Update every second

    return () => clearInterval(interval);
  }, []);

  if (!sessionStats) {
    return null;
  }

  const summary = sessionStatsManager.getSessionSummary();
  const recentEvents = sessionStatsManager.getRecentEvents(5);

  const formatTime = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'PIECE_PLACED': return '📍';
      case 'PIECE_ROTATED': return '🔄';
      case 'UNDO': return '↶';
      case 'REDO': return '↷';
      case 'SNAP': return '🎯';
      case 'DRAG_START': return '👆';
      default: return '•';
    }
  };

  return (
    <div className={`bg-white border rounded-lg ${className}`}>
      <div 
        className="p-3 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-700">Session Stats</h3>
          <span className="text-xs text-gray-500">
            {isExpanded ? '▼' : '▶'}
          </span>
        </div>
        
        {summary && (
          <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Time:</span>
              <span className="ml-1 font-medium">{summary.playTime}</span>
            </div>
            <div>
              <span className="text-gray-500">Actions:</span>
              <span className="ml-1 font-medium">{summary.totalActions}</span>
            </div>
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="border-t p-3 space-y-3">
          {/* Detailed Stats */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-500">Moves:</span>
                <span className="font-medium">{sessionStats.totalMoves}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Rotations:</span>
                <span className="font-medium">{sessionStats.totalRotations}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Snaps:</span>
                <span className="font-medium">{sessionStats.totalSnaps}</span>
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-500">Undos:</span>
                <span className="font-medium">{sessionStats.totalUndos}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Redos:</span>
                <span className="font-medium">{sessionStats.totalRedos}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Drags:</span>
                <span className="font-medium">{sessionStats.totalDrags}</span>
              </div>
            </div>
          </div>

          {/* Efficiency Metrics */}
          <div className="border-t pt-3">
            <h4 className="text-xs font-medium text-gray-700 mb-2">Efficiency</h4>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Undo Ratio:</span>
                <span className={`font-medium ${
                  sessionStats.efficiency.undoRatio < 0.1 ? 'text-green-600' :
                  sessionStats.efficiency.undoRatio < 0.3 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {Math.round(sessionStats.efficiency.undoRatio * 100)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Snap Success:</span>
                <span className={`font-medium ${
                  sessionStats.efficiency.snapSuccessRate > 0.7 ? 'text-green-600' :
                  sessionStats.efficiency.snapSuccessRate > 0.4 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {Math.round(sessionStats.efficiency.snapSuccessRate * 100)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Avg Time/Move:</span>
                <span className="font-medium">
                  {formatTime(sessionStats.averageTimePerMove)}
                </span>
              </div>
            </div>
          </div>

          {/* Recent Events */}
          {recentEvents.length > 0 && (
            <div className="border-t pt-3">
              <h4 className="text-xs font-medium text-gray-700 mb-2">Recent Activity</h4>
              <div className="space-y-1">
                {recentEvents.reverse().map((event, index) => (
                  <div key={index} className="flex items-center text-xs text-gray-600">
                    <span className="mr-2">{getEventIcon(event.type)}</span>
                    <span className="flex-1">
                      {event.type.replace('_', ' ').toLowerCase()}
                      {event.pieceName && ` (${event.pieceName})`}
                    </span>
                    <span className="text-gray-400">
                      {Math.round((Date.now() - event.timestamp) / 1000)}s ago
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Piece Interactions */}
          {Object.keys(sessionStats.pieceInteractions).length > 0 && (
            <div className="border-t pt-3">
              <h4 className="text-xs font-medium text-gray-700 mb-2">Piece Usage</h4>
              <div className="grid grid-cols-3 gap-1 text-xs">
                {Object.entries(sessionStats.pieceInteractions)
                  .sort(([,a], [,b]) => b - a)
                  .slice(0, 6)
                  .map(([piece, count]) => (
                    <div key={piece} className="flex justify-between">
                      <span className="text-gray-500">{piece}:</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Export Button */}
          <div className="border-t pt-3">
            <button
              onClick={() => {
                const data = sessionStatsManager.exportSessionData();
                const blob = new Blob([data], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `session_stats_${new Date().toISOString().split('T')[0]}.json`;
                link.click();
                URL.revokeObjectURL(url);
              }}
              className="w-full px-3 py-1 bg-gray-100 text-gray-700 rounded text-xs hover:bg-gray-200 transition-colors"
            >
              Export Session Data
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
