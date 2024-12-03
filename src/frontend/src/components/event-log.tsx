'use client'

import { useEffect, useState } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'

interface LogEvent {
  id: string
  timestamp: string
  agentId: string
  eventType: string
  description: string
}

export default function EventLog() {
  const [events, setEvents] = useState<LogEvent[]>([])

  useEffect(() => {
    // Simulating real-time events
    const interval = setInterval(() => {
      const newEvent: LogEvent = {
        id: Math.random().toString(36).substr(2, 9),
        timestamp: new Date().toISOString(),
        agentId: `Agent-${Math.floor(Math.random() * 10)}`,
        eventType: ['Task Started', 'Task Completed', 'Error', 'Communication'][Math.floor(Math.random() * 4)],
        description: 'Event description...',
      }
      setEvents((prevEvents) => [newEvent, ...prevEvents].slice(0, 100)) // Keep last 100 events
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <ScrollArea className="h-[500px]">
      <div className="space-y-2">
        {events.map((event) => (
          <div key={event.id} className="bg-muted p-2 rounded">
            <div className="flex justify-between text-sm">
              <span className="font-medium">{event.agentId}</span>
              <span className="text-muted-foreground">{new Date(event.timestamp).toLocaleTimeString()}</span>
            </div>
            <div className="text-sm font-medium">{event.eventType}</div>
            <div className="text-sm text-muted-foreground">{event.description}</div>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}

