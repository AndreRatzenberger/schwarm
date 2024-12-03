"""Exporter for storing OpenTelemetry spans in SQLite."""

import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExportResult

from schwarm.configs.telemetry_config import TelemetryConfig
from schwarm.telemetry.base.http_telemetry_exporter import HttpTelemetryExporter
from schwarm.utils.settings import APP_SETTINGS


class SqliteTelemetryExporter(HttpTelemetryExporter):
    """Exporter for storing OpenTelemetry spans in SQLite."""

    def __init__(self, config: TelemetryConfig = TelemetryConfig(), db_path: str = "schwarm_events.db"):
        """Initialize the SQLite exporter.

        Args:
            db_path: Path to the SQLite database file
        """
        super().__init__(config)
        self.telemetry_path = Path(APP_SETTINGS.TELEMETRY)
        self.telemetry_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.telemetry_path.joinpath(db_path).__str__()
        self._initialize_database()

    def _initialize_database(self):
        """Set up the SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS traces (
                    id TEXT PRIMARY KEY,
                    trace_id TEXT,
                    span_id TEXT,
                    parent_span_id TEXT,
                    name TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    attributes TEXT,
                    status_code TEXT,
                    status_description TEXT
                )
            """)
            conn.commit()

    def _convert_attributes(self, attributes: dict[str, Any]) -> str:
        """Convert span attributes to a JSON string.

        Args:
            attributes: Dictionary of span attributes

        Returns:
            JSON string representation of attributes
        """
        # Convert attributes to a serializable format
        serializable_attrs = {}
        for key, value in attributes.items():
            # Convert complex types to strings if needed
            if isinstance(value, (dict, list, tuple)):
                serializable_attrs[key] = json.dumps(value)
            else:
                serializable_attrs[key] = str(value)
        return json.dumps(serializable_attrs)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Store spans in the SQLite database.

        Args:
            spans: Sequence of spans to export

        Returns:
            SpanExportResult indicating success or failure
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                for span in spans:
                    # Safely get span context and parent span ID
                    span_context = span.get_span_context()
                    if span_context is None:
                        continue

                    parent_span_id = None
                    if span.parent is not None:
                        parent_span_id = format(span.parent.span_id, "016x")

                    # Convert attributes to JSON string
                    attributes_json = self._convert_attributes(dict(span.attributes))  # type: ignore

                    conn.execute(
                        """
                        INSERT INTO traces (
                            id, trace_id, span_id, parent_span_id, 
                            name, start_time, end_time, attributes,
                            status_code, status_description
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            format(span_context.span_id, "016x"),
                            format(span_context.trace_id, "032x"),
                            format(span_context.span_id, "016x"),
                            parent_span_id,
                            span.name,
                            span.start_time,
                            span.end_time,
                            attributes_json,
                            span.status.status_code.name,
                            span.status.description,
                        ),
                    )
                conn.commit()
            return SpanExportResult.SUCCESS
        except Exception as e:
            print(f"Error exporting spans: {e}")
            return SpanExportResult.FAILURE

    def query_spans(self):
        """Retrieve all spans from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM traces")
            return [
                {
                    "id": row[0],
                    "trace_id": row[1],
                    "span_id": row[2],
                    "parent_span_id": row[3],
                    "name": row[4],
                    "start_time": row[5],
                    "end_time": row[6],
                    "attributes": json.loads(row[7]),
                    "status_code": row[8],
                    "status_description": row[9],
                }
                for row in cursor.fetchall()
            ]

    def query_span_by_id(self, span_id: str) -> dict[str, Any] | None:
        """Retrieve a specific span by its ID.

        Args:
            span_id: The ID of the span to retrieve

        Returns:
            Dict containing span data or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM traces WHERE id = ?", (span_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "trace_id": row[1],
                    "span_id": row[2],
                    "parent_span_id": row[3],
                    "name": row[4],
                    "start_time": row[5],
                    "end_time": row[6],
                    "attributes": json.loads(row[7]),
                    "status_code": row[8],
                    "status_description": row[9],
                }
            return None

    def query_spans_after_id(self, after_id: str) -> list[dict[str, Any]]:
        """Retrieve all spans created after the given span ID.

        Args:
            after_id: The ID of the reference span

        Returns:
            List of spans created after the reference span
        """
        with sqlite3.connect(self.db_path) as conn:
            # First get the start_time of the reference span
            cursor = conn.execute("SELECT start_time FROM traces WHERE id = ?", (after_id,))
            ref_row = cursor.fetchone()
            if not ref_row:
                return []  # Return empty list if reference span not found

            ref_start_time = ref_row[0]

            # Then get all spans created after that time
            cursor = conn.execute(
                "SELECT * FROM traces WHERE start_time > ? ORDER BY start_time ASC", (ref_start_time,)
            )
            return [
                {
                    "id": row[0],
                    "trace_id": row[1],
                    "span_id": row[2],
                    "parent_span_id": row[3],
                    "name": row[4],
                    "start_time": row[5],
                    "end_time": row[6],
                    "attributes": json.loads(row[7]),
                    "status_code": row[8],
                    "status_description": row[9],
                }
                for row in cursor.fetchall()
            ]

    def force_flush(self, timeout_millis: float = 30000) -> bool:
        """Force flush any pending spans to the database.

        Args:
            timeout_millis: Maximum time to wait for flush to complete

        Returns:
            bool indicating success
        """
        return True

    def shutdown(self) -> None:
        """Cleanup resources."""
        print("SQLite exporter shutdown completed.")
