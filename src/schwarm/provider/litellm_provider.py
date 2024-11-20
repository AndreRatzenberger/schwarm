"""Provider for the Lite LLM API."""

from typing import Any

import litellm
from litellm import completion, completion_cost, token_counter  # type: ignore
from litellm.caching.caching import Cache
from litellm.integrations.custom_logger import CustomLogger
from loguru import logger

from schwarm.models.message import Message, MessageInfo
from schwarm.models.types import Agent
from schwarm.provider.base import BaseLLMProvider
from schwarm.provider.models.lite_llm_config import LiteLLMConfig
from schwarm.utils.file import temporary_env_vars


class ConfigurationError(Exception):
    """Raised when there's an error in the provider configuration."""

    pass


class CompletionError(Exception):
    """Raised when there's an error during completion."""

    pass


class LoggingHandler(CustomLogger):
    """Custom handler for logging events."""

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):  # type: ignore
        """Log a success event."""
        logger.log("INFO", f"Success event: {kwargs}")
        logger.log("INFO", f"Value of Cache hit: {kwargs['cache_hit']}")


class LiteLLMProvider(BaseLLMProvider):
    """Provider for the Lite LLM API.

    This provider implements the LLMProvider interface using the LiteLLM library,
    which supports multiple LLM providers through a unified interface.

    Attributes:
        active_model: The currently active model identifier
        config: Provider configuration
    """

    provider_name: str = "lite_llm"
    _env_backup: dict[str, str] = {}

    def __init__(
        self,
        config: LiteLLMConfig,
        agent: Agent | None = None,
    ):
        """Initialize the Lite LLM provider.

        Args:
            config: Provider configuration
            agent: Optional agent context
        """
        super().__init__(agent, config) if agent else None

        self.config = config

        litellm.drop_params = True
        # Validate configuration

        if self.test_connection() is False:
            raise ConfigurationError("Invalid API key or connection to Lite LLM provider")

        self.enable_cache = config.enable_cache
        if self.enable_cache:
            litellm.cache = Cache(type="disk", disk_cache_dir=".llm_cache")  # type: ignore
            customHandler_caching = LoggingHandler()
            litellm.callbacks = [customHandler_caching]

        if config.enable_debug:
            litellm.set_verbose = True  # type: ignore

    def test_connection(self) -> bool:
        """Test connection to Lite LLM provider.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            msg = Message(role="user", content="Test connection")

            self.complete(messages=[msg])
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e!s}")
            return False

    # async def async_complete(
    #     self, messages: list[Message], override_model: str | None = None, stream: bool | None = False
    # ) -> Message:
    #     """Generate completion for given messages.

    #     Args:
    #         messages: List of messages in the conversation
    #         override_model: Optional model to use instead of active_model
    #         stream: Whether to stream the response

    #     Returns:
    #         Message: The completion response

    #     Raises:
    #         CompletionError: If the completion fails or returns invalid format
    #         ValueError: If the input messages are invalid
    #     """
    #     if not messages:
    #         raise ValueError("At least one message is required")
    #     try:
    #         model = override_model or self.active_model
    #         message_list = [message.model_dump() for message in messages]
    #         response = await acompletion(model=model, messages=message_list, stream=stream, caching=self.enable_cache)
    #         choices = getattr(response, "choices", None)
    #         cost = completion_cost(completion_response=response)
    #         token_count = token_counter(model, messages=message_list)

    #         info = MessageInfo(token_counter=token_count, completion_cost=cost)

    #         if not choices:
    #             raise CompletionError("Invalid response format from LLM service")

    #         choice = choices[0]
    #         model_extra = getattr(choice, "model_extra", {})
    #         message = model_extra.get("message", {})

    #         return Message(
    #             content=message.get("content", ""),
    #             role=message.get("role", "assistant"),
    #             name=self.active_model,
    #             info=info,
    #         )
    #     except Exception as e:
    #         if isinstance(e, CompletionError):
    #             raise
    #         raise CompletionError(f"Completion failed: {e!s}") from e

    def _complete(
        self,
        messages: list[Message],
        override_model: str | None = None,
        tools: list[dict[str, Any]] = [],
        tool_choice: str = "",
        parallel_tool_calls: bool = True,
    ) -> Message:
        if not messages:
            raise ValueError("At least one message is required")
        if isinstance(self.config, LiteLLMConfig):
            active_model = self.config.model_id
        try:
            model = override_model or active_model
            # Convert messages to simple role/content format
            message_list = [
                {
                    "role": message.role,
                    "content": message.content,
                    "tool_calls": message.tool_calls,
                    "tool_call_id": message.tool_call_id,
                }
                for message in messages
            ]
            if tools:
                response = completion(
                    model=model,
                    messages=message_list,
                    tools=tools,
                    tool_choice=tool_choice,
                    parallel_tool_calls=parallel_tool_calls,
                    caching=self.enable_cache,
                )
            else:
                response = completion(model=model, messages=message_list, caching=self.enable_cache)
            choices = getattr(response, "choices", None)

            try:
                cost = completion_cost(completion_response=response)
            except Exception:
                cost = 0

            token_count = token_counter(model, messages=message_list)

            info = MessageInfo(token_counter=token_count, completion_cost=cost)

            if not choices:
                raise CompletionError("Invalid response format from LLM service")

            choice = choices[0]
            model_extra = getattr(choice, "model_extra", {})
            message = model_extra.get("message", {})

            tool_calls = message.get("tool_calls", [])

            return Message(
                content=message.get("content", ""),
                role=message.get("role", "assistant"),
                name=active_model,
                tool_calls=tool_calls,
                info=info,
                additional_info={"raw_response": response},
            )
        except Exception as e:
            if isinstance(e, CompletionError):
                raise
            raise CompletionError(f"Completion failed: {e!s}") from e

    def complete(
        self,
        messages: list[Message],
        override_model: str | None = None,
        tools: list[dict[str, Any]] = [],
        tool_choice: str = "",
        parallel_tool_calls: bool = True,
    ) -> Message:
        """Generate completion for given messages.

        Args:
            messages: List of messages in the conversation
            override_model: Optional model to use instead of active_model
            tools: List of available tools
            tool_choice: The tool choice to use
            parallel_tool_calls: Whether to make tool calls in parallel

        Returns:
            Message: The completion response

        Raises:
            CompletionError: If the completion fails or returns invalid format
            ValueError: If the input messages are invalid
        """
        if not messages:
            raise ValueError("At least one message is required")

        if isinstance(self.config, LiteLLMConfig) and self.config.env_vars and self.config.env_var_override:
            with temporary_env_vars(self.config.env_vars):
                return self._complete(
                    messages=messages,
                    override_model=override_model,
                    tools=tools,
                    tool_choice=tool_choice,
                    parallel_tool_calls=parallel_tool_calls,
                )
        else:
            return self._complete(
                messages=messages,
                override_model=override_model,
                tools=tools,
                tool_choice=tool_choice,
                parallel_tool_calls=parallel_tool_calls,
            )
