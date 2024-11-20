"""Provider for infinite memory using Zep."""

import uuid
from typing import Any

from loguru import logger
from zep_python.client import Zep
from zep_python.types import Message as ZepMessage, SessionSearchResult

from schwarm.events.event_types import EventType
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.zep_config import ZepConfig


class ZepProvider(BaseEventHandleProvider):
    """Knowledge graph provider with infinite memory."""

    def __init__(self, config: ZepConfig):
        """Initialize the provider."""
        super().__init__(config)
        self.config: ZepConfig = config
        self.zep_service: Zep | None = None
        self.user_id: str | None = None
        self.session_id: str | None = None

    def set_up(self) -> None:
        """Configure for both external use and event handling."""
        # Allow use in tools
        self.external_use = True

        # Set up event handlers
        self.internal_use = {
            EventType.START: [self.initialize],
            EventType.INSTRUCT: [self.enhance_instructions],
            EventType.MESSAGE_COMPLETION: [self.save_completion],
        }

    def initialize(self, **kwargs: Any) -> None:
        """Initialize Zep connection."""
        self.zep_service = Zep(api_key=self.config.zep_api_key, base_url=self.config.zep_api_key)

        randomize_user_id = kwargs.get("randomize_user_id", False)
        self.user_id = f"user_{uuid.uuid4()!s}" if randomize_user_id else "default_user"
        self.session_id = str(uuid.uuid4())

        self._setup_user()
        self._setup_session()

    def _setup_user(self) -> None:
        """Set up user in Zep."""
        if not self.zep_service or not self.user_id:
            raise ValueError("Zep service or user_id not initialized")

        user = self.zep_service.user.get(user_id=self.user_id)
        if not user:
            self.zep_service.user.add(user_id=self.user_id)

    def _setup_session(self) -> None:
        """Set up new session."""
        if not self.zep_service or not self.user_id or not self.session_id:
            raise ValueError("Zep service, user_id, or session_id not initialized")

        self.zep_service.memory.add_session(
            user_id=self.user_id,
            session_id=self.session_id,
        )

    def split_text(self, text: str | None, max_length: int = 1000) -> list[ZepMessage]:
        """Split text into smaller chunks."""
        result: list[ZepMessage] = []
        if not text:
            return result
        if len(text) <= max_length:
            return [ZepMessage(role="user", content=text)]
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

    def enhance_instructions(self, **kwargs: Any) -> str | None:
        """Add memory context to instructions."""
        if not self.zep_service:
            logger.error("Zep service not initialized")
            return None

        try:
            memory = self.zep_service.memory.get("user_agent", min_rating=self.config.min_fact_rating)
            if memory.relevant_facts:
                return f"\n\nRelevant facts about the story so far:\n{memory.relevant_facts}"
        except Exception as e:
            logger.error(f"Error fetching memory: {e}")
            return None

        return None

    def save_completion(self, **kwargs: Any) -> None:
        """Save completion to memory."""
        if not self.zep_service or not self.session_id:
            logger.error("Zep service or session_id not initialized")
            return

        if not self.config.on_completion_save_completion_to_memory:
            return

        messages = kwargs.get("messages", [])
        if not messages:
            return

        message = messages[-1]
        zep_messages = self.split_text(message.content)

        try:
            self.zep_service.memory.add(session_id=self.session_id, messages=zep_messages)
        except Exception as e:
            logger.error(f"Error saving to memory: {e}")

    def complete(self, messages: list[str]) -> str:
        """Not implemented as this is primarily an event-based provider."""
        raise NotImplementedError("ZepProvider does not support direct completion")
