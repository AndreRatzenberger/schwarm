import { 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Typography,
  Collapse,
  IconButton,
  Box,
  Alert,
  Chip
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import ChatIcon from '@mui/icons-material/Chat';
import BuildIcon from '@mui/icons-material/Build';
import InfoIcon from '@mui/icons-material/Info';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useState } from 'react';
import { useDebugStore } from '../store/debugStore';
import { Event, EventType } from '../types/events';

interface RowProps {
  event: Event;
}

function Row({ event }: RowProps) {
  const [open, setOpen] = useState(false);

  const getEventIcon = (type: EventType) => {
    switch (type) {
      case EventType.START:
        return <PlayArrowIcon fontSize="small" sx={{ color: '#4caf50' }} />;
      case EventType.HANDOFF:
        return <SwapHorizIcon fontSize="small" sx={{ color: '#ff9800' }} />;
      case EventType.MESSAGE_COMPLETION:
      case EventType.POST_MESSAGE_COMPLETION:
        return <ChatIcon fontSize="small" sx={{ color: '#2196f3' }} />;
      case EventType.TOOL_EXECUTION:
      case EventType.POST_TOOL_EXECUTION:
        return <BuildIcon fontSize="small" sx={{ color: '#9c27b0' }} />;
      case EventType.INSTRUCT:
        return <InfoIcon fontSize="small" sx={{ color: '#607d8b' }} />;
      default:
        return null;
    }
  };

  const getEventColor = (type: EventType) => {
    switch (type) {
      case EventType.START:
        return '#4caf50';
      case EventType.HANDOFF:
        return '#ff9800';
      case EventType.MESSAGE_COMPLETION:
      case EventType.POST_MESSAGE_COMPLETION:
        return '#2196f3';
      case EventType.TOOL_EXECUTION:
      case EventType.POST_TOOL_EXECUTION:
        return '#9c27b0';
      case EventType.INSTRUCT:
        return '#607d8b';
      default:
        return '#9e9e9e';
    }
  };

  const renderEventSummary = () => {
    if (!event?.payload) {
      return 'Invalid event data';
    }

    const toolCalls = event.payload.current_message?.tool_calls;
    const isPostEvent = event.type.startsWith('on_post_');

    switch (event.type) {
      case EventType.START:
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <span>Started agent</span>
            <Chip 
              size="small" 
              label={event.payload.current_agent?.name || 'Unknown'}
              sx={{ backgroundColor: 'rgba(76, 175, 80, 0.1)' }}
            />
          </Box>
        );
      
      case EventType.MESSAGE_COMPLETION:
      case EventType.POST_MESSAGE_COMPLETION: {
        const message = event.payload.current_message;
        const sender = message?.sender || message?.role || 'Unknown';
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {isPostEvent && <CheckCircleIcon fontSize="small" sx={{ color: '#4caf50' }} />}
            <Chip 
              size="small" 
              label={sender}
              sx={{ backgroundColor: 'rgba(33, 150, 243, 0.1)' }}
            />
            <span>{message?.content || 'No message content'}</span>
          </Box>
        );
      }
      
      case EventType.TOOL_EXECUTION:
      case EventType.POST_TOOL_EXECUTION:
        if (!toolCalls || toolCalls.length === 0) return 'No tool calls';
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {isPostEvent && <CheckCircleIcon fontSize="small" sx={{ color: '#4caf50' }} />}
            <Chip 
              size="small" 
              label={toolCalls[0].function.name}
              sx={{ backgroundColor: 'rgba(156, 39, 176, 0.1)' }}
            />
            <span>{JSON.stringify(toolCalls[0].function.arguments)}</span>
          </Box>
        );
      
      case EventType.HANDOFF:
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip 
              size="small" 
              label={event.agent_id}
              sx={{ backgroundColor: 'rgba(255, 152, 0, 0.1)' }}
            />
            <SwapHorizIcon fontSize="small" />
            <Chip 
              size="small" 
              label={event.payload.current_agent?.name || 'Unknown'}
              sx={{ backgroundColor: 'rgba(255, 152, 0, 0.1)' }}
            />
          </Box>
        );
      
      case EventType.INSTRUCT:
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <span>{event.payload.instruction_str || 'No instruction'}</span>
          </Box>
        );
      
      default:
        return 'Unknown event type';
    }
  };

  const renderEventDetails = () => {
    if (!event?.payload) {
      return <Alert severity="error">Invalid event payload</Alert>;
    }

    const context = event.payload;
    return (
      <Box sx={{ p: 2 }}>
        {context.current_agent && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Agent Details
            </Typography>
            <Box sx={{ pl: 2 }}>
              <Typography variant="body2">
                <strong>Name:</strong> {context.current_agent.name}
              </Typography>
              <Typography variant="body2">
                <strong>Model:</strong> {context.current_agent.model}
              </Typography>
              {context.current_agent.description && (
                <Typography variant="body2">
                  <strong>Description:</strong> {context.current_agent.description}
                </Typography>
              )}
            </Box>
          </Box>
        )}

        {context.current_message && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Current Message
            </Typography>
            <Box sx={{ pl: 2 }}>
              <Typography variant="body2">
                <strong>Role:</strong> {context.current_message.role}
              </Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                <strong>Content:</strong> {context.current_message.content || 'No content'}
              </Typography>
              {context.current_message.tool_calls && context.current_message.tool_calls.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Tool Calls
                  </Typography>
                  {context.current_message.tool_calls.map((tool, idx) => (
                    <Box key={idx} sx={{ pl: 2, mb: 1 }}>
                      <Typography variant="body2">
                        <strong>Tool:</strong> {tool.function.name}
                      </Typography>
                      <Typography variant="body2" sx={{ 
                        whiteSpace: 'pre-wrap',
                        fontFamily: 'monospace',
                        backgroundColor: 'rgba(0,0,0,0.1)',
                        p: 1,
                        borderRadius: 1
                      }}>
                        {JSON.stringify(tool.function.arguments, null, 2)}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          </Box>
        )}

        {context.message_history.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Message History
            </Typography>
            <Box sx={{ pl: 2 }}>
              <Typography variant="body2">
                Total Messages: {context.message_history.length}
              </Typography>
            </Box>
          </Box>
        )}

        {Object.keys(context.context_variables).length > 0 && (
          <Box>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Context Variables
            </Typography>
            <Box sx={{ 
              pl: 2,
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              backgroundColor: 'rgba(0,0,0,0.1)',
              p: 1,
              borderRadius: 1
            }}>
              {JSON.stringify(context.context_variables, null, 2)}
            </Box>
          </Box>
        )}
      </Box>
    );
  };

  if (!event) {
    return null;
  }

  return (
    <>
      <TableRow 
        sx={{ 
          '&:hover': { 
            backgroundColor: 'action.hover' 
          }
        }}
      >
        <TableCell padding="checkbox">
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell sx={{ whiteSpace: 'nowrap' }}>
          {new Date(event.datetime).toLocaleTimeString()}
        </TableCell>
        <TableCell>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {getEventIcon(event.type)}
            <Chip 
              size="small" 
              label={event.type.replace('on_', '')}
              sx={{ 
                backgroundColor: `${getEventColor(event.type)}20`,
                color: getEventColor(event.type),
                fontWeight: 500
              }}
            />
          </Box>
        </TableCell>
        <TableCell>
          <Chip 
            size="small" 
            label={event.agent_id}
            sx={{ backgroundColor: 'rgba(0,0,0,0.1)' }}
          />
        </TableCell>
        <TableCell sx={{ width: '100%' }}>{renderEventSummary()}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={5}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            {renderEventDetails()}
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export default function EventTable() {
  const events = useDebugStore((state) => state.eventHistory);

  if (!events?.length) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="info">No events to display</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h6" gutterBottom component="div" sx={{ p: 2, pb: 0 }}>
        Event History
      </Typography>
      <TableContainer 
        component={Paper} 
        sx={{ 
          flexGrow: 1,
          '& .MuiTableCell-root': {
            borderBottom: '1px solid rgba(81, 81, 81, 1)'
          }
        }}
      >
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox" />
              <TableCell>Time</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Agent</TableCell>
              <TableCell>Summary</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {events.map((event, index) => (
              <Row key={index} event={event} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
