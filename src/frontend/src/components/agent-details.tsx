interface Agent {
  id: string
  name: string
}

interface AgentDetailsProps {
  agent: Agent
}

export default function AgentDetails({ agent }: AgentDetailsProps) {
  return (
    <div>
      <h3 className="text-lg font-medium">{agent.name}</h3>
      <p className="text-sm text-muted-foreground">ID: {agent.id}</p>
      {/* Add more agent details here */}
    </div>
  )
}

