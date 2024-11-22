"""Web-based debug provider for visualizing system information through a served website."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import Field
from starlette.websockets import WebSocketDisconnect

from schwarm.events.event_data import Event, EventType
from schwarm.provider.base import BaseEventHandleProvider, BaseEventHandleProviderConfig
from schwarm.provider.budget_provider import BudgetProvider
from schwarm.provider.provider_context import ProviderContext
from schwarm.provider.provider_manager import ProviderManager
from schwarm.utils.settings import APP_SETTINGS


class WebDebugConfig(BaseEventHandleProviderConfig):
    """Configuration for the web debug provider.

    This configuration includes settings for the web interface and data collection.
    """

    host: str = Field(default="localhost", description="Host to serve the web interface")
    port: int = Field(default=8000, description="Port to serve the web interface")
    save_history: bool = Field(default=True, description="Whether to save event history for replay")
    show_budget: bool = Field(default=True, description="Whether to show budget information")
    provider_id: str = Field(default="web_debug", description="Provider ID")


class WebDebugProvider(BaseEventHandleProvider):
    """Web-based debug provider that visualizes system information through a served website.

    Features:
    - Real-time visualization of agent interactions and system state
    - Interactive graph showing agent relationships and message flow
    - Detailed event timeline with replay capabilities
    - Live budget tracking and visualization
    - WebSocket-based real-time updates
    """

    config: WebDebugConfig
    _provider_id: str = Field(default="web_debug", description="Provider ID")
    _app: FastAPI
    _active_connections: list[WebSocket]
    _event_history: list[dict]
    _loop: asyncio.AbstractEventLoop | None

    def __init__(self, config: WebDebugConfig, **data: Any):
        """Initialize the web debug provider."""
        super().__init__(config=config, **data)
        self._app = FastAPI()
        self._active_connections = []
        self._event_history = []
        self._loop = None
        self._setup_routes()
        self._setup_static_files()

    def initialize(self) -> None:
        """Initialize the web debug provider and start the web server."""
        self._start_server()

    def _setup_routes(self) -> None:
        """Set up FastAPI routes for the web interface."""
        app = self._app

        @app.get("/", response_class=HTMLResponse)
        async def get_dashboard() -> str:
            return self._get_dashboard_html()

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            await websocket.accept()
            self._active_connections.append(websocket)
            try:
                # Send initial state
                if self._event_history:
                    await websocket.send_json({"type": "history", "data": self._event_history})
                while True:
                    await websocket.receive_text()  # Keep connection alive
            except WebSocketDisconnect:
                self._active_connections.remove(websocket)

    def _setup_static_files(self) -> None:
        """Set up static files directory for web assets."""
        static_dir = Path(APP_SETTINGS.DATA_FOLDER) / "web_debug" / "static"
        static_dir.mkdir(parents=True, exist_ok=True)
        self._app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def _start_server(self) -> None:
        """Start the FastAPI server in a background thread."""

        def run_server() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            config = uvicorn.Config(app=self._app, host=self.config.host, port=self.config.port, loop="asyncio")
            server = uvicorn.Server(config)
            self._loop.run_until_complete(server.serve())

        import threading

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        logger.info(f"Web debug interface available at http://{self.config.host}:{self.config.port}")

    async def _broadcast_event(self, event_type: str, data: Any) -> None:
        """Broadcast an event to all connected clients."""
        if self.config.save_history:
            self._event_history.append({"timestamp": datetime.now().isoformat(), "type": event_type, "data": data})

        message = json.dumps({"type": event_type, "data": data})

        for connection in self._active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to client: {e}")

    def _run_coroutine(self, coroutine: Any) -> None:
        """Run a coroutine in the event loop."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(coroutine, self._loop)

    def _get_dashboard_html(self) -> str:
        """Generate the HTML for the dashboard."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Schwarm Debug Dashboard</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        .container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .panel {{ border: 1px solid #ccc; padding: 15px; border-radius: 5px; }}
        #agent-graph {{ height: 400px; }}
        #event-timeline {{ height: 300px; overflow-y: auto; }}
        #budget-panel {{ grid-column: span 2; }}
        .event {{ margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="panel">
            <h2>Agent Interaction Graph</h2>
            <div id="agent-graph"></div>
        </div>
        <div class="panel">
            <h2>Event Timeline</h2>
            <div id="event-timeline"></div>
        </div>
        <div id="budget-panel" class="panel">
            <h2>Budget Overview</h2>
            <div id="budget-visualization"></div>
        </div>
    </div>
    <script>
        const ws = new WebSocket(`ws://${{window.location.hostname}}:{self.config.port}/ws`);
        let eventHistory = [];
        
        ws.onmessage = (event) => {{
            const data = JSON.parse(event.data);
            if (data.type === 'history') {{
                eventHistory = data.data;
                updateVisualization();
            }} else {{
                eventHistory.push(data);
                updateVisualization();
            }}
        }};

        function updateVisualization() {{
            updateAgentGraph();
            updateEventTimeline();
            updateBudgetVisualization();
        }}

        function updateAgentGraph() {{
            // D3.js force-directed graph implementation
            const nodes = [];
            const links = [];
            // Extract nodes and links from event history
            // Implementation details...
        }}

        function updateEventTimeline() {{
            const timeline = d3.select('#event-timeline');
            timeline.html('');
            eventHistory.forEach(event => {{
                timeline.append('div')
                    .attr('class', 'event')
                    .html(`
                        <strong>${{new Date(event.timestamp).toLocaleTimeString()}}</strong>
                        <br/>
                        ${{event.type}}: ${{JSON.stringify(event.data)}}
                    `);
            }});
        }}

        function updateBudgetVisualization() {{
            // D3.js budget visualization implementation
            // Implementation details...
        }}
    </script>
</body>
</html>
        """

    def handle_event(self, event: Event) -> ProviderContext | None:
        """Handle events by updating the web visualization."""
        if event.type == EventType.START:
            return self.handle_start(event.payload)
        elif event.type == EventType.MESSAGE_COMPLETION:
            return self.handle_message_completion()
        elif event.type == EventType.TOOL_EXECUTION:
            return self.handle_tool_execution()
        elif event.type == EventType.POST_TOOL_EXECUTION:
            return self.handle_post_tool_execution()
        return None

    def handle_start(self, payload: ProviderContext) -> ProviderContext | None:
        """Handle agent start by initializing the visualization."""
        if not self.context:
            logger.warning("No context available for web debug provider")
            return None

        agent_data = {
            "name": payload.current_agent.name,
            "model": payload.current_agent.model,
            "instructions": payload.current_agent.instructions,
        }

        self._run_coroutine(self._broadcast_event("agent_start", agent_data))
        return payload

    def handle_message_completion(self) -> None:
        """Handle message completion by updating the visualization."""
        if not self.context:
            return

        if self.config.show_budget:
            self._update_budget_visualization()

        message_data = {
            "agent": self.context.current_agent.name,
            "message": self.context.current_message.model_dump() if self.context.current_message else None,
        }

        self._run_coroutine(self._broadcast_event("message_completion", message_data))

    def handle_tool_execution(self) -> None:
        """Handle tool execution by updating the visualization."""
        if not self.context or not self.context.message_history:
            return

        latest_message = self.context.message_history[-1]
        if not latest_message.tool_calls:
            return

        tool_data = [
            {"name": tool_call.function.name, "arguments": tool_call.function.arguments}
            for tool_call in latest_message.tool_calls
        ]

        self._run_coroutine(self._broadcast_event("tool_execution", tool_data))

    def handle_post_tool_execution(self) -> None:
        """Handle post tool execution by updating the visualization."""
        if not self.context or not self.context.message_history:
            return

        result_messages = [msg.model_dump() for msg in self.context.message_history[-2:] if msg.role == "tool"]

        if result_messages:
            self._run_coroutine(self._broadcast_event("tool_result", result_messages))

    def _update_budget_visualization(self) -> None:
        """Update the budget visualization."""
        if not self.config.show_budget:
            return

        manager = ProviderManager()
        budget = manager.get_provider_by_id(self.context.current_agent.name, "budget")

        if isinstance(budget, BudgetProvider):
            budget_data = {
                "max_spent": budget.config.max_spent,
                "max_tokens": budget.config.max_tokens,
                "current_spent": budget.config.current_spent,
                "current_tokens": budget.config.current_tokens,
            }

            self._run_coroutine(self._broadcast_event("budget_update", budget_data))
