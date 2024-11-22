import { Box, Typography, LinearProgress, Stack, Paper } from '@mui/material';
import { AttachMoney, Token } from '@mui/icons-material';
import { useDebugStore } from '../store/debugStore';

export default function BudgetPanel() {
  const budget = useDebugStore((state) => state.budget);

  if (!budget) {
    return (
      <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography color="text.secondary">
          No budget data available
        </Typography>
      </Box>
    );
  }

  const spentPercentage = (budget.current_spent / budget.max_spent) * 100;
  const tokenPercentage = (budget.current_tokens / budget.max_tokens) * 100;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="h6" gutterBottom>
        Resource Usage
      </Typography>

      <Stack spacing={3} sx={{ flex: 1 }}>
        {/* Cost Usage */}
        <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
          <Stack spacing={2}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <AttachMoney color="primary" />
              <Typography variant="subtitle1">
                Cost Usage
              </Typography>
            </Stack>
            <Box>
              <Stack direction="row" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">
                  ${budget.current_spent.toFixed(2)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  ${budget.max_spent.toFixed(2)}
                </Typography>
              </Stack>
              <LinearProgress 
                variant="determinate" 
                value={Math.min(spentPercentage, 100)}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'rgba(144, 202, 249, 0.2)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: spentPercentage > 90 ? 'error.main' : 'primary.main',
                  },
                }}
              />
            </Box>
          </Stack>
        </Paper>

        {/* Token Usage */}
        <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
          <Stack spacing={2}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <Token color="primary" />
              <Typography variant="subtitle1">
                Token Usage
              </Typography>
            </Stack>
            <Box>
              <Stack direction="row" justifyContent="space-between" mb={1}>
                <Typography variant="body2" color="text.secondary">
                  {budget.current_tokens.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {budget.max_tokens.toLocaleString()}
                </Typography>
              </Stack>
              <LinearProgress 
                variant="determinate" 
                value={Math.min(tokenPercentage, 100)}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'rgba(144, 202, 249, 0.2)',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: tokenPercentage > 90 ? 'error.main' : 'primary.main',
                  },
                }}
              />
            </Box>
          </Stack>
        </Paper>
      </Stack>
    </Box>
  );
}
