import { Box, Container, Grid } from '@chakra-ui/react';
import Header from './Header.tsx';
import AgentGraph from './AgentGraph.tsx';
import EventTimeline from './EventTimeline.tsx';
import BudgetPanel from './BudgetPanel.tsx';

export default function Layout() {
  return (
    <Box minH="100vh" bg="bg">
      <Header />
      <Container maxW="container" py={6}>
        <Grid
          templateColumns="repeat(2, 1fr)"
          gap={6}
          templateAreas={`
            "graph timeline"
            "budget budget"
          `}
        >
          <Box
            gridArea="graph"
            bg="surface"
            p={6}
            borderRadius="md"
            boxShadow="sm"
            minH="400px"
          >
            <AgentGraph />
          </Box>

          <Box
            gridArea="timeline"
            bg="surface"
            p={6}
            borderRadius="md"
            boxShadow="sm"
            minH="400px"
          >
            <EventTimeline />
          </Box>

          <Box
            gridArea="budget"
            bg="surface"
            p={6}
            borderRadius="md"
            boxShadow="sm"
            minH="200px"
          >
            <BudgetPanel />
          </Box>
        </Grid>
      </Container>
    </Box>
  );
}
