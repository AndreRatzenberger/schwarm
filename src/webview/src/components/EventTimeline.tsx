import { useMemo } from 'react';
import { Box, Typography } from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
} from '@mui/lab';
import {
  Message as MessageIcon,
  Code as CodeIcon,
  Person as PersonIcon,
  SwapHoriz as SwapIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useDebugStore } from '../store/debugStore';
import { Event, EventType, EventPayload } from '../types/events';

const getEventIcon = (type: EventType) => {
  switch (type) {
    case 'agent_start':
      return <PersonIcon />;
    case 'message_completion':
      return <MessageIcon />;
    case 'tool_execution':
      return <CodeIcon />;
    case 'handoff':
      return <SwapIcon />;
    default:
      return <ErrorIcon />;
  }
};

const getEventColor = (type: EventType) => {
  switch (type) {
    case 'agent_start':
      return 'primary.main';
    case 'message_completion':
      return 'success.main';
    case 'tool_execution':
      return 'info.main';
    case 'handoff':
      return 'warning.main';
    default:
      return 'error.main';
  }
};

const formatEventContent = (event: Event) => {
  const data = event.data as any; // Temporary type assertion for development
  
  switch (event.type) {
    case 'agent_start':
      return `Agent ${data.agent?.name || 'Unknown'} started`;
    case 'message_completion':
      return `Message from ${data.agent || 'Unknown'}`;
    case 'tool_execution': {
      const tools = Array.isArray(data) ? data : [];
      return `Tool executed: ${tools[0]?.name || 'Unknown tool'}`;
    }
    case 'handoff':
      return `Handoff from ${data.from || 'Unknown'} to ${data.to || 'Unknown'}`;
    case 'tool_result':
      return `Tool result received`;
    case 'budget_update':
      return `Budget: ${data.current_spent?.toFixed(2) || 0}/${data.max_spent?.toFixed(2) || 0}`;
    case 'reset':
      return 'System reset';
    default:
      return 'Unknown event';
  }
};

export default function EventTimeline() {
  const events = useDebugStore((state) => state.eventHistory);

  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
  }, [events]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Event Timeline
      </Typography>
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <Timeline>
          {sortedEvents.map((event, index) => (
            <TimelineItem key={`${event.timestamp}-${index}`}>
              <TimelineSeparator>
                <TimelineDot sx={{ bgcolor: getEventColor(event.type) }}>
                  {getEventIcon(event.type)}
                </TimelineDot>
                {index < events.length - 1 && <TimelineConnector />}
              </TimelineSeparator>
              <TimelineContent>
                <Typography variant="body1">
                  {formatEventContent(event)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </Typography>
              </TimelineContent>
            </TimelineItem>
          ))}
        </Timeline>
      </Box>
    </Box>
  );
}
