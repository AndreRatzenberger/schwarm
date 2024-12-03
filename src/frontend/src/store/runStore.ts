import { create } from 'zustand';
import type { Log } from '../types';

interface RunState {
  activeRunId: string | null;
  setActiveRunId: (id: string | null) => void;
  findRunIdFromLogs: (logs: Log[]) => string | null;
}

export const useRunStore = create<RunState>((set) => ({
  activeRunId: null,
  setActiveRunId: (id) => set({ activeRunId: id }),
  findRunIdFromLogs: (logs) => {
    // Find the most recent log with a run_id
    const runLog = [...logs]
      .reverse()
      .find(log => log.run_id);
    return runLog?.run_id || null;
  }
}));
