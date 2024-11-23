import { Box, Container, Tab, Tabs } from '@mui/material';
import { useState, SyntheticEvent } from 'react';
import Header from './Header';
import AgentGraph from './AgentGraph';
import EventTable from './EventTable';


interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      style={{ height: 'calc(100vh - 112px)', overflow: 'auto' }}
      {...other}
    >
      {value === index && (
        <Box sx={{ height: '100%' }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function Layout() {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (_event: SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      backgroundColor: 'background.default',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <Header />
      
      <Box sx={{ 
        borderBottom: 1, 
        borderColor: 'divider',
        backgroundColor: 'background.paper' 
      }}>
        <Container maxWidth={false}>
          <Tabs 
            value={currentTab} 
            onChange={handleTabChange} 
            aria-label="debug interface tabs"
          >
            <Tab label="Events" id="tab-0" aria-controls="tabpanel-0" />
            <Tab label="Agent Graph" id="tab-1" aria-controls="tabpanel-1" />
            <Tab label="Budget" id="tab-2" aria-controls="tabpanel-2" />
          </Tabs>
        </Container>
      </Box>

      <Container 
        maxWidth={false} 
        sx={{ 
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          height: 'calc(100vh - 112px)'  // Subtract header height and tabs height
        }}
      >
        <TabPanel value={currentTab} index={0}>
          <EventTable />
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          <AgentGraph />
        </TabPanel>

      </Container>
    </Box>
  );
}
