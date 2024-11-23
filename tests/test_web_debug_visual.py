"""Visual demo for the web debug interface.

This is a development tool that provides a live preview of the web debug interface.
It allows developers to:
1. View the UI in real-time
2. Test different scenarios and states
3. Verify UI updates and animations
4. Debug visual components
"""

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from schwarm.events.event_data import Event, EventType
from schwarm.models.agent import Agent
from schwarm.models.message import Message
from schwarm.models.provider_context import ProviderContext
from schwarm.provider.web_debug_provider import WebDebugConfig, WebDebugProvider

# Create required directories
STATIC_DIR = Path("static")
TEMPLATES_DIR = Path("templates")
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

# Create demo app
app = FastAPI()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Create web debug provider
debug_provider = WebDebugProvider(
    config=WebDebugConfig(
        host="localhost",
        port=8000,  # Changed to 8000 to match our frontend config
        save_history=True,
        show_budget=True
    )
)

def _make_serializable(obj: Any) -> Any:
    """Convert non-serializable objects to serializable format.
    
    Args:
        obj: Any Python object that needs to be made serializable
        
    Returns:
        A serializable version of the object
    """
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(v) for v in obj]
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif obj is None:
        return None
    else:
        # Convert any other type to string representation
        return str(obj)

def send_event(event: Event[ProviderContext]) -> None:
    """Send an event to the web debug interface.
    
    This function takes any Event[ProviderContext] and ensures it can be properly
    serialized before sending it to the web debug interface. It handles conversion
    of non-serializable fields to strings if necessary.
    
    Args:
        event: The event to send, containing a ProviderContext payload
    """
    # Ensure datetime is serializable
    if isinstance(event.datetime, datetime):
        event.datetime = event.datetime.isoformat()
    
    # Make context variables serializable
    if event.payload and event.payload.context_variables:
        event.payload.context_variables = _make_serializable(event.payload.context_variables)
    
    # Make message history serializable
    if event.payload and event.payload.message_history:
        for message in event.payload.message_history:
            if message.additional_info:
                message.additional_info = _make_serializable(message.additional_info)
            if message.tool_calls:
                message.tool_calls = _make_serializable(message.tool_calls)
            if message.info:
                message.info = _make_serializable(message.info)
    
    # Send event through debug provider
    debug_provider.handle_event(event)

@app.get("/demo", response_class=HTMLResponse)
async def demo_controls():
    """Show demo controls panel."""
    return templates.TemplateResponse("demo.html", {"request": {}})

@app.post("/trigger/{event_type}")
async def trigger_event(event_type: str):
    """Trigger a specific demo event."""
    if event_type == "on_start":
        await simulate_agent_start()
    elif event_type == "on_message_completion":
        await simulate_message()
    elif event_type == "on_tool_execution":
        await simulate_tool_call()
    elif event_type == "on_handoff":
        await simulate_handoff()
    elif event_type == "reset":
        await reset_demo()
    
    return {"status": "success", "event": event_type}

async def simulate_agent_start():
    """Simulate starting a new agent."""
    agent_types = [
        ("DemoAgent", "gpt-4", "Demo agent for UI testing"),
        ("ResearchAgent", "gpt-4", "Specialized in research tasks"),
        ("AnalysisAgent", "gpt-3.5-turbo", "Specialized in data analysis"),
        ("WritingAgent", "gpt-4", "Specialized in content creation"),
        ("CodingAgent", "gpt-4", "Specialized in code generation")
    ]
    
    agent_type = agent_types[int(time.time()) % len(agent_types)]
    agent = Agent(
        name=agent_type[0],
        model=agent_type[1],
        description=agent_type[2],
        instructions=f"This is a {agent_type[0]} for testing the web debug interface."
    )
    
    context = ProviderContext(
        current_agent=agent,
        message_history=[],
        context_variables={}
    )
    
    event = Event(
        type=EventType.START,
        payload=context,
        agent_id=agent.name,
        datetime=datetime.now().isoformat()
    )
    
    send_event(event)

