graph TB
    subgraph WebDebugProvider
        WDP[WebDebugProvider]
        WS[WebSocket Server]
        API[FastAPI Server]
        EH[Event Handler]
        VIZ[Visualizations]
    end

    subgraph Frontend
        UI[Web Dashboard]
        AG[Agent Graph]
        TL[Timeline]
        BV[Budget Viz]
    end

    subgraph Events
        START[Start Event]
        MSG[Message Event]
        TOOL[Tool Event]
        POST[Post Tool Event]
    end

    %% Event Flow
    START --> EH
    MSG --> EH
    TOOL --> EH
    POST --> EH

    %% Provider Internal Flow
    EH --> WDP
    WDP --> WS
    WDP --> API
    
    %% Frontend Communication
    WS --> UI
    API --> UI

    %% Frontend Components
    UI --> AG
    UI --> TL
    UI --> BV

    %% Visualization Types
    VIZ --> |D3.js Graph|AG
    VIZ --> |Timeline View|TL
    VIZ --> |Budget Charts|BV

    %% Styling
    classDef provider fill:#f9f,stroke:#333,stroke-width:2px
    classDef frontend fill:#bbf,stroke:#333,stroke-width:2px
    classDef events fill:#bfb,stroke:#333,stroke-width:2px
    
    class WDP,WS,API,EH,VIZ provider
    class UI,AG,TL,BV frontend
    class START,MSG,TOOL,POST events
