import { Box, Flex, Heading, Spacer, Button, useColorMode } from '@chakra-ui/react';
import { MoonIcon, SunIcon } from '@chakra-ui/icons';

export default function Header() {
  const { colorMode, toggleColorMode } = useColorMode();

  return (
    <Box px={6} py={4} borderBottom="1px" borderColor="gray.200">
      <Flex alignItems="center">
        <Heading size="md">Schwarm Debug Interface</Heading>
        <Spacer />
        <Button onClick={toggleColorMode} size="sm" variant="ghost">
          {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
        </Button>
      </Flex>
    </Box>
  );
}
