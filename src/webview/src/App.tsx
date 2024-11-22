import { ChakraProvider } from '@chakra-ui/react';
import { useEffect } from 'react';
import Layout from './components/Layout.tsx';
import { wsService } from './services/websocket.ts';
import { system } from './theme.ts';

function App() {
  useEffect(() => {
    // Connect to WebSocket when app starts
    wsService.connect('ws://localhost:8000/ws');

    // Cleanup on unmount
    return () => {
      wsService.disconnect();
    };
  }, []);

  return (
    <ChakraProvider value={system}>
      <Layout />
    </ChakraProvider>
  );
}

export default App;
