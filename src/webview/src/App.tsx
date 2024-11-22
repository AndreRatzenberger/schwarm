import { ThemeProvider, CssBaseline } from '@mui/material';
import { createTheme } from '@mui/material/styles';
import { useEffect } from 'react';
import Layout from './components/Layout.tsx';
import { wsService } from './services/websocket.ts';

// Create a dark theme by default
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
});

function App() {
  useEffect(() => {
    // Connect to WebSocket when app starts
    const wsUrl = import.meta.env.VITE_WS_URL;
    if (!wsUrl) {
      console.error('WebSocket URL not configured. Please set VITE_WS_URL in .env file.');
      return;
    }
    wsService.connect(wsUrl);

    // Cleanup on unmount
    return () => {
      wsService.disconnect();
    };
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout />
    </ThemeProvider>
  );
}

export default App;
