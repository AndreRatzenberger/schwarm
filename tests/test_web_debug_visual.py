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
from typing import Any

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
        port=8001,
        save_history=True,
        show_budget=True
    )
)

# Demo control panel HTML
DEMO_CONTROLS = """
<!DOCTYPE html>
<html>
<head>
    <title>Web Debug UI Demo Controls</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .control-panel { 
            position: fixed;
            top: 20px;
            right: 20px;
            width: 300px;
            background: #fff;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .button {
            display: block;
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }
        .button:hover { background: #0056b3; }
        .scenario { margin: 20px 0; }
        .status { 
            padding: 10px;
            margin-top: 20px;
            background: #f8f9fa;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="control-panel">
        <h2>UI Demo Controls</h2>
        
        <div class="scenario">
            <h3>1. Basic Agent Interaction</h3>
            <button class="button" onclick="triggerEvent('start_agent')">Start Agent</button>
            <button class="button" onclick="triggerEvent('send_message')">Send Message</button>
            <button class="button" onclick="triggerEvent('tool_call')">Execute Tool</button>
        </div>

        <div class="scenario">
            <h3>2. Multi-Agent Scenario</h3>
            <button class="button" onclick="triggerEvent('add_agent')">Add New Agent</button>
            <button class="button" onclick="triggerEvent('agent_handoff')">Agent Handoff</button>
        </div>

        <div class="scenario">
            <h3>3. Resource Usage</h3>
            <button class="button" onclick="triggerEvent('update_budget')">Update Budget</button>
            <button class="button" onclick="triggerEvent('token_spike')">Simulate Token Spike</button>
        </div>

        <div class="scenario">
            <h3>4. Error Scenarios</h3>
            <button class="button" onclick="triggerEvent('tool_error')">Tool Error</button>
            <button class="button" onclick="triggerEvent('agent_error')">Agent Error</button>
        </div>

        <div class="scenario">
            <h3>5. Reset</h3>
            <button class="button" onclick="triggerEvent('reset')" style="background: #dc3545;">Reset Demo</button>
        </div>

        <div class="status" id="status">Status: Ready</div>
    </div>

    <script>
        function triggerEvent(eventType) {
            const status = document.getElementById('status');
            status.textContent = `Status: Triggering ${eventType}...`;
            
            fetch(`/trigger/${eventType}`, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    status.textContent = `Status: ${data.event} completed`;
                    setTimeout(() => {
                        status.textContent = 'Status: Ready';
                    }, 2000);
                });
        }
    </script>
</body>
</html>
"""

# Save demo controls to templates
with open(TEMPLATES_DIR / "demo.html", "w") as f:
    f.write(DEMO_CONTROLS)

@app.get("/demo", response_class=HTMLResponse)
async def demo_controls():
    """Show demo controls panel."""
    return templates.TemplateResponse("demo.html", {"request": {}})

@app.post("/trigger/{event_type}")
async def trigger_event(event_type: str):
    """Trigger a specific demo event."""
    if event_type == "start_agent":
        await simulate_agent_start()
    elif event_type == "send_message":
        await simulate_message()
    elif event_type == "tool_call":
        await simulate_tool_call()
    elif event_type == "add_agent":
        await simulate_new_agent()
    elif event_type == "agent_handoff":
        await simulate_handoff()
    elif event_type == "update_budget":
        await simulate_budget_update()
    elif event_type == "token_spike":
        await simulate_token_spike()
    elif event_type == "tool_error":
        await simulate_tool_error()
    elif event_type == "agent_error":
        await simulate_agent_error()
    elif event_type == "reset":
        await reset_demo()
    
    return {"status": "success", "event": event_type}

