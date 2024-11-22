sequenceDiagram
    participant A as Agent
    participant WDP as WebDebugProvider
    participant WS as WebSocket
    participant UI as Web UI
    participant VIZ as Visualizations

    Note over WDP: Provider Initialization
    WDP->>WDP: Initialize FastAPI
    WDP->>WDP: Setup WebSocket
    WDP->>WDP: Start Server

    Note over UI: Client Connection
    UI->>WS: Connect
    WS->>UI: Send Initial State
    
    Note over A,VIZ: Real-time Updates
    A->>WDP: Event (START)
    WDP->>WDP: Process Event
    WDP->>WS: Broadcast Update
    WS->>UI: Send Update
    UI->>VIZ: Update Agent Graph
    UI->>VIZ: Update Timeline
    
    A->>WDP: Event (MESSAGE)
    WDP->>WDP: Process Event
    WDP->>WS: Broadcast Update
    WS->>UI: Send Update
    UI->>VIZ: Update Visualizations
    
    A->>WDP: Event (TOOL)
    WDP->>WDP: Process Event
    WDP->>WS: Broadcast Update
    WS->>UI: Send Update
    UI->>VIZ: Update Tool Execution
    
    Note over UI: Replay Feature
    UI->>UI: Store Event History
    UI->>VIZ: Replay Events
    
    Note over UI: Budget Updates
    WDP->>WDP: Check Budget
    WDP->>WS: Send Budget Data
    WS->>UI: Update Budget
    UI->>VIZ: Update Budget Charts
