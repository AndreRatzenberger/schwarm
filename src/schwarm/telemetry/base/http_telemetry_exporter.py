"""Base class for custom OpenTelemetry exporters."""

from abc import ABC, abstractmethod
from threading import Thread

import uvicorn
from fastapi import FastAPI
from opentelemetry.sdk.trace.export import SpanExportResult

from schwarm.telemetry.base.telemetry_exporter import TelemetryExporter


class HttpTelemetryExporter(TelemetryExporter, ABC):
    """Base class for custom OpenTelemetry exporters."""

    def __init__(self, api_host="0.0.0.0", api_port=8000):
        """Initialize the base exporter."""
        super().__init__()
        self.api_host = api_host
        self.api_port = api_port
        self.app = FastAPI()
        self._configure_api()
        self._start_api()

    def _export(self, spans):
        """Forward spans to the backend."""
        try:
            result = self.export(spans)
            if result is None:
                return SpanExportResult.SUCCESS
            return result
        except Exception:
            return SpanExportResult.FAILURE
        finally:
            self.shutdown()

    @abstractmethod
    def query_spans(self):
        """Retrieve all spans. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the query_spans method")

    @abstractmethod
    def query_span_by_id(self, span_id):
        """Retrieve a span by ID. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement the query_span_by_id method")

    def _configure_api(self):
        """Set up API endpoints for querying spans."""

        @self.app.get("/spans")
        def get_spans():
            """Retrieve all spans."""
            return self.query_spans()

        @self.app.get("/spans/{span_id}")
        def get_span_by_id(span_id: str):
            """Retrieve a span by its ID."""
            return self.query_span_by_id(span_id)

    def _start_api(self):
        """Run the FastAPI app in a background thread."""

        def run():
            uvicorn.run(self.app, host=self.api_host, port=self.api_port, log_level="info")

        thread = Thread(target=run, daemon=True)
        thread.start()
