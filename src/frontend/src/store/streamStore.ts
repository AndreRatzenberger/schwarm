import { create } from 'zustand'

interface StreamMessage {
    id: string;
    content: string;
    timestamp: string;
    agent: string;
}

interface StreamStore {
    messages: StreamMessage[];
    addMessage: (content: string, agent: string) => void;
    clearMessages: () => void;
}

export const useStreamStore = create<StreamStore>((set) => ({
    messages: [],
    addMessage: (content: string, agent: string) => set((state) => ({
        messages: [...state.messages, {
            id: crypto.randomUUID(),
            content,
            agent,
            timestamp: new Date().toISOString()
        }]
    })),
    clearMessages: () => set({ messages: [] })
}))
