import { useAppStore } from '../store';

export interface SessionEvent {
  type: 'PIECE_PLACED' | 'PIECE_REMOVED' | 'PIECE_ROTATED' | 'PIECE_MOVED' | 'UNDO' | 'REDO' | 'SNAP' | 'DRAG_START' | 'DRAG_END';
  timestamp: number;
  pieceId?: string;
  pieceName?: string;
  position?: { x: number; y: number; z: number };
  metadata?: any;
}

export interface SessionStats {
  sessionId: string;
  startTime: number;
  endTime?: number;
  totalMoves: number;
  totalRotations: number;
  totalSnaps: number;
  totalUndos: number;
  totalRedos: number;
  totalDrags: number;
  pieceInteractions: { [pieceName: string]: number };
  events: SessionEvent[];
  playTime: number;
  averageTimePerMove: number;
  efficiency: {
    undoRatio: number;
    snapSuccessRate: number;
    movesPerPiece: number;
  };
}

class SessionStatsManager {
  private currentSession: SessionStats | null = null;
  private eventBuffer: SessionEvent[] = [];
  private readonly MAX_EVENTS = 1000;

  /**
   * Start a new session
   */
  startSession(): SessionStats {
    this.currentSession = {
      sessionId: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      startTime: Date.now(),
      totalMoves: 0,
      totalRotations: 0,
      totalSnaps: 0,
      totalUndos: 0,
      totalRedos: 0,
      totalDrags: 0,
      pieceInteractions: {},
      events: [],
      playTime: 0,
      averageTimePerMove: 0,
      efficiency: {
        undoRatio: 0,
        snapSuccessRate: 0,
        movesPerPiece: 0
      }
    };

    this.eventBuffer = [];
    return this.currentSession;
  }

  /**
   * End the current session
   */
  endSession(): SessionStats | null {
    if (!this.currentSession) return null;

    this.currentSession.endTime = Date.now();
    this.currentSession.playTime = this.currentSession.endTime - this.currentSession.startTime;
    this.updateEfficiencyMetrics();

    const completedSession = { ...this.currentSession };
    this.currentSession = null;
    return completedSession;
  }

  /**
   * Record an event in the current session
   */
  recordEvent(event: Omit<SessionEvent, 'timestamp'>): void {
    if (!this.currentSession) return;

    const fullEvent: SessionEvent = {
      ...event,
      timestamp: Date.now()
    };

    // Add to current session
    this.currentSession.events.push(fullEvent);
    this.eventBuffer.push(fullEvent);

    // Limit event history
    if (this.currentSession.events.length > this.MAX_EVENTS) {
      this.currentSession.events.shift();
    }

    // Update counters
    this.updateCounters(fullEvent);
    this.updateEfficiencyMetrics();
  }

  /**
   * Update session counters based on event
   */
  private updateCounters(event: SessionEvent): void {
    if (!this.currentSession) return;

    switch (event.type) {
      case 'PIECE_PLACED':
        this.currentSession.totalMoves++;
        if (event.pieceName) {
          this.currentSession.pieceInteractions[event.pieceName] = 
            (this.currentSession.pieceInteractions[event.pieceName] || 0) + 1;
        }
        break;
      case 'PIECE_ROTATED':
        this.currentSession.totalRotations++;
        break;
      case 'SNAP':
        this.currentSession.totalSnaps++;
        break;
      case 'UNDO':
        this.currentSession.totalUndos++;
        break;
      case 'REDO':
        this.currentSession.totalRedos++;
        break;
      case 'DRAG_START':
        this.currentSession.totalDrags++;
        break;
    }
  }

