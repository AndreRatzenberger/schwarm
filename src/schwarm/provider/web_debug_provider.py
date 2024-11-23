"""Web-based debug provider for visualizing system information through a served website."""

import asyncio
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import Field

from schwarm.events.event_data import Event
from schwarm.provider.base import BaseEventHandleProvider, BaseEventHandleProviderConfig

STATIC_DIR = Path("static")
TEMPLATES_DIR = Path("templates")
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)


class WebDebugConfig(BaseEventHandleProviderConfig):
    """Configuration for the web debug provider."""

    host: str = Field(default="localhost", description="Host to serve the web interface")
    port: int = Field(default=8000, description="Port to serve the web interface")
    provider_id: str = Field(default="web_debug", description="Provider ID")


class WebDebugProvider(BaseEventHandleProvider):
    """Web-based debug provider that visualizes system information through a served website."""

    config: WebDebugConfig
    _provider_id: str = Field(default="web_debug", description="Provider ID")
    _app: FastAPI
    _loop: asyncio.AbstractEventLoop | None

    def __init__(self, config: WebDebugConfig, **data: Any):
        """Initialize the web debug provider."""
        super().__init__(config=config, **data)
        self._app = FastAPI()
        self._loop = None
        self._setup_cors()
        self._setup_routes()
        self._setup_static_files()
        self._start_server()

    def _setup_cors(self) -> None:
        """Set up CORS middleware for the FastAPI app."""
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self) -> None:
        """Set up FastAPI routes for the web interface."""
        app = self._app

        @app.get("/log", response_class=HTMLResponse)
        async def demo_controls(request: Request):
            """Show demo controls panel."""
            templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
            return templates.TemplateResponse("demo.html", {"request": request})

    def _setup_static_files(self) -> None:
        """Set up static files directory for web assets."""
        self._app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

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
        input("Press Enter to continue...")

    def initialize(self) -> None:
        """Initialize the web debug provider and start the web server."""
        self._start_server()

    async def handle_event(self, event: Event) -> dict:
        """Handle events by updating the web visualization."""
        logger.info(f"Received event: {event.type} with payload: {event.payload}")
        return {"status": "success", "event": event.type}
