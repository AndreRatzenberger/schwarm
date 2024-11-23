import { useEffect, useState } from 'react';
import { Event } from '../types/events';

const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return {
        date: date.toLocaleDateString(),
        time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };
};

const JsonViewer = ({ data }: { data: unknown }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const preview = JSON.stringify(data).slice(0, 50) + (JSON.stringify(data).length > 50 ? '...' : '');
    
    return (
        <div className="json-viewer" style={{ cursor: 'pointer' }}>
            {isExpanded ? (
                <pre 
                    onClick={() => setIsExpanded(false)}
                    style={{
                        color: '#333',
                        background: '#f8f9fa',
                        border: '1px solid #e9ecef',
                        margin: 0,
                        padding: '8px',
                        borderRadius: '4px',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-all'
                    }}
                >
                    {JSON.stringify(data, null, 2)}
                </pre>
            ) : (
                <div 
                    onClick={() => setIsExpanded(true)}
                    style={{ 
                        padding: '8px',
                        background: '#f8f9fa',
                        borderRadius: '4px',
                        fontSize: '0.9em',
                        color: '#333',
                        border: '1px solid #e9ecef'
                    }}
                >
                    {preview}
                </div>
            )}
        </div>
    );
};

const StatusIndicator = ({ status }: { status: string }) => {
    return (
        <div className="status-indicator">
            <span className={`status-${status}`}>●</span>
            <span style={{ marginLeft: '8px', color: '#333' }}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
        </div>
    );
};

export const EventTable = () => {
    const [events, setEvents] = useState<Event<unknown>[]>([]);
    const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8123');

        ws.onopen = () => {
            setWsStatus('connected');
            setError(null);
            console.log('Connected to WebSocket');
        };

        ws.onclose = () => {
            setWsStatus('disconnected');
            setError('Connection closed. Waiting for reconnection...');
            console.log('Disconnected from WebSocket');
        };

        ws.onerror = (event) => {
            setError('WebSocket error occurred');
            console.error('WebSocket error:', event);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data) as Event<unknown>;
                setEvents(prev => [data, ...prev]);
            } catch (err) {
                console.error('Error parsing message:', err);
                setError('Error parsing incoming message');
            }
        };

        return () => {
            ws.close();
        };
    }, []);

    return (
        <div style={{
            maxWidth: '1200px',
            margin: '0 auto',
            padding: '20px'
        }}>
            <h1 style={{
                color: '#333',
                marginBottom: '24px',
                textAlign: 'center'
            }}>
                Schwarm Event Monitor
            </h1>
            
            <div className="event-table-container">
                <div className="status-bar" style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    background: '#f8f9fa',
                    padding: '12px 16px',
                    borderRadius: '6px',
                    marginBottom: '16px'
                }}>
                    <div className="status-info">
                        <StatusIndicator status={wsStatus} />
                    </div>
                    <div style={{ fontSize: '0.9em', color: '#666' }}>
                        {events.length} events received
                    </div>
                </div>
                
                {error && (
                    <div style={{ 
                        padding: '12px',
                        marginBottom: '16px',
                        background: '#fff3f3',
                        border: '1px solid #ffcdd2',
                        borderRadius: '4px',
                        color: '#d32f2f'
                    }}>
                        {error}
                    </div>
                )}

                <div style={{ 
                    background: 'white',
                    borderRadius: '8px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    overflow: 'hidden'
                }}>
                    <table className="event-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                            <tr>
                                <th style={{ 
                                    padding: '16px', 
                                    background: '#f8f9fa', 
                                    color: '#333',
                                    borderBottom: '2px solid #dee2e6'
                                }}>Time</th>
                                <th style={{ 
                                    padding: '16px', 
                                    background: '#f8f9fa', 
                                    color: '#333',
                                    borderBottom: '2px solid #dee2e6'
                                }}>Type</th>
                                <th style={{ 
                                    padding: '16px', 
                                    background: '#f8f9fa', 
                                    color: '#333',
                                    borderBottom: '2px solid #dee2e6'
                                }}>Agent ID</th>
                                <th style={{ 
                                    padding: '16px', 
                                    background: '#f8f9fa', 
                                    color: '#333',
                                    borderBottom: '2px solid #dee2e6'
                                }}>Payload</th>
                            </tr>
                        </thead>
                        <tbody>
                            {events.length === 0 ? (
                                <tr>
                                    <td colSpan={4} style={{ 
                                        textAlign: 'center',
                                        padding: '40px',
                                        color: '#666',
                                        background: '#fafafa'
                                    }}>
                                        <div style={{ fontSize: '1.1em', marginBottom: '8px' }}>
                                            No events received yet
                                        </div>
                                        <div style={{ fontSize: '0.9em', color: '#888' }}>
                                            Waiting for incoming events...
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                events.map((event, index) => {
                                    const { date, time } = formatDateTime(event.datetime);
                                    return (
                                        <tr key={index} style={{ borderBottom: '1px solid #dee2e6' }}>
                                            <td style={{ padding: '16px', color: '#333' }}>
                                                <div style={{ fontSize: '0.9em', color: '#666' }}>{date}</div>
                                                <div style={{ fontWeight: '500' }}>{time}</div>
                                            </td>
                                            <td style={{ padding: '16px', color: '#333' }}>
                                                <span style={{
                                                    padding: '4px 8px',
                                                    borderRadius: '12px',
                                                    fontSize: '0.9em',
                                                    background: '#e3f2fd',
                                                    color: '#1976d2'
                                                }}>
                                                    {event.type}
                                                </span>
                                            </td>
                                            <td style={{ 
                                                padding: '16px', 
                                                fontFamily: 'monospace',
                                                color: '#333'
                                            }}>
                                                {event.agent_id}
                                            </td>
                                            <td style={{ padding: '16px' }}>
                                                <JsonViewer data={event.payload} />
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
