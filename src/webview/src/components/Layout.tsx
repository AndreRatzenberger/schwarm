import { Container, Grid, Paper } from '@mui/material';
import Header from './Header';
import AgentGraph from './AgentGraph';
import EventTimeline from './EventTimeline';
import BudgetPanel from './BudgetPanel';

export default function Layout() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Header />
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Grid container spacing={3}>
          {/* Agent Graph */}
          <Grid item xs={12} md={6}>
            <Paper 
              elevation={2} 
              sx={{ 
                p: 2, 
                height: '400px',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              <AgentGraph />
            </Paper>
          </Grid>

          {/* Event Timeline */}
          <Grid item xs={12} md={6}>
            <Paper 
              elevation={2} 
              sx={{ 
                p: 2, 
                height: '400px',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              <EventTimeline />
            </Paper>
          </Grid>

          {/* Budget Panel */}
          <Grid item xs={12}>
            <Paper 
              elevation={2} 
              sx={{ 
                p: 2, 
                height: '200px',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              <BudgetPanel />
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </div>
  );
}
