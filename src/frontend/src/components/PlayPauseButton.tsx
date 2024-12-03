import React, { useEffect } from 'react'
import { Play, Pause } from 'lucide-react'
import { usePauseStore } from '../store/pauseStore'
import { useSettingsStore } from '../store/settingsStore'
import { Button } from "@/components/ui/button"


export default function PlayPauseButton() {
  const { isPaused, fetchPauseState, togglePause } = usePauseStore()
  const { refreshInterval } = useSettingsStore()

  useEffect(() => {
    // Initial fetch
    fetchPauseState()
    if (!refreshInterval) return

    // Set up interval for periodic fetching
    const intervalId = setInterval(fetchPauseState, refreshInterval)

    // Cleanup interval on unmount or when interval changes
    return () => clearInterval(intervalId)
  }, [refreshInterval, fetchPauseState])

  return (
    <Button
      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      onClick={togglePause}
    >

      {isPaused ? (
        <>
          <Play className="h-5 w-5 mr-2" />
          Resume
        </>
      ) : (
        <>
          <Pause className="h-5 w-5 mr-2" />
          Pause
        </>
      )}
  
    </Button>
  )
}
