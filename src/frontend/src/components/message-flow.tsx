import { useEffect, useRef, useState } from 'react'
import { Card, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { ScrollArea } from './ui/scroll-area'
import { MessageSquare } from 'lucide-react'
import { AgentDetailsPanel } from './agent-details-panel'
import { useLogStore } from '../store/logStore'
import { useStreamStore } from '../store/streamStore'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
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

const EventFlow = () => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [items, setItems] = useState<ChatLog[]>([])
  const [selectedItem, setSelectedItem] = useState<ChatLog | null>(null)
  const [agentSides, setAgentSides] = useState<Map<string, 'left' | 'right'>>(new Map())
  const scrollAreaRef = useRef<HTMLDivElement>(null)
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

    if (selectedAgent && selectedAgent !== 'all') {
      setItems(chatLogs.filter(item => item.agent === selectedAgent))
    } else {
      setItems(chatLogs)
    }

    // Auto-select the newest item if none is selected
    if (!selectedItem && chatLogs.length > 0) {
      setSelectedItem(chatLogs[chatLogs.length - 1])
    }
  }, [logs, selectedAgent])

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [items])

  const agents = Array.from(new Set(logs.map(log => log.agent)))

  const handleItemClick = (item: ChatLog) => {
    setSelectedItem(item)
  }

  const renderItem = (item: ChatLog) => {
    const side = agentSides.get(item.agent) || 'left'
    const colors = levelColors[item.type] || levelColors.LOG

    return (
      <div key={item.id} className={`flex flex-col ${side === 'right' ? 'items-end' : 'items-start'}`}>
        <div
          className={`max-w-[70%] rounded-lg p-3 ${colors.bg} ${colors.text} ml-4 mr-4 cursor-pointer hover:opacity-80 transition-opacity ${selectedItem?.id === item.id ? 'ring-2 ring-blue-500' : ''}`}
          onClick={() => handleItemClick(item)}
        >
          <div className="flex items-center space-x-2 mb-1">
            <MessageSquare className="h-4 w-4" />
            <span className="font-semibold text-sm">
              {item.agent}
            </span>
          </div>
          <p className="text-sm">
            {item.message}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {new Date(item.timestamp).toLocaleString()}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <Select onValueChange={setSelectedAgent}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select an agent" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Agents</SelectItem>
          {agents.map(agent => (
            <SelectItem key={agent} value={agent}>{agent}</SelectItem>
          ))}
        </SelectContent>
      </Select>
      <div className="mt-4 flex">
        <AgentDetailsPanel
          agent={selectedItem?.agent || 'No Selection'}
          details={selectedItem?.attributes || {}}
        />
        <div className="flex-1 ml-4">
          <ScrollArea className="h-[600px] w-full rounded-md border p-4" ref={scrollAreaRef}>
            <div className="space-y-4">
              {items.map(renderItem)}
            </div>
          </ScrollArea>
        </div>
      </div>
    </div>
  )
}

const MessageFlow = () => {
  const messages = useStreamStore(state => state.messages)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div>
      <ScrollArea className="h-[600px] w-full rounded-md border p-4" ref={scrollAreaRef}>
        <div className="space-y-4">
          {messages.map(message => (
            <div key={message.id} className="flex flex-col items-start">
              <div className="max-w-[70%] rounded-lg p-3 bg-gray-100 text-gray-800 ml-4 mr-4">
                <p className="text-sm whitespace-pre-wrap">
                  {message.content}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {new Date(message.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}

export default function MessageFlowTabs() {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Message Flow Visualization</CardTitle>
        <CardDescription>Track agent interactions and message streams</CardDescription>
        <Tabs defaultValue="event-flow" className="w-full">
          <TabsList>
            <TabsTrigger value="event-flow">Event Flow</TabsTrigger>
            <TabsTrigger value="message-flow">Message Flow</TabsTrigger>
          </TabsList>
          <TabsContent value="event-flow">
            <EventFlow />
          </TabsContent>
          <TabsContent value="message-flow">
            <MessageFlow />
          </TabsContent>
        </Tabs>
      </CardHeader>
    </Card>
  )
}
