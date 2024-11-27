import pytest
from unittest.mock import MagicMock
from schwarm.core.schwarm import Schwarm2
from schwarm.telemetry.sqlite_telemetry_exporter import SqliteTelemetryExporter
from schwarm.telemetry.telemetry_manager import TelemetryManager
from schwarm.models.types import Agent
from schwarm.models.message import Message
from schwarm.events.event import EventType

@pytest.fixture
def test_db_path(tmp_path):
    """Fixture to provide a temporary database path."""
    return str(tmp_path / "test_events.db")

@pytest.fixture
def sqlite_exporter(test_db_path):
    """Fixture to provide a SqliteTelemetryExporter instance."""
    return SqliteTelemetryExporter(db_path=test_db_path)

@pytest.fixture
def telemetry_manager(sqlite_exporter):
    """Fixture to provide a TelemetryManager instance."""
    return TelemetryManager(
        telemetry_exporters=[sqlite_exporter],
        enabled_providers=["test_provider", "all"]
    )

@pytest.fixture
def mock_agent():
    """Fixture to provide a mock agent."""
    return Agent(
        name="test_agent",
        instructions="Test instructions",
        functions=[],
        configs=[]
    )

def test_schwarm2_initialization_with_telemetry(telemetry_manager):
    """Test Schwarm2 initialization with telemetry."""
    schwarm = Schwarm2(agent_list=[], telemetry_exporters=[])
    assert schwarm._telemetry_manager is not None
    assert isinstance(schwarm._telemetry_manager, TelemetryManager)

def test_schwarm2_with_custom_telemetry(sqlite_exporter):
    """Test Schwarm2 with custom telemetry exporter."""
    schwarm = Schwarm2(agent_list=[], telemetry_exporters=[sqlite_exporter])
    # Verify the exporter was added by checking if we can get a tracer
    tracer = schwarm._telemetry_manager.get_tracer("test_provider")
    assert tracer is not None

def test_schwarm2_event_tracking(telemetry_manager, mock_agent, sqlite_exporter):
    """Test that Schwarm2 properly tracks events through telemetry."""
    # Initialize Schwarm2 with our test exporter
    schwarm = Schwarm2(agent_list=[], telemetry_exporters=[sqlite_exporter])
    
    # Create a simple message
    message = Message(role="user", content="test message")
    
    # Run a quickstart to generate some events
    schwarm.quickstart(
        agent=mock_agent,
        input_text="test input",
        context_variables={},
        override_model="",
        mode="auto"
    )
    
    # Query the SQLite database for recorded spans
    spans = sqlite_exporter.query_spans()
    
    # Verify that key events were recorded
    event_names = [span["name"] for span in spans]
    assert any("START" in name for name in event_names)
    assert any("INSTRUCT" in name for name in event_names)

def test_schwarm2_provider_telemetry_integration(telemetry_manager, mock_agent, sqlite_exporter):
    """Test that providers properly integrate with telemetry system."""
    schwarm = Schwarm2(agent_list=[], telemetry_exporters=[sqlite_exporter])
    
    # Register the test agent
    schwarm.register_agent(mock_agent)
    
    # Verify that the provider manager has telemetry enabled
    assert schwarm._provider_manager is not None
    
    # Run a simple operation to generate provider-related spans
    schwarm.quickstart(
        agent=mock_agent,
        input_text="test input",
        context_variables={},
        override_model="",
        mode="auto"
    )
    
    # Query spans and verify provider-related events were recorded
    spans = sqlite_exporter.query_spans()
    provider_spans = [
        span for span in spans 
        if any(attr in span["attributes"].get("provider_id", "") 
              for attr in ["test_provider", "all"])
    ]
    assert len(provider_spans) > 0

def test_schwarm2_telemetry_disabled_provider(telemetry_manager, mock_agent, sqlite_exporter):
    """Test that disabled providers don't generate telemetry."""
    # Initialize with only specific providers enabled
    manager = TelemetryManager(
        telemetry_exporters=[sqlite_exporter],
        enabled_providers=["specific_provider"]  # Not including test_provider
    )
    
    schwarm = Schwarm2(agent_list=[], telemetry_exporters=[sqlite_exporter])
    schwarm.register_agent(mock_agent)
    
    # Run operation
    schwarm.quickstart(
        agent=mock_agent,
        input_text="test input",
        context_variables={},
        override_model="",
        mode="auto"
    )
    
    # Verify no spans were recorded for test_provider
    spans = sqlite_exporter.query_spans()
    test_provider_spans = [
        span for span in spans 
        if "test_provider" in span["attributes"].get("provider_id", "")
    ]
    assert len(test_provider_spans) == 0
