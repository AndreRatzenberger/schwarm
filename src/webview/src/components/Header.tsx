import { AppBar, Toolbar, Typography, Box, Stack } from '@mui/material';
import { Terminal, FiberManualRecord } from '@mui/icons-material';
import { useDebugStore } from '../store/debugStore';

export default function Header() {
  const isConnected = useDebugStore((state) => state.isConnected);

  return (
    <AppBar position="static" color="transparent" elevation={1}>
      <Toolbar>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Terminal sx={{ fontSize: 24 }} />
          <Typography variant="h6">
            Schwarm Debug Interface
          </Typography>
        </Stack>

        <Box sx={{ flexGrow: 1 }} />

        <Stack direction="row" alignItems="center" spacing={1}>
          <FiberManualRecord 
            sx={{ 
              fontSize: 12,
              color: isConnected ? '#4caf50' : '#f44336'
            }} 
          />
          <Typography variant="body2" color="text.secondary">
            {isConnected ? 'Connected' : 'Disconnected'}
          </Typography>
        </Stack>
      </Toolbar>
    </AppBar>
  );
}
