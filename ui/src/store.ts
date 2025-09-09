import { create } from "zustand";

type Status = { ok: boolean | null; message: string };

type State = {
  tab: "home" | "viewer" | "dashboard" | "status" | "run" | "view";
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
};

export const useAppStore = create<State>((set) => ({
  tab: "home",
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
}));
