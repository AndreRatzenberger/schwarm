import { create } from 'zustand';
import { useSettingsStore } from './settingsStore';

interface BreakpointState {
  breakpoints: {
    on_start: boolean;
    on_handoff: boolean;
    on_instruct: boolean;
    on_message_completion: boolean;
    on_post_message_completion: boolean;
    on_start_turn: boolean;
    on_tool_execution: boolean;
    on_post_tool_execution: boolean;
  };
  turnAmount: number;
  fetchBreakpoints: () => Promise<void>;
  fetchTurnAmount: () => Promise<void>;
  toggleBreakpoint: (key: keyof BreakpointState['breakpoints']) => Promise<void>;
  setTurnAmount: (amount: number) => Promise<void>;
}

export const useBreakpointStore = create<BreakpointState>((set) => ({
  breakpoints: {
    on_start: false,
    on_handoff: false,
    on_instruct: false,
    on_message_completion: false,
    on_post_message_completion: false,
    on_start_turn: false,
    on_tool_execution: false,
    on_post_tool_execution: false,
  },
  turnAmount: 1,
  fetchBreakpoints: async () => {
    const { endpointUrl } = useSettingsStore.getState();
    try {
      const response = await fetch(`${endpointUrl}/breakpoint`);
      const data = await response.json();
      set({ breakpoints: data });
    } catch (error) {
      console.error('Failed to fetch breakpoints:', error);
    }
  },
  fetchTurnAmount: async () => {
    const { endpointUrl } = useSettingsStore.getState();
    try {
      const response = await fetch(`${endpointUrl}/breakpoint/turns`);
      const data = await response.json();
      set({ turnAmount: data.turn_amount || 1 });
    } catch (error) {
      console.error('Failed to fetch turn amount:', error);
    }
  },
  toggleBreakpoint: async (key) => {
    const { endpointUrl } = useSettingsStore.getState();
    try {
      const response = await fetch(`${endpointUrl}/breakpoint?event_type=${key}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      if (response.ok) {
        const { breakpoints } = useBreakpointStore.getState();
        set({
          breakpoints: {
            ...breakpoints,
            [key]: !breakpoints[key],
          },
        });
      }
    } catch (error) {
      console.error('Failed to toggle breakpoint:', error);
    }
  },
  setTurnAmount: async (amount) => {
    const { endpointUrl } = useSettingsStore.getState();
    try {
      const response = await fetch(`${endpointUrl}/breakpoint/turns?turn_amount=${amount}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      if (response.ok) {
        set({ turnAmount: amount });
      }
    } catch (error) {
      console.error('Failed to set turn amount:', error);
    }
  },
}));
