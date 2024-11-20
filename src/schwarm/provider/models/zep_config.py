"""Config for the zep provider."""

from schwarm.provider.models import BaseEventHandleProviderConfig


class ZepConfig(BaseEventHandleProviderConfig):
    """Configuration for the Zep provider."""

    zep_api_key: str = "zepzep"
    zep_url: str = "http://localhost:8000"
    min_fact_rating: float = 0.3
    on_interaction_add_result_to_instructions: bool = True
    on_completion_save_completion_to_memory: bool = True
    on_tool_execution_save_memory: bool = True
