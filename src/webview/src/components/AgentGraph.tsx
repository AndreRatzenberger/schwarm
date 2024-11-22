import { useEffect, useRef } from 'react';
import { Box, Heading } from '@chakra-ui/react';
import * as d3 from 'd3';
import { useDebugStore } from '../store/debugStore';

interface Node extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  model: string;
  active: boolean;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: Node;
  target: Node;
}

export default function AgentGraph() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { agents, activeAgent, connections } = useDebugStore();

  useEffect(() => {
    if (!svgRef.current) return;

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();

    // Convert agents to nodes
    const nodes: Node[] = Array.from(agents.entries()).map(([name, agent]) => ({
      id: name,
      name,
      model: agent.model,
      active: name === activeAgent,
    }));

    // Create a map for quick node lookup
    const nodeMap = new Map(nodes.map(node => [node.id, node]));

    // Convert connections to links
    const links: Link[] = connections
      .map(({ from, to }) => {
        const sourceNode = nodeMap.get(from);
        const targetNode = nodeMap.get(to);
        if (!sourceNode || !targetNode) return null;
        return {
          source: sourceNode,
          target: targetNode,
        };
      })
      .filter((link): link is Link => link !== null);

    // Set up SVG
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;
    const svg = d3.select(svgRef.current);

    // Create arrow marker for links
    svg.append('defs')
      .append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-10 -10 20 20')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M -10,-5 L 0,0 L -10,5')
      .attr('fill', '#718096');

    // Create simulation
    const simulation = d3.forceSimulation<Node>(nodes)
      .force('link', d3.forceLink<Node, Link>(links).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Create links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#718096')
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrowhead)');

    // Create nodes
    const node = svg.append('g')
      .selectAll<SVGGElement, Node>('g')
      .data(nodes)
      .join('g');

    // Add drag behavior
    const drag = d3.drag<SVGGElement, Node>()
      .on('start', dragStarted)
      .on('drag', dragged)
      .on('end', dragEnded);

    node.call(drag as d3.DragBehavior<SVGGElement, Node, Node>);

    // Add circles to nodes
    node.append('circle')
      .attr('r', 25)
      .attr('fill', d => d.active ? '#4299E1' : '#A0AEC0')
      .attr('stroke', '#2C5282')
      .attr('stroke-width', 2);

    // Add text to nodes
    node.append('text')
      .text(d => d.name)
      .attr('text-anchor', 'middle')
      .attr('dy', '.3em')
      .attr('fill', 'white')
      .style('font-size', '12px');

    // Add tooltips
    node.append('title')
      .text(d => `${d.name}\nModel: ${d.model}`);

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as Node).x!)
        .attr('y1', d => (d.source as Node).y!)
        .attr('x2', d => (d.target as Node).x!)
        .attr('y2', d => (d.target as Node).y!);

      node
        .attr('transform', d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragStarted(event: d3.D3DragEvent<SVGGElement, Node, Node>) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, Node, Node>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragEnded(event: d3.D3DragEvent<SVGGElement, Node, Node>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [agents, activeAgent, connections]);

  return (
    <Box>
      <Heading size="md" mb={4}>Agent Interaction Graph</Heading>
      <Box position="relative" width="100%" height="320px">
        <svg
          ref={svgRef}
          width="100%"
          height="100%"
          style={{ overflow: 'visible' }}
        />
      </Box>
    </Box>
  );
}
