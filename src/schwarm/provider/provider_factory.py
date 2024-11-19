"""Factory for creating providers."""

from loguru import logger

from schwarm.models.types import Agent
from schwarm.provider.base.base_llm_provider import BaseLLMProvider
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.litellm_provider import LiteLLMProvider
from schwarm.provider.models.base_provider_config import BaseProviderConfig
from schwarm.provider.models.lite_llm_config import LiteLLMConfig
from schwarm.provider.zep_provider import ZepProvider


class ProviderFactory:
    """Factory for creating providers.

    This class handles provider creation and registration without managing state.
    Provider lifecycle management is handled by the Agent class.
    """

    def __init__(self):
        """Initialize the provider factory."""
        self._provider_registry: dict[str, type[BaseProvider]] = {
            "lite_llm": LiteLLMProvider,
            "zep": ZepProvider,
        }

    def register_provider(self, name: str, provider_class: type[BaseProvider]) -> None:
        """Register a new provider type.

        Args:
            name: Name to register the provider under
            provider_class: Provider class to register
        """
        self._provider_registry[name] = provider_class
        logger.debug(f"Registered provider type: {name}")

    def create_provider(self, config: BaseProviderConfig, agent: Agent | None = None) -> BaseProvider | None:
        """Create a provider instance based on configuration.

        Args:
            config: Provider configuration
            agent: Optional agent context

        Returns:
            Created provider instance or None if creation fails
        """
        provider_class = self._provider_registry.get(config.provider_name)
        if not provider_class:
            logger.warning(f"No provider class registered for {config.provider_name}")
            return None

        try:
            if issubclass(provider_class, BaseLLMProvider):
                if not agent:
                    raise ValueError("Agent required for LLM provider creation")
                if isinstance(config, LiteLLMConfig):
                    return provider_class(agent.model, config)  # type: ignore
            if agent:
                return provider_class(agent, config)
            return None
        except Exception as e:
            logger.error(f"Failed to create provider {config.provider_name}: {e}")
            return None
