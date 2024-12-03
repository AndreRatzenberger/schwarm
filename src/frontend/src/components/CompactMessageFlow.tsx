import { useEffect, useState } from 'react'
import { MessageSquare } from 'lucide-react'
import { useLogStore } from '../store/logStore'
import { ScrollArea } from './ui/scroll-area'
import { formatTextToEventType } from '../lib/utils'
import type { Log } from '../types'

const levelColors = {
  INFO: { bg: 'bg-blue-100', text: 'text-blue-800' },
  WARN: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
  ERROR: { bg: 'bg-red-100', text: 'text-red-800' },
  LOG: { bg: 'bg-gray-100', text: 'text-gray-800' },
  START_TURN: { bg: 'bg-green-100', text: 'text-green-800' },
  INSTRUCT: { bg: 'bg-purple-100', text: 'text-purple-800' },
  MESSAGE_COMPLETION: { bg: 'bg-indigo-100', text: 'text-indigo-800' },
  POST_MESSAGE_COMPLETION: { bg: 'bg-teal-100', text: 'text-teal-800' },
  TOOL_EXECUTION: { bg: 'bg-orange-100', text: 'text-orange-800' },
  POST_TOOL_EXECUTION: { bg: 'bg-pink-100', text: 'text-pink-800' },
  HANDOFF: { bg: 'bg-cyan-100', text: 'text-cyan-800' }
} as const

type ChatLog = Log & {
  type: keyof typeof levelColors
}

export default function CompactMessageFlow() {
  const [items, setItems] = useState<ChatLog[]>([])
  const [agentSides, setAgentSides] = useState<Map<string, 'left' | 'right'>>(new Map())
  const getFilteredLogs = useLogStore(state => state.getFilteredLogs)
  const logs = getFilteredLogs()

  useEffect(() => {
    // Filter and transform logs to chat format
    const chatLogs = logs
      .filter((log): log is Log & { level: keyof typeof levelColors } =>
        log.level === 'INSTRUCT' ||
        log.level === 'MESSAGE_COMPLETION' ||
        log.level === 'START_TURN' ||
        log.level === 'TOOL_EXECUTION'
      )
      .map(log => ({
        ...log,
        type: log.level
      }))
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
      .slice(-5) // Only show last 5 messages

    // Determine agent sides
    const newAgentSides = new Map<string, 'left' | 'right'>()
    let lastSide: 'left' | 'right' = 'left'

    chatLogs.forEach(log => {
      if (!newAgentSides.has(log.agent)) {
        newAgentSides.set(log.agent, lastSide)
        lastSide = lastSide === 'left' ? 'right' : 'left'
      }
    })

    setAgentSides(newAgentSides)
    setItems(chatLogs)
  }, [logs])

  const renderItem = (item: ChatLog) => {
    const side = agentSides.get(item.agent) || 'left'
    const colors = levelColors[item.type] || levelColors.LOG

    return (
      <div key={item.id} className={`flex flex-col ${side === 'right' ? 'items-end' : 'items-start'}`}>
        <div className={`max-w-[70%] rounded-lg p-2 ${colors.bg} ${colors.text} ml-2 mr-2`}>
          <div className="flex items-center space-x-2">
            <MessageSquare className="h-3 w-3" />
            <span className="font-semibold text-xs">
              {item.agent} - {item.level}
            </span>
          </div>
          <p className="text-xs mt-1 line-clamp-2">
            {formatTextToEventType(item)}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <ScrollArea className="h-[300px] w-full rounded-md border p-2">
        <div className="space-y-2">
          {items.map(renderItem)}
        </div>
      </ScrollArea>
    </div>
  )
}
