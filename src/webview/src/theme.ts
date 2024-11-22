import { createSystem, defineConfig } from '@chakra-ui/react';

const config = defineConfig({
    cssVarsRoot: ':where(:root, :host)',
    theme: {
        tokens: {
            colors: {
                bg: { value: '#F7FAFC' },
                surface: { value: '#FFFFFF' },
                primary: { value: '#4299E1' },
                secondary: { value: '#A0AEC0' },
                success: { value: '#48BB78' },
                warning: { value: '#ECC94B' },
                error: { value: '#F56565' },
                text: { value: '#2D3748' },
                muted: { value: '#718096' },
                border: { value: '#E2E8F0' }
            },
            sizes: {
                container: { value: '80rem' },
                header: { value: '4rem' },
                sidebar: { value: '16rem' }
            }
        }
    }
});

export const system = createSystem(config);
