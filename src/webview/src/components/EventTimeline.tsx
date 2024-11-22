import { useEffect, useRef } from 'react';
import { Box, Heading, Stack, Text, Badge, Flex } from '@chakra-ui/react';
import { useDebugStore } from '../store/debugStore';
import { Event, EventType, Message, BudgetData } from '../types/events';

const eventTypeColors: Record<EventType, string> = {
  agent_start: 'green',
  message_completion: 'blue',
  tool_execution: 'purple',
  tool_result: 'cyan',
  handoff: 'orange',
  budget_update: 'yellow',
  reset: 'red',
};

const eventTypeLabels: Record<EventType, string> = {
  agent_start: 'Agent Started',
  message_completion: 'Message',
  tool_execution: 'Tool Call',
  tool_result: 'Tool Result',
  handoff: 'Agent Handoff',
  budget_update: 'Budget Update',
  reset: 'Reset',
};

interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
}

function formatEventContent(event: Event): string {
  switch (event.type) {
    case 'agent_start': {
      type AgentStartPayload = { agent: { name: string } };
      const data = event.data as AgentStartPayload;
      return `Agent ${data.agent.name} initialized`;
    }
    
    case 'message_completion': {
      type MessageCompletionPayload = { agent: string; message: Message };
      const data = event.data as MessageCompletionPayload;
      return data.message.content;
    }
    
    case 'tool_execution': {
      const tools = event.data as ToolCall[];
      return tools
        .map((tool) => `${tool.name}(${JSON.stringify(tool.arguments)})`)
        .join(', ');
    }
    
    case 'tool_result': {
      const messages = event.data as Message[];
      return messages
        .map((msg) => msg.content)
        .join('\n');
    }
    
    case 'handoff': {
      type HandoffPayload = { from: string; to: string; message: Message };
      const data = event.data as HandoffPayload;
      return `From ${data.from} to ${data.to}`;
    }
    
    case 'budget_update': {
      const data = event.data as BudgetData;
      return `Spent: $${data.current_spent.toFixed(2)} / $${data.max_spent.toFixed(2)}`;
    }
    
    case 'reset':
      return 'System reset';
    
    default:
      return 'Unknown event';
  }
}

export default function EventTimeline() {
  const { eventHistory } = useDebugStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [eventHistory]);

  return (
    <Box>
      <Heading size="md" mb={4}>Event Timeline</Heading>
      <Box
        ref={scrollRef}
        height="320px"
        overflowY="auto"
        css={{
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: 'var(--chakra-colors-gray-100)',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'var(--chakra-colors-gray-300)',
            borderRadius: '4px',
          },
        }}
      >
        <Stack gap={3}>
          {eventHistory.map((event, index) => (
            <Box
              key={index}
              p={3}
              bg="var(--chakra-colors-white)"
              borderRadius="md"
              borderLeft="4px solid"
              borderLeftColor={`${eventTypeColors[event.type]}.500`}
              boxShadow="sm"
              _dark={{
                bg: 'var(--chakra-colors-gray-800)',
              }}
            >
              <Flex justify="space-between" align="center" mb={2}>
                <Badge colorScheme={eventTypeColors[event.type]}>
                  {eventTypeLabels[event.type]}
                </Badge>
                <Text fontSize="sm" color="gray.500">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </Text>
              </Flex>
              <Text fontSize="sm" whiteSpace="pre-wrap">
                {formatEventContent(event)}
              </Text>
            </Box>
          ))}
        </Stack>
      </Box>
    </Box>
  );
}
