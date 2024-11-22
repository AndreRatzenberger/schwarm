import { create } from 'zustand';
import { Agent, Message, BudgetData, Event } from '../types/events';

interface DebugStore {
    // Agents
    agents: Map<string, Agent>;
    activeAgent: string | null;
    addAgent: (agent: Agent) => void;
    setActiveAgent: (agentName: string) => void;

    // Messages
    messages: Message[];
    addMessage: (message: Message) => void;

    // Events
    eventHistory: Event[];
    addEvent: (event: Event) => void;
    clearEvents: () => void;

    // Budget
    budget: BudgetData | null;
    updateBudget: (budget: BudgetData) => void;

    // Connections
    connections: Array<{ from: string; to: string }>;
    addConnection: (from: string, to: string) => void;
}

export const useDebugStore = create<DebugStore>((set) => ({
    // Agents
    agents: new Map(),
    activeAgent: null,
    addAgent: (agent) =>
        set((state) => ({
            agents: new Map(state.agents).set(agent.name, agent),
            activeAgent: state.activeAgent || agent.name,
        })),
    setActiveAgent: (agentName) => set({ activeAgent: agentName }),

    // Messages
    messages: [],
    addMessage: (message) =>
        set((state) => ({ messages: [...state.messages, message] })),

    // Events
    eventHistory: [],
    addEvent: (event) =>
        set((state) => ({ eventHistory: [...state.eventHistory, event] })),
    clearEvents: () => set({ eventHistory: [] }),

    // Budget
    budget: null,
    updateBudget: (budget) => set({ budget }),

    // Connections
    connections: [],
    addConnection: (from, to) =>
        set((state) => ({
            connections: [...state.connections, { from, to }],
        })),
}));
