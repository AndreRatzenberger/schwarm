import { create } from 'zustand';
import type { Log } from '../types';
import { useRunStore } from './runStore';

interface LogState {
  logs: Log[];
  latestId: string | null;
  setLogs: (logs: Log[]) => void;
  appendLogs: (newLogs: Log[]) => void;
  setLatestId: (id: string) => void;
  reset: () => void;
  getFilteredLogs: () => Log[];
}

function isLogPartOfRun(log: Log, runId: string | null): boolean {
  if (!runId) return true; // If no run is selected, show all logs
  if (log.id === runId) return true; // This is the run log itself
  if (log.run_id === runId) return true; // This log is part of the run
  
  return false;
}

export const useLogStore = create<LogState>((set, get) => ({
  logs: [],
  latestId: null,
  setLogs: (logs) => set({ 
    logs,
    latestId: logs.length > 0 ? logs[logs.length - 1].id : null
  }),
  appendLogs: (newLogs) => set((state) => ({ 
    logs: [...state.logs, ...newLogs],
    latestId: newLogs.length > 0 ? newLogs[newLogs.length - 1].id : state.latestId
  })),
  setLatestId: (id) => set({ latestId: id }),
  reset: () => set({ logs: [], latestId: null }),
  getFilteredLogs: () => {
    const state = get();
    const activeRunId = useRunStore.getState().activeRunId;
    return state.logs.filter(log => isLogPartOfRun(log, activeRunId));
  }
}));