async def simulate_message():
    """Simulate message exchange."""
    # Ensure we have an active agent
    if not debug_provider.context or not debug_provider.context.current_agent:
        await simulate_agent_start()
        await asyncio.sleep(0.5)  # Give time for the agent to be initialized
    
    messages = [
        "Hello, this is a test message!",
        "Can you help me with something?",
        "I'd like to test the visualization.",
        "How does this look in the UI?"
    ]
    
    message = Message(
        role="user",
        content=messages[int(time.time()) % len(messages)],
        sender="User"
    )
    
    context = debug_provider.context
    if context and context.current_agent:
        context.message_history.append(message)
        
        event = Event(
            type=EventType.MESSAGE_COMPLETION,
            payload=context,
            agent_id=context.current_agent.name,
            datetime=datetime.now().isoformat()
        )
        
        send_event(event)

async def simulate_tool_call():
    """Simulate tool execution."""
    # Ensure we have an active agent
    if not debug_provider.context or not debug_provider.context.current_agent:
        await simulate_agent_start()
        await asyncio.sleep(0.5)  # Give time for the agent to be initialized
    
    tools = [
        {"name": "search_web", "args": {"query": "test query"}},
        {"name": "calculate", "args": {"expression": "2 + 2"}},
        {"name": "fetch_data", "args": {"url": "http://example.com"}},
        {"name": "process_text", "args": {"text": "sample text"}}
    ]
    
    context = debug_provider.context
    if context and context.current_agent:
        tool = tools[int(time.time()) % len(tools)]
        message = Message(
            role="assistant",
            content=f"Executing {tool['name']}",
            tool_calls=[{
                "function": {
                    "name": tool['name'],
                    "arguments": tool['args']
                }
            }]
        )
        
        context.message_history.append(message)
        
        event = Event(
            type=EventType.TOOL_EXECUTION,
            payload=context,
            agent_id=context.current_agent.name,
            datetime=datetime.now().isoformat()
        )
        
        send_event(event)

async def simulate_handoff():
    """Simulate agent handoff."""
    if not debug_provider.context or len(debug_provider._event_history) < 2:
        await simulate_agent_start()
        await asyncio.sleep(1)
    
    context = debug_provider.context
    if context and context.current_agent:
        # Create handoff message
        message = Message(
            role="assistant",
            content="Handing off to another agent",
            sender=context.current_agent.name
        )
        context.message_history.append(message)
        
        # Create new agent for handoff
        new_agent = Agent(
            name="HandoffAgent",
            model="gpt-4",
            description="Agent receiving handoff",
            instructions="This agent handles tasks handed off from other agents."
        )
        context.current_agent = new_agent
        
        event = Event(
            type=EventType.HANDOFF,
            payload=context,
            agent_id=new_agent.name,
            datetime=datetime.now().isoformat()
        )
        
        send_event(event)

async def reset_demo():
    """Reset the demo state."""
    debug_provider._event_history.clear()
    debug_provider._run_coroutine(debug_provider._broadcast_event("reset", {}))

def run_demo():
    """Run the demo server.
    
    This starts:
    1. The web debug interface at http://localhost:8000
    2. The demo control panel with embedded visualization at http://localhost:8002/demo
    
    Usage:
    1. Start the demo:
       python tests/test_web_debug_visual.py
       
    2. Open http://localhost:8002/demo in your browser to see:
       - The debug interface embedded on the right
       - Control panel with test scenarios on the left
       
    3. Use the control panel buttons to:
       - Start agents
       - Simulate messages
       - Trigger tool executions
       - Test multi-agent scenarios
       - Simulate errors
       - Monitor resource usage
       
    4. Watch the debug interface update in real-time
    
    5. Use this for:
       - UI development
       - Visual testing
       - Demo preparation
       - Feature verification
    """
    logger.info("Starting Web Debug UI Demo")
    logger.info("Open http://localhost:8002/demo to access the demo interface")
    
    # Initialize providers
    debug_provider.initialize()
    
    # Run demo control server
    uvicorn.run(app, host="localhost", port=8002)  # Changed to port 8002

if __name__ == "__main__":
    run_demo()
