import { create } from 'zustand';
import type { Span } from '../types';

interface DataState {
  data: Span[] | null;
  setData: (data: Span[] | null) => void;
  fetchData: () => void;
  error: string | null;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useDataStore = create<DataState>((set) => ({
  data: null,
  setData: (data) => set({ data }),
  fetchData: () => {},
  error: null,
  setError: (error) => set({ error }),
  reset: () => set({ data: null, error: null })
}));
