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
  Alert
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { useState } from 'react';
import { useDebugStore } from '../store/debugStore';
import { Event, EventType } from '../types/events';

interface RowProps {
  event: Event;
}

function Row({ event }: RowProps) {
  const [open, setOpen] = useState(false);

  const renderEventSummary = () => {
    if (!event?.payload) {
      return 'Invalid event data';
    }

    const toolCalls = event.payload.current_message?.tool_calls;

    switch (event.type) {
      case EventType.START:
        return `Started agent ${event.payload.current_agent?.name || 'Unknown'}`;
      
      case EventType.MESSAGE_COMPLETION:
      case EventType.POST_MESSAGE_COMPLETION:
        return event.payload.current_message?.content || 'No message content';
      
      case EventType.TOOL_EXECUTION:
      case EventType.POST_TOOL_EXECUTION:
        if (!toolCalls || toolCalls.length === 0) return 'No tool calls';
        return `Executing tool: ${toolCalls[0].function.name}`;
      
      case EventType.HANDOFF:
        return `Handoff from ${event.agent_id} to ${event.payload.current_agent?.name || 'Unknown'}`;
      
      case EventType.INSTRUCT:
        return event.payload.instruction_str || 'No instruction';
      
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
          <div>
            <Typography variant="subtitle2">Agent</Typography>
            <div>Name: {context.current_agent.name}</div>
            <div>Model: {context.current_agent.model}</div>
            {context.current_agent.description && (
              <div>Description: {context.current_agent.description}</div>
            )}
          </div>
        )}

        {context.current_message && (
          <div style={{ marginTop: '1rem' }}>
            <Typography variant="subtitle2">Current Message</Typography>
            <div>Role: {context.current_message.role}</div>
            <div>Content: {context.current_message.content || 'No content'}</div>
            {context.current_message.tool_calls && context.current_message.tool_calls.length > 0 && (
              <div>
                <Typography variant="subtitle2">Tool Calls</Typography>
                {context.current_message.tool_calls.map((tool, idx) => (
                  <div key={idx}>
                    <div>Tool: {tool.function.name}</div>
                    <div>Args: {JSON.stringify(tool.function.arguments)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {context.message_history.length > 0 && (
          <div style={{ marginTop: '1rem' }}>
            <Typography variant="subtitle2">Message History</Typography>
            <div>Messages: {context.message_history.length}</div>
          </div>
        )}

        {Object.keys(context.context_variables).length > 0 && (
          <div style={{ marginTop: '1rem' }}>
            <Typography variant="subtitle2">Context Variables</Typography>
            <pre>{JSON.stringify(context.context_variables, null, 2)}</pre>
          </div>
        )}
      </Box>
    );
  };

  if (!event) {
    return null;
  }

  return (
    <>
      <TableRow>
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>{new Date(event.datetime).toLocaleTimeString()}</TableCell>
        <TableCell>{event.type}</TableCell>
        <TableCell>{event.agent_id}</TableCell>
        <TableCell>{renderEventSummary()}</TableCell>
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
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h6" gutterBottom>
        Event History
      </Typography>
      <TableContainer component={Paper} sx={{ flexGrow: 1 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell style={{ width: '40px' }} />
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
    </div>
  );
}
