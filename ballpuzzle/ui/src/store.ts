import { create } from "zustand";
import * as THREE from "three";

type Status = { ok: boolean | null; message: string };

type State = {
  tab: "shape" | "solve" | "view" | "status" | "puzzle";
  setTab: (t: State["tab"]) => void;

  containerStatus: Status;
  solutionStatus: Status;
  eventsStatus: Status;

  setContainerStatus: (s: Status) => void;
  setSolutionStatus: (s: Status) => void;
  setEventsStatus: (s: Status) => void;

  // raw objects (available for next phases)
  containerObj: any | null;
  solutionObj: any | null;
  eventsLines: string[] | null;
  setContainerObj: (o: any | null) => void;
  setSolutionObj: (o: any | null) => void;
  setEventsLines: (ls: string[] | null) => void;

  // selected placement index
  selectedPlacementIdx: number | null;
  setSelectedPlacementIdx: (i: number | null) => void;

  // puzzle state
  puzzleContainer: any | null;
  puzzlePieces: { [key: string]: any } | null;
  placedPieces: Array<{ piece: string; position: any; rotation: any; id: string }>;
  selectedPiece: string | null;
  selectedPieceTransform: {
    position: THREE.Vector3;
    rotation: THREE.Euler;
    snappedToContainer: THREE.Vector3 | null;
  } | null;
  puzzleOrientation: {
    rotation: THREE.Matrix4;
    center: THREE.Vector3;
    groundOffsetY: number;
    faces?: Array<{
      normal: THREE.Vector3;
      vertices: THREE.Vector3[];
      isLargest: boolean;
    }>;
  } | null;
  
  setPuzzleContainer: (container: any | null) => void;
  setPuzzlePieces: (pieces: { [key: string]: any } | null) => void;
  setPlacedPieces: (pieces: Array<{ piece: string; position: any; rotation: any; id: string }>) => void;
  setSelectedPiece: (piece: string | null) => void;
  setSelectedPieceTransform: (transform: { position: THREE.Vector3; rotation: THREE.Euler; snappedToContainer: THREE.Vector3 | null } | null) => void;
  setPuzzleOrientation: (orientation: { rotation: THREE.Matrix4; center: THREE.Vector3; groundOffsetY: number; faces?: Array<{ normal: THREE.Vector3; vertices: THREE.Vector3[]; isLargest: boolean }> } | null) => void;
  addPlacedPiece: (piece: { piece: string; position: any; rotation: any; id: string }) => void;
  removePlacedPiece: (id: string) => void;
};

export const useAppStore = create<State>((set) => ({
  tab: "shape",
  setTab: (t) => set({ tab: t }),

  containerStatus: { ok: null, message: "" },
  solutionStatus: { ok: null, message: "" },
  eventsStatus: { ok: null, message: "" },

  setContainerStatus: (s) => set({ containerStatus: s }),
  setSolutionStatus: (s) => set({ solutionStatus: s }),
  setEventsStatus: (s) => set({ eventsStatus: s }),

  containerObj: null,
  solutionObj: null,
  eventsLines: null,
  setContainerObj: (o) => set({ containerObj: o }),
  setSolutionObj: (o) => set({ solutionObj: o }),
  setEventsLines: (ls) => set({ eventsLines: ls }),

  selectedPlacementIdx: null,
  setSelectedPlacementIdx: (i) => set({ selectedPlacementIdx: i }),

  puzzleContainer: null,
  puzzlePieces: null,
  placedPieces: [],
  selectedPiece: null,
  selectedPieceTransform: null,
  puzzleOrientation: null,
  
  setPuzzleContainer: (container) => set({ puzzleContainer: container }),
  setPuzzlePieces: (pieces) => set({ puzzlePieces: pieces }),
  setPlacedPieces: (pieces) => set({ placedPieces: pieces }),
  setSelectedPiece: (piece) => set({ selectedPiece: piece }),
  setSelectedPieceTransform: (transform) => set({ selectedPieceTransform: transform }),
  setPuzzleOrientation: (orientation) => set({ puzzleOrientation: orientation }),
  addPlacedPiece: (piece) => set((state) => ({ 
    placedPieces: [...state.placedPieces, piece] 
  })),
  removePlacedPiece: (id) => set((state) => ({ 
    placedPieces: state.placedPieces.filter(p => p.id !== id) 
  })),
}));
