import { useCallback } from 'react'
import dynamic from 'next/dynamic'

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false })

interface Agent {
  id: string
  name: string
}

interface AgentLink {
  source: string
  target: string
}

const agents: Agent[] = Array.from({ length: 20 }, (_, i) => ({
  id: `agent-${i}`,
  name: `Agent ${i}`,
}))

const links: AgentLink[] = Array.from({ length: 30 }, () => ({
  source: agents[Math.floor(Math.random() * agents.length)].id,
  target: agents[Math.floor(Math.random() * agents.length)].id,
}))

interface AgentGraphProps {
  onSelectAgent: (agent: Agent | null) => void
}

export default function AgentGraph({ onSelectAgent }: AgentGraphProps) {
  const handleNodeClick = useCallback((node: Agent) => {
    onSelectAgent(node)
  }, [onSelectAgent])

  return (
    <ForceGraph2D
      graphData={{ nodes: agents, links }}
      nodeLabel="name"
      nodeColor={() => '#3b82f6'}
      linkColor={() => '#94a3b8'}
      onNodeClick={handleNodeClick}
      width={800}
      height={600}
    />
  )
}

