"""provides infinite memory."""

import uuid

from zep_python.client import Zep

from schwarm.provider.base import BaseEventHandleProvider
from schwarm.provider.models.zep_config import ZepConfig


class ZepProvider(BaseEventHandleProvider):
    """Knowledge graph provider with infinite memory."""

    config: ZepConfig
    zap_service: Zep

    def initialize(self, randomize_user_id: bool = False) -> None:
        """Initializes the provider."""
        self.zap_service = Zep(api_key=self.config.zep_api_key, base_url=self.config.zep_api_key)

        user_id = self.agent.name + str(uuid.uuid4()) if randomize_user_id else self.agent.name
        session_id = str(uuid.uuid4())

        user = self.zap_service.user.get(user_id=user_id)
        if not user:
            self.zap_service.user.add(user_id=user_id)

        self.zap_service.memory.add_session(
            user_id=user_id,
            session_id=session_id,
        )

    def on_start(self):
        super().on_start()

    def on_handoff(self, next_agent):
        super().on_handoff(next_agent)

    def on_message_completion(self):
        super().on_message_completion()

    def on_tool_execution(self):
        super().on_tool_execution()

    def on_post_message_completion(self):
        super().on_post_message_completion()

    def on_post_tool_execution(self):
        super().on_post_tool_execution()