  /**
   * Update efficiency metrics
   */
  private updateEfficiencyMetrics(): void {
    if (!this.currentSession) return;

    const stats = this.currentSession;
    
    // Undo ratio (lower is better)
    stats.efficiency.undoRatio = stats.totalMoves > 0 ? 
      stats.totalUndos / stats.totalMoves : 0;

    // Snap success rate (snaps vs total drags)
    stats.efficiency.snapSuccessRate = stats.totalDrags > 0 ? 
      stats.totalSnaps / stats.totalDrags : 0;

    // Moves per piece (lower is better for efficiency)
    const uniquePieces = Object.keys(stats.pieceInteractions).length;
    stats.efficiency.movesPerPiece = uniquePieces > 0 ? 
      stats.totalMoves / uniquePieces : 0;

    // Average time per move
    const currentTime = Date.now();
    const playTime = currentTime - stats.startTime;
    stats.averageTimePerMove = stats.totalMoves > 0 ? 
      playTime / stats.totalMoves : 0;

    stats.playTime = playTime;
  }

  /**
   * Get current session stats
   */
  getCurrentSession(): SessionStats | null {
    if (!this.currentSession) return null;

    this.updateEfficiencyMetrics();
    return { ...this.currentSession };
  }

  /**
   * Get recent events (last N events)
   */
  getRecentEvents(count: number = 10): SessionEvent[] {
    if (!this.currentSession) return [];
    
    return this.currentSession.events.slice(-count);
  }

  /**
   * Get session summary for display
   */
  getSessionSummary(): {
    playTime: string;
    totalActions: number;
    efficiency: string;
    mostUsedPiece: string | null;
  } | null {
    if (!this.currentSession) return null;

    const stats = this.getCurrentSession()!;
    const playTimeMinutes = Math.floor(stats.playTime / 60000);
    const playTimeSeconds = Math.floor((stats.playTime % 60000) / 1000);
    
    const totalActions = stats.totalMoves + stats.totalRotations + stats.totalUndos + stats.totalRedos;
    
    let mostUsedPiece: string | null = null;
    let maxInteractions = 0;
    Object.entries(stats.pieceInteractions).forEach(([piece, count]) => {
      if (count > maxInteractions) {
        maxInteractions = count;
        mostUsedPiece = piece;
      }
    });

    const efficiencyScore = Math.max(0, 100 - (stats.efficiency.undoRatio * 50) - (stats.efficiency.movesPerPiece * 10));

    return {
      playTime: `${playTimeMinutes}:${playTimeSeconds.toString().padStart(2, '0')}`,
      totalActions,
      efficiency: `${Math.round(efficiencyScore)}%`,
      mostUsedPiece
    };
  }

  /**
   * Export session data for analysis
   */
  exportSessionData(): string {
    if (!this.currentSession) return '';

    return JSON.stringify(this.getCurrentSession(), null, 2);
  }

  /**
   * Reset current session
   */
  resetSession(): void {
    this.currentSession = null;
    this.eventBuffer = [];
  }
}

// Global instance
export const sessionStatsManager = new SessionStatsManager();

// Helper functions for common events
export function recordPiecePlacement(pieceName: string, position: { x: number; y: number; z: number }) {
  sessionStatsManager.recordEvent({
    type: 'PIECE_PLACED',
    pieceName,
    position
  });
}

export function recordPieceRotation(pieceName: string) {
  sessionStatsManager.recordEvent({
    type: 'PIECE_ROTATED',
    pieceName
  });
}

export function recordUndo() {
  sessionStatsManager.recordEvent({
    type: 'UNDO'
  });
}

export function recordRedo() {
  sessionStatsManager.recordEvent({
    type: 'REDO'
  });
}

export function recordSnap(pieceName: string, position: { x: number; y: number; z: number }) {
  sessionStatsManager.recordEvent({
    type: 'SNAP',
    pieceName,
    position
  });
}

export function recordDragStart(pieceName: string) {
  sessionStatsManager.recordEvent({
    type: 'DRAG_START',
    pieceName
  });
}

export function recordDragEnd(pieceName: string) {
  sessionStatsManager.recordEvent({
    type: 'DRAG_END',
    pieceName
  });
}
