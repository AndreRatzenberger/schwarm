import { ScrollArea } from './ui/scroll-area'

interface AgentDetailsPanelProps {
  agent: string;
  details: Record<string, unknown>;
}

export function AgentDetailsPanel({ agent, details }: AgentDetailsPanelProps) {
  return (
    <div className="w-[300px] border-r">
      <div className="p-4 border-b">
        <h3 className="font-semibold">Agent Details: {agent}</h3>
        <p className="text-sm text-muted-foreground">
          Detailed information about the agent and its properties.
        </p>
      </div>
      <ScrollArea className="h-[calc(100vh-200px)]">
        <div className="p-4 space-y-4">
          {Object.entries(details).map(([key, value]) => (
            <div key={key} className="border-b pb-2">
              <h3 className="font-semibold text-sm">{key}</h3>
              <p className="text-sm">
                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
              </p>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
