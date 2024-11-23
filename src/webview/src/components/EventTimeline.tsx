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
  Info as InfoIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useDebugStore } from '../store/debugStore';
import { Event, EventType, ProviderContext } from '../types/events';

const getEventIcon = (type: EventType) => {
  switch (type) {
    case 'on_start':
      return <PersonIcon />;
    case 'on_post_message_completion':
      return <MessageIcon />;
    case 'on_tool_execution':
      return <CodeIcon />;
    case 'on_handoff':
      return <SwapIcon />;
    case 'on_instruct':
        return <InfoIcon />;
    default:
      return <ErrorIcon />;
  }
};

const getEventColor = (type: EventType) => {
  switch (type) {
    case 'on_start':
      return 'primary.main';
    case 'on_post_message_completion':
      return 'success.main';
    case 'on_tool_execution':
      return 'info.main';
    case 'on_handoff':
      return 'warning.main';
    case 'on_instruct':
      return 'info.main';
    default:
      return 'error.main';
  }
};

const formatEventContent = (event: Event) => {
  const data = event.payload as ProviderContext; // Temporary type assertion for development
  
  switch (event.type) {
    case 'on_start':
      return `Agent ${data.current_agent?.name || 'Unknown'} started`;
    case 'on_post_message_completion':
      return `Message from ${data.current_agent || 'Unknown'}`;
    case 'on_tool_execution': {
      const tools = Array.isArray(data) ? data : [];
      return `Tool executed: ${tools[0]?.name || 'Unknown tool'}`;
    }
    case 'on_handoff':
      return `Handoff from ${data.current_agent || 'Unknown'} to ${data.current_agent || 'Unknown'}`;
    default:
      return 'Unknown event';
  }
};

export default function EventTimeline() {
  const events = useDebugStore((state) => state.eventHistory);

  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => 
      new Date(b.datetime).getTime() - new Date(a.datetime).getTime()
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
            <TimelineItem key={`${event.datetime}-${index}`}>
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
                  {new Date(event.datetime).toLocaleTimeString()}
                </Typography>
              </TimelineContent>
            </TimelineItem>
          ))}
        </Timeline>
      </Box>
    </Box>
  );
}
