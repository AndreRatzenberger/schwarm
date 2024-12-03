import React, { useEffect, useState } from 'react';
import ReactFlow, { Background, Edge, Node, MarkerType } from 'reactflow';
import { useLogStore } from '../store/logStore';
import 'reactflow/dist/style.css';

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

function CompactNetworkView() {
  const getFilteredLogs = useLogStore(state => state.getFilteredLogs);
  const logs = getFilteredLogs();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  useEffect(() => {
    const agents = new Map();
    const connections = new Map();
    let nextColorIndex = 0;

    // Initialize agent data
    logs.forEach(log => {
      if (!agents.has(log.agent)) {
        agents.set(log.agent, {
          events: 0,
          colorIndex: nextColorIndex++ % colorPalette.length
        });
      }
    });

    // Process connections
    logs.forEach((log, index) => {
      if (index > 0) {
        const prevLog = logs[index - 1];
        if (prevLog.agent !== log.agent) {
          const connectionKey = `${prevLog.agent}-${log.agent}`;
          connections.set(connectionKey, (connections.get(connectionKey) || 0) + 1);
        }
      }
    });

    // Create nodes
    const nodeArray: Node[] = Array.from(agents.entries()).map(([name, data], index) => {
      const angle = (2 * Math.PI * index) / agents.size;
      const radius = 100;
      const x = 150 + radius * Math.cos(angle);
      const y = 100 + radius * Math.sin(angle);
      const colors = colorPalette[data.colorIndex];

      return {
        id: name,
        position: { x, y },
        data: {
          label: (
            <div className={`p-1 rounded-lg shadow-sm border ${colors.bg} ${colors.text}`}>
              <div className="font-medium text-xs">{name}</div>
            </div>
          )
        },
        style: {
          width: 'auto',
          borderRadius: '4px'
        }
      };
    });

    // Create edges
    const edgeArray: Edge[] = Array.from(connections.entries()).map(([key, count]) => {
      const [source, target] = key.split('-');
      const sourceAgent = agents.get(source);
      const sourceColors = colorPalette[sourceAgent.colorIndex];

      return {
        id: key,
        source,
        target,
        type: 'smoothstep',
        style: {
          stroke: sourceColors.color,
          strokeWidth: 1 + Math.min(count / 5, 2)
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: sourceColors.color,
        }
      };
    });

    setNodes(nodeArray);
    setEdges(edgeArray);
  }, [logs]);

  return (
    <div className="bg-white rounded-lg shadow-sm" style={{ height: '250px' }}>
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        fitView
        defaultEdgeOptions={{ 
          type: 'smoothstep',
          style: { strokeWidth: 2 }
        }}
      >
        <Background color="#E5E7EB" />
      </ReactFlow>
    </div>
  );
}

export default CompactNetworkView;
