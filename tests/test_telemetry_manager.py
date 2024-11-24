import pytest
from opentelemetry import trace
from schwarm.telemetry.telemetry_manager import TelemetryManager
from schwarm.telemetry.sqlite_telemetry_exporter import SqliteTelemetryExporter

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

def test_telemetry_manager_initialization(telemetry_manager):
    """Test TelemetryManager initialization."""
    assert isinstance(telemetry_manager.global_tracer, trace.Tracer)
    assert len(telemetry_manager.enabled_providers) == 2
    assert "test_provider" in telemetry_manager.enabled_providers
    assert "all" in telemetry_manager.enabled_providers

def test_is_tracing_enabled(telemetry_manager):
    """Test tracing enabled check."""
    assert telemetry_manager.is_tracing_enabled("test_provider") is True
    assert telemetry_manager.is_tracing_enabled("all") is True
    assert telemetry_manager.is_tracing_enabled("disabled_provider") is False

def test_get_tracer(telemetry_manager):
    """Test getting tracers for different providers."""
    # Get tracer for enabled provider
    tracer1 = telemetry_manager.get_tracer("test_provider")
    assert isinstance(tracer1, trace.Tracer)
    assert "test_provider" in telemetry_manager.tracers

    # Get tracer for disabled provider (should return no-op tracer)
    tracer2 = telemetry_manager.get_tracer("disabled_provider")
    assert isinstance(tracer2, trace.Tracer)
    assert "disabled_provider" not in telemetry_manager.tracers

    # Get same tracer again (should reuse existing instance)
    tracer3 = telemetry_manager.get_tracer("test_provider")
    assert tracer3 is tracer1

def test_telemetry_manager_with_multiple_exporters(test_db_path):
    """Test TelemetryManager with multiple exporters."""
    exporter1 = SqliteTelemetryExporter(db_path=test_db_path)
    exporter2 = SqliteTelemetryExporter(db_path=test_db_path + "_2")
    
    manager = TelemetryManager(
        telemetry_exporters=[exporter1, exporter2],
        enabled_providers=["test_provider"]
    )
    
    assert isinstance(manager.global_tracer, trace.Tracer)
    assert len(manager.enabled_providers) == 1

def test_telemetry_manager_with_no_exporters():
    """Test TelemetryManager initialization with no exporters."""
    manager = TelemetryManager(telemetry_exporters=[], enabled_providers=[])
    assert isinstance(manager.global_tracer, trace.Tracer)
    assert len(manager.enabled_providers) == 0

def test_telemetry_manager_with_all_providers():
    """Test TelemetryManager with 'all' providers enabled."""
    manager = TelemetryManager(
        telemetry_exporters=[],
        enabled_providers=["all"]
    )
    
    # Should enable tracing for any provider when 'all' is specified
    assert manager.is_tracing_enabled("any_provider") is True
    assert manager.is_tracing_enabled("another_provider") is True
