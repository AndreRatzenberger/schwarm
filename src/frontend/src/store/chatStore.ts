import { create } from 'zustand';
import { useSettingsStore } from './settingsStore';

interface ChatStore {
    isChatRequested: boolean;
    setIsChatRequested: (value: boolean) => void;
    chatInput: string;
    setChatInput: (value: string) => void;
    submitChat: (input: string) => Promise<void>;
}

export const useChatStore = create<ChatStore>((set) => ({
    isChatRequested: false,
    setIsChatRequested: (value) => set({ isChatRequested: value }),
    chatInput: '',
    setChatInput: (value) => set({ chatInput: value }),
    submitChat: async (input) => {
        try {
            const endpointUrl = useSettingsStore.getState().endpointUrl;
            const url = new URL(`${endpointUrl}/chat`);
            url.searchParams.append('user_input', input);

            const response = await fetch(url.toString(), {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to submit chat');
            }

            set({ chatInput: '', isChatRequested: false });
        } catch (error) {
            console.error('Error submitting chat:', error);
        }
    },
}));
