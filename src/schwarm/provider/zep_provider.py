"""Provider for infinite memory using Zep."""

import uuid

from loguru import logger
from pydantic import Field
from zep_python.client import Zep
from zep_python.types import Message as ZepMessage, SessionSearchResult

from schwarm.models.event import Event, EventType
from schwarm.models.provider_context import ProviderContextModel
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.base.base_provider import BaseProviderConfig


class ZepConfig(BaseProviderConfig):
    """Configuration for Zep memory provider."""

    user_id: str = Field(default="default_user", description="User ID for Zep service")
    zep_prompt: str = Field(default="", description="Prompt for Zep service")
    zep_api_key: str = Field(..., description="API key for Zep service")
    zep_api_url: str = Field(default="http://localhost:8000", description="URL for Zep service")
    min_fact_rating: float = Field(default=0.7, description="Minimum rating for facts to be considered")
    save_every_message: bool = Field(default=False, description="Whether to save every message to memory")
    on_completion_save_completion_to_memory: bool = Field(
        default=True, description="Whether to save completions to memory"
    )


class ZepProvider(BaseEventHandleProvider):
    """Knowledge graph provider with infinite memory."""

    def __init__(self, config: ZepConfig, **data):
        """Initialize the provider."""
        super().__init__(config, **data)
        self.config: ZepConfig = config
        self.zep_service: Zep | None = None
        self.user_id: str | None = None
        self.session_id: str | None = None
        self.initialize()

    def initialize(self):
        """Initialize Zep connection."""
        self.zep_service = Zep(api_key=self.config.zep_api_key, base_url=self.config.zep_api_url)

        self.user_id = self.config.user_id
        self.session_id = str(uuid.uuid4())

        self._setup_user()
        self._setup_session()

    def _setup_user(self) -> None:
        """Set up user in Zep."""
        if not self.zep_service or not self.user_id:
            raise ValueError("Zep service or user_id not initialized")

        try:
            user = self.zep_service.user.get(user_id=self.user_id)
            if not user:
                self.zep_service.user.add(user_id=self.user_id)
        except Exception:
            self.zep_service.user.add(user_id=self.user_id)

    def _setup_session(self) -> None:
        """Set up new session."""
        if not self.zep_service or not self.user_id or not self.session_id:
            raise ValueError("Zep service, user_id, or session_id not initialized")

        self.zep_service.memory.add_session(
            user_id=self.user_id,
            session_id=self.session_id,
        )

    def get_memory(self) -> str | None:
        """Get memory for the current session."""
        if not self.zep_service or not self.session_id:
            logger.error("Zep service or session_id not initialized")
            return None

        try:
            memory = self.zep_service.memory.get(self.session_id, min_rating=self.config.min_fact_rating)
            if memory:
                return f"{memory.relevant_facts}"
        except Exception as e:
            logger.error(f"Error fetching memory: {e}")
            return None

        return None

    def split_text(self, text: str | None, max_length: int = 1000) -> list[ZepMessage]:
        """Split text into smaller chunks."""
        result: list[ZepMessage] = []
        if not text:
            return result
        if len(text) <= max_length:
            return [ZepMessage(role="user", content=text, role_type="user")]
        for i in range(0, len(text), max_length):
            result.append(ZepMessage(role="user", content=text[i : i + max_length], role_type="user"))
        return result

    def add_to_memory(self, text: str) -> None:
        """Add text to memory."""
        if not self.zep_service or not self.session_id:
            logger.error("Zep service or session_id not initialized")
            return

        messages = self.split_text(text)
        self.zep_service.memory.add(session_id=self.session_id, messages=messages)

    def search_memory(self, query: str) -> list[SessionSearchResult]:
        """Search memory for a query."""
        if not self.zep_service or not self.user_id:
            logger.error("Zep service or user_id not initialized")
            return []

        response = self.zep_service.memory.search_sessions(
            text=query,
            user_id=self.user_id,
            search_scope="facts",
            min_fact_rating=self.config.min_fact_rating,
        )
        if not response.results:
            return []
        return response.results

    def enhance_instructions(self, provider_context: ProviderContextModel | None = None) -> str | None:
        """Add memory context to instructions."""
        if not self.zep_service or not self.session_id:
            logger.error("Zep service not initialized")
            return None

        try:
            memory = self.zep_service.memory.get(self.session_id, min_rating=self.config.min_fact_rating)
            if memory and memory.relevant_facts:
                return f"\n\nRelevant facts about the story so far:\n{memory.relevant_facts}"
        except Exception as e:
            logger.error(f"Error fetching memory: {e}")
            return None

        return None

    def save_completion(self, provider_context: ProviderContextModel | None = None) -> None:
        """Save completion to memory."""
        if not self.zep_service or not self.session_id:
            logger.error("Zep service or session_id not initialized")
            return

        if not self.config.on_completion_save_completion_to_memory:
            return

        if not provider_context or not provider_context.current_message:
            return

        for item in reversed(provider_context.message_history):
            if item.role == "user":
                message = item
                break

        zep_messages = self.split_text(message.content)

        try:
            self.zep_service.memory.add(session_id=self.session_id, messages=zep_messages)
        except Exception as e:
            logger.error(f"Error saving to memory: {e}")

    def complete(self, messages: list[str]) -> str:
        """Not implemented as this is primarily an event-based provider."""
        raise NotImplementedError("ZepProvider does not support direct completion")

    def handle_event(self, event: Event, context: ProviderContextModel) -> ProviderContextModel | None:
        """Handle an event."""
        if self.config.on_completion_save_completion_to_memory:
            if event.type == EventType.POST_MESSAGE_COMPLETION:
                self.save_completion(context)
        return None
