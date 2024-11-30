"""Handoff agent implementation using schwarm_fluent architecture."""

from typing import List, Optional

from schwarm.agents.agents.agent import Agent
from schwarm.context.context import Context
from schwarm.events.events import Event, EventType
from schwarm.functions.function import Function

class HandoffFunction(Function):
    """Function that handles agent handoff logic."""
    
    def __init__(self, possible_agents: List[Agent]) -> None:
        """Initialize the handoff function.
        
        Args:
            possible_agents: List of agents that can be handed off to
        """
        super().__init__(
            name="handoff_to_agent",
            description="Hands off control to another agent"
        )
        self.possible_agents = possible_agents
        
    async def execute(
        self,
        context: Context,
        reason: str,
        agent_name: str
    ) -> dict:
        """Execute the handoff function.
        
        Args:
            context: Current execution context
            reason: Reason for the handoff
            agent_name: Name of the agent to hand off to
            
        Returns:
            Dict containing handoff result and target agent
            
        Raises:
            ValueError: If target agent not found
        """
        # Find target agent
        target_agent = next(
            (a for a in self.possible_agents if a.name == agent_name),
            None
        )
        
        if not target_agent:
            raise ValueError(f"Agent {agent_name} not found in possible agents")
            
        # Store handoff information in context
        context.set("last_handoff_reason", reason)
        context.set("last_handoff_agent", agent_name)
        
        return {
            "message": f"Handing off to agent {agent_name} because {reason}",
            "target_agent": target_agent
        }


class HandoffAgent(Agent):
    """Agent capable of handing off tasks to other agents.
    
    This agent evaluates the current context and determines which
    specialized agent should handle the task next.
    
    Example:
        handoff_agent = HandoffAgent(
            name="router",
            possible_agents=[agent1, agent2],
            amount_of_agents=1,
            duplicates_allowed=False
        )
    """
    
    def __init__(
        self,
        name: str,
        possible_agents: List[Agent],
        amount_of_agents: int = 1,
        duplicates_allowed: bool = False,
        single_agent_fanout: bool = False,
        instructions: Optional[str] = None,
        context: Optional[Context] = None,
    ) -> None:
        """Initialize the handoff agent.
        
        Args:
            name: Agent name
            possible_agents: List of agents that can be handed off to
            amount_of_agents: Number of agents to hand off to
            duplicates_allowed: Whether same agent can be selected multiple times
            single_agent_fanout: Whether to fan out to single agent multiple times
            instructions: Custom instructions (uses default if None)
            context: Shared context (creates new if None)
        """
        # Create handoff function
        handoff_function = HandoffFunction(possible_agents)
        
        # Generate default instructions if none provided
        if instructions is None:
            instructions = self._generate_instructions(possible_agents)
            
        super().__init__(
            name=name,
            instructions=instructions,
            functions=[handoff_function],
            context=context
        )
        
        # Store handoff configuration
        self.context.set("amount_of_agents", amount_of_agents)
        self.context.set("duplicates_allowed", duplicates_allowed)
        self.context.set("single_agent_fanout", single_agent_fanout)
        
    def _generate_instructions(self, possible_agents: List[Agent]) -> str:
        """Generate default instructions based on available agents.
        
        Args:
            possible_agents: List of available agents
            
        Returns:
            Generated instruction string
        """
        instructions = [
            "You are a routing agent that hands off tasks to specialized agents.",
            "\nAvailable agents:"
        ]
        
        for agent in possible_agents:
            instructions.append(
                f"\n- {agent.name}: {agent.get_instructions()}"
            )
            
        instructions.append(
            "\nAnalyze the task and choose the most appropriate agent."
        )
        
        return "".join(instructions)
        
    async def handle_handoff_result(self, result: dict) -> None:
        """Handle the result of a handoff operation.
        
        Args:
            result: Result from handoff function execution
        """
        target_agent = result["target_agent"]
        
        # Dispatch handoff event
        await self.event_dispatcher.dispatch(
            Event(
                type=EventType.AGENT_HANDOFF,
                data={
                    "from_agent": self.name,
                    "to_agent": target_agent.name,
                    "reason": self.context.get("last_handoff_reason")
                },
                source=self.name
            )
        )
        
        # Update handoff history in context
        handoff_history = self.context.get("handoff_history", [])
        handoff_history.append({
            "from": self.name,
            "to": target_agent.name,
            "reason": self.context.get("last_handoff_reason")
        })
        self.context.set("handoff_history", handoff_history)
