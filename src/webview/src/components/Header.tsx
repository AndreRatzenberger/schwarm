import { Box, Flex, Heading } from '@chakra-ui/react';

export default function Header() {
  return (
    <Box 
      px={6} 
      py={4} 
      borderBottomWidth="1px" 
      borderBottomColor="gray.200"
      bg="white"
    >
      <Flex align="center" justify="space-between">
        <Heading size="md">Schwarm Debug Interface</Heading>
      </Flex>
    </Box>
  );
}
