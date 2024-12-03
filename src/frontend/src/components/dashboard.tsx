import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import EventLog from './event-log'
import AgentGraph from './agent-graph'
import AgentDetails from './agent-details'
import AgentStatistics from './agent-statistics'
import MessageFlow from './message-flow'

export default function Dashboard() {
  const [selectedAgent, setSelectedAgent] = useState(null)

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Agent Framework Dashboard</h1>
      <Tabs defaultValue="graph" className="space-y-4">
        <TabsList>
          <TabsTrigger value="graph">Agent Graph</TabsTrigger>
          <TabsTrigger value="events">Event Log</TabsTrigger>
          <TabsTrigger value="stats">Statistics</TabsTrigger>
          <TabsTrigger value="flow">Message Flow</TabsTrigger>
        </TabsList>
        <TabsContent value="graph" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Connection Graph</CardTitle>
              <CardDescription>Visualize how agents are connected to each other</CardDescription>
            </CardHeader>
            <CardContent className="h-[600px]">
              <AgentGraph onSelectAgent={setSelectedAgent} />
            </CardContent>
          </Card>
          {selectedAgent && (
            <Card>
              <CardHeader>
                <CardTitle>Agent Details</CardTitle>
                <CardDescription>Information about the selected agent</CardDescription>
              </CardHeader>
              <CardContent>
                <AgentDetails agent={selectedAgent} />
              </CardContent>
            </Card>
          )}
        </TabsContent>
        <TabsContent value="events">
          <Card>
            <CardHeader>
              <CardTitle>Event Log</CardTitle>
              <CardDescription>Real-time log of all agent events</CardDescription>
            </CardHeader>
            <CardContent>
              <EventLog />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="stats">
          <Card>
            <CardHeader>
              <CardTitle>Agent Statistics</CardTitle>
              <CardDescription>Overview of agent performance and activity</CardDescription>
            </CardHeader>
            <CardContent>
              <AgentStatistics />
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="flow">
          <MessageFlow />
        </TabsContent>
      </Tabs>
    </div>
  )
}

