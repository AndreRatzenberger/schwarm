import { Box, Heading, SimpleGrid, Text } from '@chakra-ui/react';
import { useDebugStore } from '../store/debugStore';

function ResourceBar({ value, max, label }: { value: number; max: number; label: string }) {
  const percentage = (value / max) * 100;
  const color = percentage > 90 ? 'red.500' : percentage > 70 ? 'yellow.500' : 'green.500';

  return (
    <Box mb={6}>
      <Text fontWeight="medium" mb={1}>{label}</Text>
      <Text fontSize="2xl" fontWeight="bold" mb={1}>
        {label === 'Cost' ? `$${value.toFixed(2)}` : value.toLocaleString()}
        <Text as="span" fontSize="sm" color="gray.500" ml={1}>
          of {label === 'Cost' ? `$${max.toFixed(2)}` : max.toLocaleString()}
        </Text>
      </Text>
      <Box
        w="100%"
        h="8px"
        bg="gray.100"
        borderRadius="full"
        overflow="hidden"
        _dark={{ bg: 'gray.700' }}
      >
        <Box
          h="100%"
          w={`${Math.min(percentage, 100)}%`}
          bg={color}
          transition="width 0.3s ease-in-out"
          borderRadius="full"
          {...(percentage > 70 && {
            animation: 'pulse 2s infinite',
            '@keyframes pulse': {
              '0%': { opacity: 1 },
              '50%': { opacity: 0.7 },
              '100%': { opacity: 1 },
            },
          })}
        />
      </Box>
      <Text fontSize="sm" color="gray.500" mt={1}>
        {percentage.toFixed(1)}% utilized
      </Text>
    </Box>
  );
}

export default function BudgetPanel() {
  const { budget } = useDebugStore();

  if (!budget) {
    return (
      <Box>
        <Heading size="md" mb={4}>Resource Usage</Heading>
        <Box p={4} textAlign="center" color="gray.500">
          No budget data available
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      <Heading size="md" mb={4}>Resource Usage</Heading>
      <SimpleGrid columns={[1, null, 2]} gap={6}>
        <ResourceBar
          value={budget.current_spent}
          max={budget.max_spent}
          label="Cost"
        />
        <ResourceBar
          value={budget.current_tokens}
          max={budget.max_tokens}
          label="Tokens"
        />
      </SimpleGrid>
    </Box>
  );
}
