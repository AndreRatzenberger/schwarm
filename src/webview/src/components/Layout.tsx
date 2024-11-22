import { Box, Container, Grid, GridItem, useColorModeValue } from '@chakra-ui/react';
import Header from './Header';
import AgentGraph from './AgentGraph';
import EventTimeline from './EventTimeline';
import BudgetPanel from './BudgetPanel';

export default function Layout() {
  const bg = useColorModeValue('gray.50', 'gray.900');
  const panelBg = useColorModeValue('white', 'gray.800');

  return (
    <Box minH="100vh" bg={bg}>
      <Header />
      <Container maxW="container.xl" py={6}>
        <Grid
          templateColumns="repeat(2, 1fr)"
          gap={6}
          templateAreas={`
            "graph timeline"
            "budget budget"
          `}
        >
          <GridItem
            area="graph"
            bg={panelBg}
            p={6}
            rounded="lg"
            shadow="sm"
            minH="400px"
          >
            <AgentGraph />
          </GridItem>

          <GridItem
            area="timeline"
            bg={panelBg}
            p={6}
            rounded="lg"
            shadow="sm"
            minH="400px"
          >
            <EventTimeline />
          </GridItem>

          <GridItem
            area="budget"
            bg={panelBg}
            p={6}
            rounded="lg"
            shadow="sm"
            minH="200px"
          >
            <BudgetPanel />
          </GridItem>
        </Grid>
      </Container>
    </Box>
  );
}
