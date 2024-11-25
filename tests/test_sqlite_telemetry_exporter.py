import os
import pytest
import sqlite3
from schwarm.telemetry.sqlite_telemetry_exporter import SqliteTelemetryExporter

@pytest.fixture
def test_db_path(tmp_path):
    """Fixture to provide a temporary database path."""
    return str(tmp_path / "test_events.db")

@pytest.fixture
def exporter(test_db_path):
    """Fixture to provide a SqliteTelemetryExporter instance."""
    exporter = SqliteTelemetryExporter(db_path=test_db_path)
    yield exporter
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

class MockSpan:
    """Mock span class for testing."""
    def __init__(self, span_id, trace_id, parent_span_id, name, start_time, end_time, attributes):
        self.span_id = span_id
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.attributes = attributes

    def to_dict(self):
        return {
            "context": {
                "span_id": self.span_id,
                "trace_id": self.trace_id
            },
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "attributes": self.attributes
        }

def test_initialize_database(test_db_path):
    """Test database initialization."""
    exporter = SqliteTelemetryExporter(db_path=test_db_path)
    
    # Verify table creation
    with sqlite3.connect(test_db_path) as conn:
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='traces'
        """)
        assert cursor.fetchone() is not None

def test_export_spans(exporter):
    """Test exporting spans to SQLite database."""
    # Create test spans
    spans = [
        MockSpan(
            span_id="span1",
            trace_id="trace1",
            parent_span_id="parent1",
            name="test_span_1",
            start_time="2024-01-01T10:00:00",
            end_time="2024-01-01T10:00:01",
            attributes={"key1": "value1"}
        ),
        MockSpan(
            span_id="span2",
            trace_id="trace1",
            parent_span_id="span1",
            name="test_span_2",
            start_time="2024-01-01T10:00:01",
            end_time="2024-01-01T10:00:02",
            attributes={"key2": "value2"}
        )
    ]

    # Export spans
    exporter.export(spans)

    # Query and verify
    stored_spans = exporter.query_spans()
    assert len(stored_spans) == 2
    
    # Verify first span
    span1 = exporter.query_span_by_id("span1")
    assert span1 is not None
    assert span1["trace_id"] == "trace1"
    assert span1["name"] == "test_span_1"
    assert span1["attributes"] == {"key1": "value1"}

    # Verify second span
    span2 = exporter.query_span_by_id("span2")
    assert span2 is not None
    assert span2["parent_span_id"] == "span1"
    assert span2["name"] == "test_span_2"
    assert span2["attributes"] == {"key2": "value2"}

def test_query_nonexistent_span(exporter):
    """Test querying a span that doesn't exist."""
    result = exporter.query_span_by_id("nonexistent")
    assert result is None

def test_export_duplicate_span(exporter):
    """Test handling of duplicate span IDs."""
    span = MockSpan(
        span_id="duplicate_span",
        trace_id="trace1",
        parent_span_id=None,
        name="test_span",
        start_time="2024-01-01T10:00:00",
        end_time="2024-01-01T10:00:01",
        attributes={"key": "value1"}
    )

    # Export the same span twice
    exporter.export([span])
    with pytest.raises(sqlite3.IntegrityError):
        exporter.export([span])

def test_shutdown(exporter, capsys):
    """Test shutdown method."""
    exporter.shutdown()
    captured = capsys.readouterr()
    assert "SQLite exporter shutdown completed" in captured.out
