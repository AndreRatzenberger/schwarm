import { create } from 'zustand'
import { useSettingsStore } from './settingsStore'

interface PauseState {
  isPaused: boolean
  error: string | null
  setIsPaused: (isBreak: boolean) => void
  fetchPauseState: () => Promise<void>
  togglePause: () => Promise<void>
  reset: () => void
}

export const usePauseStore = create<PauseState>((set, get) => ({
  isPaused: false,
  error: null,
  setIsPaused: (isPaused) => set({ isPaused: isPaused }),
  fetchPauseState: async () => {
    const { endpointUrl } = useSettingsStore.getState()
    try {
      const response = await fetch(`${endpointUrl}/break`, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Accept': 'application/json',
        },
        credentials: 'omit'
      })
      
      const isPause = await response.json()
      
      // Even if response.ok is false, if we got valid data, use it
      if (typeof isPause === 'boolean') {
        set({ isPaused: isPause, error: null })
      } else {
        throw new Error('Invalid pause state received')
      }
    } catch (error) {
      // Don't update pause state on error, just log it
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch pause state'
      console.warn('Pause state fetch warning:', errorMessage)
      set({ error: errorMessage })
    }
  },
  togglePause: async () => {
    const { endpointUrl } = useSettingsStore.getState()
    
    try {
      const response = await fetch(`${endpointUrl}/break`, {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Accept': 'application/json',
        },
        credentials: 'omit'
      })
      
      const result = await response.json()
      
      // If we got a valid boolean response, use it directly instead of fetching again
      if (typeof result === 'boolean') {
        set({ isPaused: result, error: null })
      } else {
        // If response is not what we expect, fetch the current state
        await get().fetchPauseState()
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to toggle pause state'
      console.warn('Pause toggle warning:', errorMessage)
      set({ error: errorMessage })
      
      // On error, fetch current state to ensure UI is in sync
      await get().fetchPauseState()
    }
  },
  reset: () => set({ isPaused: false, error: null })
}));
