"""provides infinite memory."""

import uuid

from zep_python.client import Zep
from zep_python.types import Message as ZepMessage, SessionSearchResult

from schwarm.provider.base import BaseEventHandleProvider
from schwarm.provider.base.base_event_handle_provider import InjectionTask
from schwarm.provider.models.zep_config import ZepConfig


class ZepProvider(BaseEventHandleProvider):
    """Knowledge graph provider with infinite memory."""

    config: ZepConfig
    zap_service: Zep

    def initialize(self, randomize_user_id: bool = False) -> None:
        """Initializes the provider."""
        self.zap_service = Zep(api_key=self.config.zep_api_key, base_url=self.config.zep_api_key)

        self.user_id = self.agent.name + str(uuid.uuid4()) if randomize_user_id else self.agent.name
        self.session_id = str(uuid.uuid4())

        self.user = self.zap_service.user.get(user_id=self.user_id)
        if not self.user:
            self.zap_service.user.add(user_id=self.user_id)

        self.zap_service.memory.add_session(
            user_id=self.user_id,
            session_id=self.session_id,
        )

    def split_text(self, text: str | None, max_length: int = 1000) -> list:
        """Split text into smaller chunks."""
        result = []
        if not text:
            return result
        if len(text) <= max_length:
            return [ZepMessage(role="user", content=text)]
        for i in range(0, len(text), max_length):
            result.append(ZepMessage(role="user", content=text[i : i + max_length], role_type="user"))
        return result

    def add_to_memory(self, text: str) -> None:
        """Add text to memory."""
        messages = self.split_text(text)
        self.zap_service.memory.add(session_id=self.session_id, messages=messages)

    def search_memory(self, query: str) -> list[SessionSearchResult]:
        response = self.zap_service.memory.search_sessions(
            text=query,
            user_id=self.user_id,
            search_scope="facts",
            min_fact_rating=self.config.min_fact_rating,
        )
        if not response.results:
            return []
        return response.results

    def handle_on_instruct(self) -> InjectionTask | None:
        """Handle the on_instruct event."""
        memory = self.zap_service.memory.get("user_agent", min_rating=self.config.min_fact_rating)
        facts = f"\n\n\nRelevant facts about the story so far:\n{memory.relevant_facts}"
        return InjectionTask(target="instruction", value=facts)

    def handle_post_message_completion(self) -> None:
        """Handle post message completion to update context."""
        if self.config.on_completion_save_completion_to_memory:
            self.zap_service.memory.add(
                session_id=self.session_id, messages=self.split_text(self.get_context().current_message.content)
            )
