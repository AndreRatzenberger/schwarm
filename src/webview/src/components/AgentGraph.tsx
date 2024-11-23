import { useRef, useCallback, useMemo, } from 'react';
import { Typography, Box, useTheme } from '@mui/material';
import ForceGraph2D from 'react-force-graph-2d';
import { useDebugStore } from '../store/debugStore';
import { EventType } from '../types/events';

type NodeData = {
  id: string;
  name: string;
  model: string;
  val: number;
  interactions: number;
};

type LinkData = {
  source: string;
  target: string;
  interactions: number;
  lastInteraction: string;
};

export default function AgentGraph() {
  const theme = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const agents = useDebugStore((state) => state.agents);
  const connections = useDebugStore((state) => state.connections);
  const activeAgent = useDebugStore((state) => state.activeAgent);
  const events = useDebugStore((state) => state.eventHistory);

  const graphData = useMemo(() => {
    // Create nodes from agents with interaction counts
    const interactionCounts = new Map<string, number>();
    events.forEach(event => {
      const agentId = event.agent_id;
      interactionCounts.set(agentId, (interactionCounts.get(agentId) || 0) + 1);
    });

    const nodes = Array.from(agents.values()).map(agent => ({
      id: agent.name,
      name: agent.name,
      model: agent.model,
      val: 20 + (interactionCounts.get(agent.name) || 0) * 2, // Base size + interactions
      interactions: interactionCounts.get(agent.name) || 0
    }));

    // Create links with interaction counts and types
    const linkMap = new Map<string, LinkData>();
    connections.forEach(conn => {
      const linkId = `${conn.from}-${conn.to}`;
      const existingLink = linkMap.get(linkId);
      if (existingLink) {
        existingLink.interactions++;
      } else {
        linkMap.set(linkId, {
          source: conn.from,
          target: conn.to,
          interactions: 1,
          lastInteraction: events.find(e => 
            e.type === EventType.HANDOFF && 
            e.agent_id === conn.from
          )?.datetime || ''
        });
      }
    });

    return { 
      nodes, 
      links: Array.from(linkMap.values())
    };
  }, [agents, connections, events]);

  const getNodeColor = useCallback((node: NodeData) => {
    if (node.id === activeAgent) {
      return theme.palette.primary.main;
    }
    // Color based on model
    if (node.model.includes('gpt-4')) {
      return theme.palette.secondary.main;
    }
    return theme.palette.info.main;
  }, [activeAgent, theme]);

  const getLinkWidth = useCallback((link: LinkData) => {
    // Width based on interaction count
    return 1 + Math.min(link.interactions * 0.5, 3);
  }, []);

  const getLinkColor = useCallback((link: LinkData) => {
    // Color based on recency of interaction
    const age = Date.now() - new Date(link.lastInteraction).getTime();
    const opacity = Math.max(0.2, 1 - age / (1000 * 60 * 5)); // Fade over 5 minutes
    return `rgba(102, 102, 102, ${opacity})`;
  }, []);

  return (
    <Box 
      ref={containerRef}
      sx={{ 
        display: 'flex', 
        flexDirection: 'column', 
        height: '100%',
        position: 'relative'
      }}
    >
      <Typography variant="h6" gutterBottom sx={{ p: 2, pb: 0 }}>
        Agent Interaction Graph
      </Typography>
      <Box sx={{ 
        flex: 1, 
        display: 'flex', 
        justifyContent: 'center',
        '& canvas': {
          borderRadius: 1,
          backgroundColor: 'background.paper'
        }
      }}>
        <ForceGraph2D
          graphData={graphData}
          nodeLabel={(node: NodeData) => 
            `${node.name}\nModel: ${node.model}\nInteractions: ${node.interactions}`
          }
          nodeColor={getNodeColor}
          nodeRelSize={6}
          nodeVal={(node: NodeData) => node.val}
          linkWidth={getLinkWidth}
          linkColor={getLinkColor}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={d => d.interactions * 0.001}
          linkDirectionalParticleWidth={2}
          backgroundColor={theme.palette.background.paper}
          width={containerRef.current?.clientWidth || 800}
          height={containerRef.current?.clientHeight || 600}
        />
      </Box>
    </Box>
  );
}
