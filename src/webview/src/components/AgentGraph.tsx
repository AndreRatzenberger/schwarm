import { useRef, useCallback, useMemo } from 'react';
import { Typography, Box } from '@mui/material';
import ForceGraph2D from 'react-force-graph-2d';
import { useDebugStore } from '../store/debugStore';

type NodeData = {
  id: string;
  name: string;
  model: string;
  val: number;
};

type LinkData = {
  source: string;
  target: string;
};

export default function AgentGraph() {
  const fgRef = useRef();
  const agents = useDebugStore((state) => state.agents);
  const connections = useDebugStore((state) => state.connections);
  const activeAgent = useDebugStore((state) => state.activeAgent);

  const graphData = useMemo(() => {
    const nodes = Array.from(agents.values()).map(agent => ({
      id: agent.name,
      name: agent.name,
      model: agent.model,
      val: 20
    }));

    const links = connections.map(conn => ({
      source: conn.from,
      target: conn.to
    }));

    return { nodes, links };
  }, [agents, connections]);

  const getNodeColor = useCallback((node: NodeData) => {
    return node.id === activeAgent ? '#90caf9' : '#64b5f6';
  }, [activeAgent]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Agent Interaction Graph
      </Typography>
      <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
        <ForceGraph2D
          ref={fgRef}
          graphData={graphData}
          nodeLabel={(node: NodeData) => `${node.name}\nModel: ${node.model}`}
          nodeColor={getNodeColor}
          nodeRelSize={6}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.005}
          linkColor={() => '#666'}
          backgroundColor="transparent"
          width={600}
          height={320}
        />
      </Box>
    </Box>
  );
}
