import React, { useEffect, useRef, useState } from 'react';
import { MessageSquare, Radio, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useStreamStore } from '../store/streamStore';
import { useSettingsStore } from '../store/settingsStore';
import { usePauseStore } from '../store/pauseStore';
import { useChatStore } from '../store/chatStore';
import { Card } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Alert, AlertDescription } from './ui/alert';
import { Input } from './ui/input';
import { Button } from './ui/button';

interface StreamMessage {
    id: string;
    content: string;
    timestamp: string;
    agent: string;
}

interface WebSocketMessage {
    type: 'default' | 'tool' | 'close';
    content: string | null;
    agent?: string;
}

interface CodeProps {
    inline?: boolean;
    children?: React.ReactNode;
}

const colorPalette = [
    { bg: 'bg-blue-100', text: 'text-blue-800', color: '#3B82F6' },
    { bg: 'bg-purple-100', text: 'text-purple-800', color: '#8B5CF6' },
    { bg: 'bg-green-100', text: 'text-green-800', color: '#10B981' },
    { bg: 'bg-orange-100', text: 'text-orange-800', color: '#F97316' },
    { bg: 'bg-pink-100', text: 'text-pink-800', color: '#EC4899' },
    { bg: 'bg-cyan-100', text: 'text-cyan-800', color: '#06B6D4' },
    { bg: 'bg-yellow-100', text: 'text-yellow-800', color: '#F59E0B' },
    { bg: 'bg-red-100', text: 'text-red-800', color: '#EF4444' },
    { bg: 'bg-indigo-100', text: 'text-indigo-800', color: '#6366F1' }
];

