"""Base class for custom OpenTelemetry exporters."""

import asyncio
import mimetypes
import socket
from abc import ABC, abstractmethod
from threading import Thread

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketDisconnect
from loguru import logger
from opentelemetry.sdk.trace.export import SpanExportResult

from schwarm.configs.telemetry_config import TelemetryConfig
from schwarm.manager.stream_manager import StreamManager, StreamToolManager
from schwarm.provider.provider_manager import ProviderManager
from schwarm.telemetry.base.telemetry_exporter import TelemetryExporter
from schwarm.utils.settings import get_environment


class HttpTelemetryExporter(TelemetryExporter, ABC):
    """Base class for custom OpenTelemetry exporters."""

    def __init__(self, config: TelemetryConfig, api_host="127.0.0.1", api_port=8123):
        """Initialize the base exporter."""
        super().__init__(config)
        self.api_host = api_host
        self.api_port = api_port
        self.app = FastAPI()
        self.loaded_modules = {}
        self.chat_status_connections = set()
        self.break_status_connections = set()
        self.span_connections = set()  # New: WebSocket connections for span updates

        mimetypes.add_type("application/javascript", ".js")
        mimetypes.add_type("application/javascript", ".mjs")

        # Base directory for static files
        self.base_dir = get_environment().parent.parent.joinpath("schwarm")
        index_file_path = self.base_dir.joinpath("index.html")
        assets_dir = self.base_dir.joinpath("assets")

        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allows all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allows all methods
            allow_headers=["*"],  # Allows all headers
        )

        # Mount static assets
        if index_file_path.exists() and assets_dir.exists():
            logger.info(f"Serving static files from: {self.base_dir}")
            self.app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        else:
            raise FileNotFoundError(f"Static files not found in {self.base_dir}")

        self._configure_api()
        self._start_api()

    def _export(self, spans):
        """Forward spans to the backend."""
        try:
            result = self.export(spans)
            # Broadcast each span via WebSocket
            for span in spans:
                asyncio.create_task(self.broadcast_span(span))
            if result is None:
                return SpanExportResult.SUCCESS
            return result
        except Exception:
            return SpanExportResult.FAILURE
        finally:
            self.shutdown()

    async def broadcast_span(self, span):
        """Broadcast a single span to all connected clients."""
        if not self.span_connections:
            return

        # Convert span to dict for JSON serialization
        span_data = {
            "id": span.id,
            "name": span.name,
            "start_time": span.start_time,
            "end_time": span.end_time,
            "status_code": span.status_code,
            "parent_span_id": span.parent_span_id,
            "attributes": span.attributes,
        }

        for connection in self.span_connections.copy():
            try:
                await connection.send_json({"type": "span", "data": span_data})
            except Exception as e:
                logger.error(f"Failed to send span: {e}")
                self.span_connections.remove(connection)

    async def broadcast_chat_status(self, status: bool):
        """Broadcast chat status to all connected clients."""
        for connection in self.chat_status_connections.copy():
            try:
                await connection.send_json({"chat_requested": status})
            except Exception as e:
                logger.error(f"Failed to send chat status: {e}")
                self.chat_status_connections.remove(connection)

    async def broadcast_break_status(self, status: bool):
        """Broadcast break status to all connected clients."""
        for connection in self.break_status_connections.copy():
            try:
                await connection.send_json({"is_paused": status})
            except Exception as e:
                logger.error(f"Failed to send break status: {e}")
                self.break_status_connections.remove(connection)

    def find_free_port(self, start_port=8123, max_port=9000):
        """Find a free port starting from `start_port`."""
        for port in range(start_port, max_port + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    # Try binding to the port
                    s.bind(("127.0.0.1", port))
                    return port  # Port is free
                except OSError:
                    continue  # Port is in use, try next
        raise RuntimeError("No free port found in the specified range.")

    @abstractmethod
    def query_spans(self):
        """Retrieve all spans. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the query_spans method")

    @abstractmethod
    def query_span_by_id(self, span_id):
        """Retrieve a span by ID. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the query_span_by_id method")

    @abstractmethod
    def query_spans_after_id(self, after_id):
        """Retrieve all spans created after the given span ID. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the query_spans_after_id method")

    def _configure_api(self):
        """Set up API endpoints for querying spans."""

        @self.app.get("/", include_in_schema=False)
        def serve_index():
            """Serve the index.html file."""
            return FileResponse(str(self.base_dir.joinpath("index.html")))

        @self.app.websocket("/ws/spans")
        async def span_websocket(websocket: WebSocket):
            """Stream individual spans via WebSocket."""
            await websocket.accept()
            self.span_connections.add(websocket)
            try:
                while True:
                    try:
                        await asyncio.sleep(0.1)
                    except asyncio.CancelledError:
                        break
            except WebSocketDisconnect:
                logger.debug("Span WebSocket disconnected normally")
            except Exception as e:
                logger.error(f"Span WebSocket error: {e}")
            finally:
                self.span_connections.remove(websocket)

        @self.app.websocket("/ws/break-status")
        async def break_status_websocket(websocket: WebSocket):
            """Handle break status via WebSocket."""
            await websocket.accept()
            self.break_status_connections.add(websocket)
            try:
                while True:
                    try:
                        # Check for incoming break commands
                        data = await websocket.receive_json()
                        if "set_break" in data:
                            pm = ProviderManager._instance
                            if pm:
                                pm._global_break = data["set_break"]
                                # Broadcast new status to all clients
                                await self.broadcast_break_status(pm._global_break)

                        # Send current status periodically
                        pm = ProviderManager._instance
                        if pm:
                            await websocket.send_json({"is_paused": pm._global_break})
                        await asyncio.sleep(0.1)
                    except asyncio.CancelledError:
                        break
            except WebSocketDisconnect:
                logger.debug("Break status WebSocket disconnected normally")
            except Exception as e:
                logger.error(f"Break status WebSocket error: {e}")
            finally:
                self.break_status_connections.remove(websocket)

        @self.app.post("/breakpoint/turns")
        def set_breakpoint_number(turn_amount: int):
            """Toggle the global break state."""
            pm = ProviderManager._instance
            if pm:
                pm.breakpoint_counter = turn_amount - 1
                return pm.breakpoint_counter

        @self.app.get("/breakpoint/turns")
        def get_breakpoint_number():
            """Toggle the global break state."""
            pm = ProviderManager._instance
            if pm:
                return pm.breakpoint_counter

        @self.app.post("/breakpoint")
        def toggle_breakpoint(event_type: str):
            """Toggle the global break state."""
            pm = ProviderManager._instance
            if pm:
                pm.toggle_breakpoint(event_type)
                return pm.breakpoint

        @self.app.get("/breakpoint")
        def show_breakpoints():
            """Toggle the global break state."""
            pm = ProviderManager._instance
            if pm:
                return pm.breakpoint

        @self.app.websocket("/ws/chat-status")
        async def chat_status_websocket(websocket: WebSocket):
            """Stream chat status via WebSocket."""
            await websocket.accept()
            self.chat_status_connections.add(websocket)
            try:
                while True:
                    try:
                        # Check provider manager status
                        pm = ProviderManager._instance
                        if pm:
                            chat_requested = pm._global_break & pm.wait_for_user_input
                            await websocket.send_json({"chat_requested": chat_requested})
                        await asyncio.sleep(0.1)
                    except asyncio.CancelledError:
                        break
            except WebSocketDisconnect:
                logger.debug("Chat status WebSocket disconnected normally")
            except Exception as e:
                logger.error(f"Chat status WebSocket error: {e}")
            finally:
                self.chat_status_connections.remove(websocket)

        @self.app.websocket("/ws/chat")
        async def chat_websocket_endpoint(websocket: WebSocket):
            """Handle chat via WebSocket."""
            await websocket.accept()
            try:
                while True:
                    try:
                        # Wait for user input
                        user_input = await websocket.receive_text()

                        # Get provider manager instance
                        pm = ProviderManager._instance
                        if pm:
                            # Set user input and toggle break
                            pm.last_user_input = user_input
                            pm._global_break = False

                            # Send confirmation back to client
                            await websocket.send_json({"status": "success", "message": "Input received"})

                            # Broadcast new break status
                            await self.broadcast_break_status(False)
                    except asyncio.CancelledError:
                        break
            except WebSocketDisconnect:
                logger.debug("Chat WebSocket disconnected normally")
            except Exception as e:
                logger.error(f"Chat WebSocket error: {e}")

        @self.app.get("/spans")
        def get_spans(after_id: str | None = None):
            """Retrieve spans, optionally filtered by after_id."""
            if after_id:
                return self.query_spans_after_id(after_id)
            return self.query_spans()

        @self.app.get("/spans/{span_id}")
        def get_span_by_id(span_id: str):
            """Retrieve a span by its ID."""
            return self.query_span_by_id(span_id)

        @self.app.get("/load")
        def get_loaded_modules():
            """Retrieve a span by its ID."""
            result = ""
            for obj in self.loaded_modules:
                result += obj[1].name
            return f"{result}"

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Stream LLM outputs via WebSocket."""
            stream_manager = StreamManager()
            await stream_manager.connect(websocket)
            try:
                while True:
                    try:
                        # Wait for messages but allow for graceful shutdown
                        await asyncio.sleep(0.1)
                    except asyncio.CancelledError:
                        break
            except WebSocketDisconnect:
                logger.debug("WebSocket disconnected normally")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                await stream_manager.disconnect(websocket)

        @self.app.websocket("/ws/tool")
        async def tool_websocket_endpoint(websocket: WebSocket):
            """Stream tool outputs via WebSocket."""
            stream_manager = StreamToolManager()
            await stream_manager.connect(websocket)
            try:
                while True:
                    try:
                        # Wait for messages but allow for graceful shutdown
                        await asyncio.sleep(0.1)
                    except asyncio.CancelledError:
                        break
            except WebSocketDisconnect:
                logger.debug("WebSocket disconnected normally")
            except Exception as e:
                logger.error(f"Tool WebSocket error: {e}")
            finally:
                await stream_manager.disconnect(websocket)

    def _start_api(self):
        def run():
            free_port = self.find_free_port()
            print(f"Starting server on port {free_port}...")
            uvicorn.run(self.app, host="127.0.0.1", port=free_port)
            uvicorn.run(self.app, host=self.api_host, port=self.api_port, log_level="info")

        thread = Thread(target=run, daemon=True)
        thread.start()