async def simulate_agent_start():
    """Simulate starting a new agent."""
    agent = Agent(
        name="DemoAgent",
        model="gpt-4",
        description="Demo agent for UI testing",
        instructions="This is a demo agent for testing the web debug interface."
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
    
    debug_provider.handle_event(event)

async def simulate_message():
    """Simulate message exchange."""
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
    if context:
        context.message_history.append(message)
        
        event = Event(
            type=EventType.MESSAGE_COMPLETION,
            payload=context,
            agent_id=context.current_agent.name,
            datetime=datetime.now().isoformat()
        )
        
        debug_provider.handle_event(event)

async def simulate_tool_call():
    """Simulate tool execution."""
    tools = [
        {"name": "search_web", "args": {"query": "test query"}},
        {"name": "calculate", "args": {"expression": "2 + 2"}},
        {"name": "fetch_data", "args": {"url": "http://example.com"}},
        {"name": "process_text", "args": {"text": "sample text"}}
    ]
    
    context = debug_provider.context
    if context:
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
        
        debug_provider.handle_event(event)

async def simulate_new_agent():
    """Simulate adding a new agent."""
    agent_types = [
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
        instructions=f"This is a {agent_type[0]} for testing multi-agent scenarios."
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
    
    debug_provider.handle_event(event)

async def simulate_handoff():
    """Simulate agent handoff."""
    if not debug_provider.context or len(debug_provider._event_history) < 2:
        await simulate_new_agent()
        await asyncio.sleep(1)
    
    context = debug_provider.context
    if context:
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
        
        debug_provider.handle_event(event)

async def simulate_budget_update():
    """Simulate budget changes."""
    if debug_provider.context:
        budget_data = {
            "max_spent": 10.0,
            "max_tokens": 1000,
            "current_spent": time.time() % 10.0,
            "current_tokens": int(time.time() * 10) % 1000
        }
        
        debug_provider._run_coroutine(
            debug_provider._broadcast_event("budget_update", budget_data)
        )

async def simulate_token_spike():
    """Simulate sudden increase in token usage."""
    if debug_provider.context:
        # Simulate rapid token usage increase
        for _ in range(5):
            budget_data = {
                "max_spent": 10.0,
                "max_tokens": 1000,
                "current_spent": 5.0 + (time.time() % 5.0),
                "current_tokens": 700 + (int(time.time() * 10) % 300)
            }
            
            debug_provider._run_coroutine(
                debug_provider._broadcast_event("budget_update", budget_data)
            )
            await asyncio.sleep(0.5)

async def simulate_tool_error():
    """Simulate tool execution error."""
    context = debug_provider.context
    if context:
        error_message = Message(
            role="tool",
            content="Error executing tool",
            additional_info={
                "error": "Tool execution failed",
                "details": "Connection timeout",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        context.message_history.append(error_message)
        
        event = Event(
            type=EventType.TOOL_EXECUTION,
            payload=context,
            agent_id=context.current_agent.name,
            datetime=datetime.now().isoformat()
        )
        
        debug_provider.handle_event(event)

async def simulate_agent_error():
    """Simulate agent error."""
    context = debug_provider.context
    if context:
        error_message = Message(
            role="assistant",
            content="Error in agent execution",
            additional_info={
                "error": "Agent execution failed",
                "details": "Model API error",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        context.message_history.append(error_message)
        
        event = Event(
            type=EventType.MESSAGE_COMPLETION,
            payload=context,
            agent_id=context.current_agent.name,
            datetime=datetime.now().isoformat()
        )
        
        debug_provider.handle_event(event)

async def reset_demo():
    """Reset the demo state."""
    debug_provider._event_history.clear()
    debug_provider._run_coroutine(debug_provider._broadcast_event("reset", {}))

def run_demo():
    """Run the demo server.
    
    This starts:
    1. The web debug interface at http://localhost:8001
    2. The demo control panel at http://localhost:8000/demo
    
    Usage:
    1. Start the demo:
       uv run tests/test_web_debug_visual.py
       
    2. Open two browser windows:
       - http://localhost:8001 (Debug Interface)
       - http://localhost:8000/demo (Control Panel)
       
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
    logger.info("1. Open http://localhost:8001 to see the debug interface")
    logger.info("2. Open http://localhost:8000/demo to access demo controls")
    logger.info("3. Use the control panel to trigger different scenarios")
    logger.info("4. Watch the debug interface update in real-time")
    
    # Initialize providers
    debug_provider.initialize()
    
    # Run demo control server
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == "__main__":
    run_demo()