export default function DashboardMessageFlow() {
    const messages = useStreamStore(state => state.messages);
    const addMessage = useStreamStore(state => state.addMessage);
    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const [agentColors] = useState(new Map<string, number>());
    const { endpointUrl } = useSettingsStore();
    const { isPaused } = usePauseStore();
    const [error, setError] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const currentMessageRef = useRef('');
    const currentAgentRef = useRef('System');
    const { isChatRequested, chatInput, setChatInput, submitChat } = useChatStore();

    // Get color for agent, creating a new one if needed
    const getAgentColor = (agent: string) => {
        if (!agentColors.has(agent)) {
            agentColors.set(agent, agentColors.size % colorPalette.length);
        }
        return colorPalette[agentColors.get(agent)!];
    };

    const handleSubmitChat = async (e: React.FormEvent) => {
        e.preventDefault();
        if (chatInput.trim()) {
            await submitChat(chatInput.trim());
        }
    };

    const connect = () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        const ws = new WebSocket(`ws://${endpointUrl.replace(/^https?:\/\//, '')}/ws`);
        wsRef.current = ws;

        ws.onopen = () => {
            setIsConnected(true);
            setError(null);
            currentMessageRef.current = '';
        };

        ws.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);

                if (message.type === 'close') {
                    if (currentMessageRef.current) {
                        addMessage(currentMessageRef.current, currentAgentRef.current);
                        currentMessageRef.current = '';
                    }
                    ws.close();
                    return;
                }

                if (message.agent) {
                    currentAgentRef.current = message.agent;
                }

                if (message.content) {
                    currentMessageRef.current += message.content;
                }
            } catch (e) {
                console.error('Error parsing message:', e);
            }
        };

        ws.onerror = (event) => {
            setError('WebSocket error occurred');
            console.error('WebSocket error:', event);
        };

        ws.onclose = () => {
            setIsConnected(false);
            if (!isPaused) {
                setTimeout(connect, 2000);
            }
        };
    };

    const disconnect = () => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    };

    useEffect(() => {
        if (!isPaused) {
            connect();
        } else {
            disconnect();
        }
        return () => disconnect();
    }, [endpointUrl, isPaused]);

    useEffect(() => {
        if (scrollAreaRef.current) {
            scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
        }
    }, [messages, currentMessageRef.current]);

    return (
        <Card className="bg-white rounded-lg shadow-sm">
            <div className="p-4">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">Message Flow</h2>
                    {isConnected && (
                        <div className="flex items-center space-x-2 text-sm text-green-600">
                            <Radio className="w-3 h-3 animate-pulse" />
                            <span>Live</span>
                        </div>
                    )}
                </div>
                {error && (
                    <Alert variant="destructive" className="mb-4">
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}
                {isChatRequested && (
                    <form onSubmit={handleSubmitChat} className="mb-4 flex space-x-2">
                        <Input
                            type="text"
                            placeholder="Type your message..."
                            value={chatInput}
                            onChange={(e) => setChatInput(e.target.value)}
                            className="flex-1"
                        />
                        <Button type="submit" size="sm">
                            <Send className="h-4 w-4" />
                        </Button>
                    </form>
                )}
                <ScrollArea className="h-[600px] w-full rounded-md border p-4" ref={scrollAreaRef}>
                    <div className="space-y-4">
                        {messages.map((message: StreamMessage) => {
                            const colors = getAgentColor(message.agent);
                            return (
                                <div key={message.id} className="flex flex-col items-start">
                                    <div className={`max-w-[70%] rounded-lg p-3 ${colors.bg} ${colors.text} ml-4 mr-4`}>
                                        <div className="flex items-center space-x-2 mb-1">
                                            <MessageSquare className="h-4 w-4" />
                                            <span className="font-semibold text-sm">
                                                {message.agent}
                                            </span>
                                        </div>
                                        <div className="prose prose-sm max-w-none">
                                            <ReactMarkdown
                                                className="break-words"
                                                components={{
                                                    h1: ({ ...props }) => <h1 className="text-2xl font-bold mt-4 mb-2" {...props} />,
                                                    h2: ({ ...props }) => <h2 className="text-xl font-bold mt-3 mb-2" {...props} />,
                                                    h3: ({ ...props }) => <h3 className="text-lg font-bold mt-2 mb-1" {...props} />,
                                                    p: ({ ...props }) => <p className="mb-2" {...props} />,
                                                    ul: ({ ...props }) => <ul className="list-disc pl-4 mb-2" {...props} />,
                                                    ol: ({ ...props }) => <ol className="list-decimal pl-4 mb-2" {...props} />,
                                                    li: ({ ...props }) => <li className="mb-1" {...props} />,
                                                    code: ({ inline, children, ...props }: CodeProps) =>
                                                        inline ? (
                                                            <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm" {...props}>
                                                                {children}
                                                            </code>
                                                        ) : (
                                                            <code className="block bg-gray-100 dark:bg-gray-800 p-2 rounded text-sm overflow-x-auto" {...props}>
                                                                {children}
                                                            </code>
                                                        ),
                                                    pre: ({ ...props }) => (
                                                        <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg overflow-x-auto mb-4" {...props} />
                                                    ),
                                                    blockquote: ({ ...props }) => (
                                                        <blockquote className="border-l-4 border-gray-200 dark:border-gray-700 pl-4 italic mb-4" {...props} />
                                                    ),
                                                }}
                                            >
                                                {message.content}
                                            </ReactMarkdown>
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            {new Date(message.timestamp).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                            );
                        })}
                        {currentMessageRef.current && (
                            <div className="flex flex-col items-start">
                                <div className={`max-w-[70%] rounded-lg p-3 ${getAgentColor(currentAgentRef.current).bg} ${getAgentColor(currentAgentRef.current).text} ml-4 mr-4`}>
                                    <div className="flex items-center space-x-2 mb-1">
                                        <MessageSquare className="h-4 w-4" />
                                        <span className="font-semibold text-sm">
                                            {currentAgentRef.current}
                                        </span>
                                    </div>
                                    <div className="prose prose-sm max-w-none">
                                        <ReactMarkdown
                                            className="break-words"
                                            components={{
                                                h1: ({ ...props }) => <h1 className="text-2xl font-bold mt-4 mb-2" {...props} />,
                                                h2: ({ ...props }) => <h2 className="text-xl font-bold mt-3 mb-2" {...props} />,
                                                h3: ({ ...props }) => <h3 className="text-lg font-bold mt-2 mb-1" {...props} />,
                                                p: ({ ...props }) => <p className="mb-2" {...props} />,
                                                ul: ({ ...props }) => <ul className="list-disc pl-4 mb-2" {...props} />,
                                                ol: ({ ...props }) => <ol className="list-decimal pl-4 mb-2" {...props} />,
                                                li: ({ ...props }) => <li className="mb-1" {...props} />,
                                                code: ({ inline, children, ...props }: CodeProps) =>
                                                    inline ? (
                                                        <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm" {...props}>
                                                            {children}
                                                        </code>
                                                    ) : (
                                                        <code className="block bg-gray-100 dark:bg-gray-800 p-2 rounded text-sm overflow-x-auto" {...props}>
                                                            {children}
                                                        </code>
                                                    ),
                                                pre: ({ ...props }) => (
                                                    <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg overflow-x-auto mb-4" {...props} />
                                                ),
                                                blockquote: ({ ...props }) => (
                                                    <blockquote className="border-l-4 border-gray-200 dark:border-gray-700 pl-4 italic mb-4" {...props} />
                                                ),
                                            }}
                                        >
                                            {currentMessageRef.current}
                                        </ReactMarkdown>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </ScrollArea>

            </div>
        </Card>
    );
}
