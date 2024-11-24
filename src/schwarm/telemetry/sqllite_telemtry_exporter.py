"""Exporter for storing OpenTelemetry spans in SQLite."""

import json
import sqlite3

from schwarm.telemetry.base.http_telemetry_exporter import HttpTelemetryExporter


class SqliteTelemetryExporter(HttpTelemetryExporter):
    """Exporter for storing OpenTelemetry spans in SQLite."""

    def __init__(self, db_path="schwarm_events.db"):
        """Exporter for storing OpenTelemetry spans in SQLite."""
        super().__init__()
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Set up the SQLite database."""
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
                    attributes TEXT
                )
            """)
            conn.commit()

    def export(self, spans):
        """Store spans in the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            for span in spans:
                span_dict = span.to_dict()
                conn.execute(
                    """
                    INSERT INTO traces (id, trace_id, span_id, parent_span_id, name, start_time, end_time, attributes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        span_dict["context"]["span_id"],
                        span_dict["context"]["trace_id"],
                        span_dict["parent_span_id"],
                        span_dict["name"],
                        span_dict["start_time"],
                        span_dict["end_time"],
                        json.dumps(span_dict["attributes"]),  # Store attributes as JSON
                    ),
                )
            conn.commit()

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
                }
                for row in cursor.fetchall()
            ]

    def query_span_by_id(self, span_id):
        """Retrieve a specific span by its ID."""
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
                }
            return None

    def shutdown(self):
        """Cleanup resources."""
        print("SQLite exporter shutdown completed.")
