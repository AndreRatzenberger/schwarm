import { ThemeProvider, CssBaseline } from '@mui/material';
import { createTheme } from '@mui/material/styles';
import { useEffect } from 'react';
import Layout from './components/Layout.tsx';
import { useDebugStore } from './store/debugStore';

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
  const setConnected = useDebugStore(state => state.setConnected);

  useEffect(() => {
    // Mark as connected since we're using direct HTTP now
    setConnected(true);

    // Cleanup on unmount
    return () => {
      setConnected(false);
    };
  }, [setConnected]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Layout />
    </ThemeProvider>
  );
}

export default App;
