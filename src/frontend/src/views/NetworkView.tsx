import React, { useState, useMemo } from 'react';
import ReactFlow, { Background, Controls, MarkerType, Edge, Node } from 'reactflow';
import { useLogStore } from '../store/logStore';
import 'reactflow/dist/style.css';

// Moved outside component to prevent recreation
const colorPalette = [
  { bg: 'bg-blue-100', text: 'text-blue-800', color: '#3B82F6' },
  { bg: 'bg-purple-100', text: 'text-purple-800', color: '#8B5CF6' },
  { bg: 'bg-green-100', text: 'text-green-800', color: '#10B981' },
  { bg: 'bg-orange-100', text: 'text-orange-800', color: '#F97316' },
  { bg: 'bg-pink-100', text: 'text-pink-800', color: '#EC4899' },
  { bg: 'bg-cyan-100', text: 'text-cyan-800', color: '#06B6D4' },
  { bg: 'bg-yellow-100', text: 'text-yellow-800', color: '#F59E0B' },
  { bg: 'bg-red-100', text: 'text-red-800', color: '#EF4444' },
  { bg: 'bg-indigo-100', text: 'text-indigo-800', color: '#6366F1' }
];

// Default edge options moved outside to prevent recreation
const defaultEdgeOptions = {
  type: 'smoothstep',
  style: { strokeWidth: 2 }
};

interface AgentData {
  events: number;
  eventTypes: Map<string, number>;
  colorIndex: number;
  lastEventTime: string;
}

interface ConnectionData {
  count: number;
  eventTypes: Map<string, number>;
}

function NetworkView() {
  const getFilteredLogs = useLogStore(state => state.getFilteredLogs);
  const logs = useMemo(() => getFilteredLogs(), [getFilteredLogs]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // Memoize the graph data processing
  const { nodes, edges } = useMemo(() => {
    const agentMap = new Map<string, AgentData>();
    const connectionMap = new Map<string, ConnectionData>();
    let nextColorIndex = 0;
    let latestTimestamp = '';
    let latestConnection = '';

    // First pass: Initialize agents
    logs.forEach(log => {
      if (!agentMap.has(log.agent)) {
        agentMap.set(log.agent, {
          events: 0,
          eventTypes: new Map<string, number>(),
          colorIndex: nextColorIndex++ % colorPalette.length,
          lastEventTime: log.timestamp
        });
      }
    });

    // Second pass: Process connections and events
    for (let i = 1; i < logs.length; i++) {
      const currentLog = logs[i];
      const prevLog = logs[i - 1];
      const agent = agentMap.get(currentLog.agent);
      
      if (agent) {
        // Update agent stats
        agent.events++;
        agent.lastEventTime = currentLog.timestamp;
        agent.eventTypes.set(
          currentLog.level,
          (agent.eventTypes.get(currentLog.level) || 0) + 1
        );

        // Process connections
        if (prevLog.agent !== currentLog.agent) {
          const connectionKey = `${prevLog.agent}-${currentLog.agent}`;
          const connection = connectionMap.get(connectionKey) || {
            count: 0,
            eventTypes: new Map<string, number>()
          };

          connection.count++;
          connection.eventTypes.set(
            currentLog.level,
            (connection.eventTypes.get(currentLog.level) || 0) + 1
          );
          connectionMap.set(connectionKey, connection);

          if (currentLog.timestamp > latestTimestamp) {
            latestTimestamp = currentLog.timestamp;
            latestConnection = connectionKey;
          }
        }
      }
    }

    // Create nodes
    const nodeArray: Node[] = Array.from(agentMap.entries()).map(([name, data], index) => {
      const angle = (2 * Math.PI * index) / agentMap.size;
      const radius = 200;
      const x = 400 + radius * Math.cos(angle);
      const y = 300 + radius * Math.sin(angle);
      const colors = colorPalette[data.colorIndex];
      const isSelected = name === selectedAgent;

      return {
        id: name,
        position: { x, y },
        data: {
          label: (
            <div 
              className={`p-2 rounded-lg shadow-sm border transition-all duration-200 
                ${colors.bg} ${colors.text} 
                ${isSelected ? 'ring-2 ring-blue-500 scale-110' : ''}`}
              onClick={() => setSelectedAgent(prev => prev === name ? null : name)}
            >
              <div className="font-medium text-sm">{name}</div>
              <div className="text-xs mt-1">
                {[...data.eventTypes.entries()]
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 2)
                  .map(([type, count]) => (
                    <div key={type} className="flex justify-between gap-2">
                      <span>{type}:</span>
                      <span>{count}</span>
                    </div>
                  ))}
              </div>
            </div>
          )
        },
        style: {
          width: 'auto',
          borderRadius: '8px'
        }
      };
    });

    // Create edges
    const edgeArray: Edge[] = Array.from(connectionMap.entries())
      .filter(([key]) => {
        if (!selectedAgent) return true;
        const [source, target] = key.split('-');
        return source === selectedAgent || target === selectedAgent;
      })
      .flatMap(([key, data]) => {
        const [source, target] = key.split('-');
        const sourceAgent = agentMap.get(source);
        const colors = sourceAgent ? colorPalette[sourceAgent.colorIndex] : colorPalette[0];
        const isLatest = key === latestConnection;

        if (!selectedAgent) {
          // Show simplified view when no agent is selected
          return [{
            id: key,
            source,
            target,
            animated: isLatest,
            style: {
              stroke: colors.color,
              strokeWidth: isLatest ? 3 : 1 + Math.min(data.count / 2, 3)
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: colors.color
            }
          }];
        } else {
          // Show detailed view when an agent is selected
          return Array.from(data.eventTypes.entries()).map(([type, count], index) => ({
            id: `${key}-${type}`,
            source,
            target,
            animated: isLatest && index === 0,
            style: {
              stroke: colors.color,
              strokeWidth: 1 + Math.min(count / 2, 3),
              transform: `translateY(${index * 2}px)`
            },
            markerEnd: {
              type: MarkerType.ArrowClosed,
              color: colors.color
            },
            label: `${type} (${count})`,
            labelStyle: { fontSize: 10 },
            labelBgStyle: { fill: '#F3F4F6' }
          }));
        }
      });

    return { nodes: nodeArray, edges: edgeArray };
  }, [logs, selectedAgent]);

  return (
    <div className="bg-white rounded-lg shadow-sm p-4" style={{ height: '80vh' }}>
      <ReactFlow 
        nodes={nodes}
        edges={edges}
        fitView
        defaultEdgeOptions={defaultEdgeOptions}
      >
        <Background color="#E5E7EB" />
        <Controls />
      </ReactFlow>
      {selectedAgent && (
        <div className="absolute bottom-4 left-4 bg-white p-2 rounded-lg shadow-sm border text-sm">
          <div className="font-medium mb-1">Selected: {selectedAgent}</div>
          <div className="text-gray-500">Click agent again to deselect</div>
        </div>
      )}
    </div>
  );
}

export default NetworkView;
