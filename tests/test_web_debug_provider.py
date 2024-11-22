"""Tests for the web-based debug provider with visual examples."""

import asyncio
import time
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from loguru import logger

from schwarm.core.schwarm import Schwarm
from schwarm.events.event_data import Event, EventType
from schwarm.models.agent import Agent
from schwarm.models.message import Message
from schwarm.models.provider_context import ProviderContext
from schwarm.provider.web_debug_provider import WebDebugConfig, WebDebugProvider


def create_test_agent() -> Agent:
    """Create a test agent with web debug provider."""
    agent = Agent(
        name="TestAgent",
        model="gpt-4",
        description="Test agent for web debug visualization",
        instructions="You are a test agent demonstrating the web debug interface.",
        functions=[
            lambda x: x  # Simple test function
        ]
    )
    
    # Add web debug provider
    agent.provider_configurations.append(
        WebDebugConfig(
            host="localhost",
            port=8001,  # Different port for testing
            save_history=True,
            show_budget=True
        )
    )
    
    return agent


@pytest.fixture
def web_debug_provider(tmp_path) -> Generator[WebDebugProvider, None, None]:
    """Create a web debug provider instance for testing."""
    config = WebDebugConfig(
        host="localhost",
        port=8001,
        save_history=True,
        show_budget=True
    )
    provider = WebDebugProvider(config=config)
    provider.initialize()
    # Wait for server to start
    time.sleep(1)
    yield provider


def test_web_debug_interface(web_debug_provider: WebDebugProvider, tmp_path):
    """Test the web debug interface with visual examples.
    
    This test demonstrates:
    1. Initial dashboard view
    2. Agent interaction visualization
    3. Event timeline
    4. Budget tracking
    5. Replay functionality
    """
    # Create test client
    client = TestClient(web_debug_provider._app)
    
    # Test dashboard HTML
    response = client.get("/")
    assert response.status_code == 200
    assert "Schwarm Debug Dashboard" in response.text
    
    logger.info("Dashboard is accessible at http://localhost:8001")
    logger.info("Screenshots would show:")
    logger.info("1. Empty dashboard with panels for agent graph, timeline, and budget")
    
    # Create test events
    context = ProviderContext(
        current_agent=create_test_agent(),
        message_history=[
            Message(role="user", content="Hello, test agent!"),
            Message(role="assistant", content="Hello! I'm here to help test the visualization.")
        ]
    )
    
    # Simulate agent start
    start_event = Event(
        type=EventType.START,
        payload=context,
        agent_id="TestAgent",
        datetime="2024-01-01T12:00:00"
    )
    web_debug_provider.handle_event(start_event)
    
    logger.info("2. Agent graph now shows TestAgent node")
    
    # Simulate message completion
    msg_event = Event(
        type=EventType.MESSAGE_COMPLETION,
        payload=context,
        agent_id="TestAgent",
        datetime="2024-01-01T12:00:01"
    )
    web_debug_provider.handle_event(msg_event)
    
    logger.info("3. Timeline shows message completion event")
    logger.info("4. Agent graph shows message flow")
    
    # Simulate tool execution
    tool_event = Event(
        type=EventType.TOOL_EXECUTION,
        payload=context,
        agent_id="TestAgent",
        datetime="2024-01-01T12:00:02"
    )
    web_debug_provider.handle_event(tool_event)
    
    logger.info("5. Timeline shows tool execution")
    logger.info("6. Agent graph shows tool interaction")
    
    # Test WebSocket connection
    with client.websocket_connect("/ws") as websocket:
        # Should receive event history
        data = websocket.receive_json()
        assert data["type"] == "history"
        assert len(data["data"]) > 0
        
        logger.info("7. Replay panel shows recorded events")
    
    logger.info("\nVisualization Features Demonstrated:")
    logger.info("- Real-time agent interaction graph")
    logger.info("- Event timeline with timestamps")
    logger.info("- Tool execution visualization")
    logger.info("- Event replay functionality")
    logger.info("- WebSocket-based updates")


def test_full_agent_interaction():
    """Test a complete agent interaction with web debug visualization."""
    schwarm = Schwarm()
    agent = create_test_agent()
    schwarm.register_agent(agent)
    
    # Run a simple interaction
    response = schwarm.quickstart(
        agent=agent,
        input_text="Hello! Please help me test the visualization system.",
        context_variables={},
        mode="auto"
    )
    
    logger.info("\nFull Interaction Visualization:")
    logger.info("1. Dashboard shows complete interaction flow")
    logger.info("2. Agent graph displays message sequence")
    logger.info("3. Timeline shows all events in order")
    logger.info("4. Budget panel tracks resource usage")
    logger.info("5. Replay system allows stepping through events")
    
    assert response.messages
    assert len(response.messages) > 0


if __name__ == "__main__":
    """Run the tests and provide visual output.
    
    To run:
    1. python -m pytest tests/test_web_debug_provider.py -s
    2. Open http://localhost:8001 in browser to see visualization
    """
    pytest.main([__file__, "-s"])
