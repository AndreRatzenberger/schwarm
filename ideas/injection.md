from enum import Enum
from typing import Generic, TypeVar, Union, Optional
from dataclasses import dataclass
from typing_extensions import TypeAlias

# Injection Types
class InjectionTarget(Enum):
    INSTRUCTION = "instruction"
    MESSAGE = "message"
    CONTEXT = "context"
    AGENT = "agent"
    TOOL = "tool"

# Typed injection data
@dataclass
class InstructionInjection:
    """Data to inject into instructions."""
    content: str
    position: Literal["prefix", "suffix", "replace"] = "suffix"

@dataclass
class MessageInjection:
    """Data to inject into message history."""
    content: str
    role: str = "system"

@dataclass
class ContextInjection:
    """Data to inject into context variables."""
    key: str
    value: Any

InjectionValue: TypeAlias = Union[
    InstructionInjection,
    MessageInjection,
    ContextInjection,
    Agent,  # for agent switches
    dict[str, Any]  # for tool modifications
]

@dataclass
class InjectionTask(Generic[T]):
    """Type-safe injection task."""
    target: InjectionTarget
    value: T

# Event data types for instruction-related events
@dataclass
class InstructionEventData:
    """Data available during instruction events."""
    current_instructions: str
    context_variables: dict[str, Any]
    agent: Agent

# Modern ZepProvider implementation
class ZepProvider(ModernEventHandleProvider):
    """Knowledge graph provider with infinite memory."""
    
    config: ZepConfig
    zep_service: Optional[Zep] = None
    
    def __init__(self, config: ZepConfig):
        super().__init__(config)
        self.user_id = None
        self.session_id = None
    
    @handles_event(EventType.START)
    def initialize(self, event: Event[dict[str, Any]]) -> None:
        """Initialize Zep connection with type safety."""
        self.zep_service = Zep(
            api_key=self.config.zep_api_key, 
            base_url=self.config.zep_api_key
        )
        
        self.user_id = event.payload['agent_id']
        self.session_id = str(uuid.uuid4())
        
        self._setup_user()
        self._setup_session()
    
    def _setup_user(self) -> None:
        """Set up user in Zep."""
        if not self.zep_service.user.get(user_id=self.user_id):
            self.zep_service.user.add(user_id=self.user_id)
    
    def _setup_session(self) -> None:
        """Set up new session."""
        self.zep_service.memory.add_session(
            user_id=self.user_id,
            session_id=self.session_id,
        )
    
    @handles_event(EventType.INSTRUCT)
    def enhance_instructions(self, 
                           event: Event[InstructionEventData]
                           ) -> Optional[InjectionTask[InstructionInjection]]:
        """Add memory context to instructions with type safety."""
        if not self.zep_service:
            logger.error("Zep service not initialized")
            return None
            
        try:
            memory = self.zep_service.memory.get(
                "user_agent", 
                min_rating=self.config.min_fact_rating
            )
            
            if memory.relevant_facts:
                return InjectionTask(
                    target=InjectionTarget.INSTRUCTION,
                    value=InstructionInjection(
                        content=f"\n\nRelevant facts about the story so far:\n{memory.relevant_facts}",
                        position="suffix"
                    )
                )
        except Exception as e:
            logger.error(f"Error fetching memory: {e}")
            return None
            
        return None
    
    @handles_event(EventType.MESSAGE_COMPLETION)
    def save_completion(self, 
                       event: Event[MessageCompletionData]
                       ) -> None:
        """Save completion to memory with type safety."""
        if not self.zep_service or not self.config.on_completion_save_completion_to_memory:
            return
            
        message = event.payload.messages[-1]
        messages = self.split_text(message.content)
        
        try:
            self.zep_service.memory.add(
                session_id=self.session_id, 
                messages=messages
            )
        except Exception as e:
            logger.error(f"Error saving to memory: {e}")

# In your Schwarm class
class Schwarm:
    def _handle_injection(self, 
                         injection: Optional[InjectionTask], 
                         context: dict[str, Any]) -> None:
        """Handle injection tasks with type safety."""
        if not injection:
            return
            
        if injection.target == InjectionTarget.INSTRUCTION:
            value: InstructionInjection = injection.value
            if value.position == "suffix":
                context["current_instructions"] += value.content
            elif value.position == "prefix":
                context["current_instructions"] = value.content + context["current_instructions"]
            else:  # replace
                context["current_instructions"] = value.content
                
        elif injection.target == InjectionTarget.MESSAGE:
            value: MessageInjection = injection.value
            context["messages"].append(Message(
                role=value.role,
                content=value.content
            ))
            
        elif injection.target == InjectionTarget.CONTEXT:
            value: ContextInjection = injection.value
            context["context_variables"][value.key] = value.value
            
        elif injection.target == InjectionTarget.AGENT:
            # Handle agent switch
            context["current_agent"] = injection.value
            
    def _trigger_provider_event(self, 
                              event_type: EventType, 
                              payload: Any,
                              context: dict[str, Any]) -> None:
        """Trigger event and handle injections."""
        event = Event(type=event_type, payload=payload)
        
        for provider in self._get_providers():
            try:
                injection = provider.handle_event(event)
                self._handle_injection(injection, context)
            except Exception as e:
                logger.error(f"Error in provider {provider}: {e}")