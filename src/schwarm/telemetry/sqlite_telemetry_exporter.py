"""Exporter for storing OpenTelemetry spans in SQLite."""

import json
import sqlite3
from collections.abc import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExportResult

from schwarm.telemetry.base.http_telemetry_exporter import HttpTelemetryExporter


class SqliteTelemetryExporter(HttpTelemetryExporter):
    """Exporter for storing OpenTelemetry spans in SQLite."""

    def __init__(self, db_path: str = "schwarm_events.db"):
        """Initialize the SQLite exporter.

        Args:
            db_path: Path to the SQLite database file
        """
        super().__init__()
        self.db_path = db_path
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
                    # Convert span to dictionary format
                    span_context = span.get_span_context()
                    parent_span_id = span.parent.span_id if span.parent else None

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
                            format(parent_span_id, "016x") if parent_span_id else None,
                            span.name,
                            span.start_time,
                            span.end_time,
                            json.dumps(dict(span.attributes)),
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

    def query_span_by_id(self, span_id: str):
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
