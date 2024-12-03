import { create } from 'zustand'

interface StreamMessage {
    id: string;
    content: string;
    timestamp: string;
}

interface StreamStore {
    messages: StreamMessage[];
    addMessage: (content: string) => void;
    clearMessages: () => void;
}

export const useStreamStore = create<StreamStore>((set) => ({
    messages: [],
    addMessage: (content: string) => set((state) => ({
        messages: [...state.messages, {
            id: crypto.randomUUID(),
            content,
            timestamp: new Date().toISOString()
        }]
    })),
    clearMessages: () => set({ messages: [] })
}))
