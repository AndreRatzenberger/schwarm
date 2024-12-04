"""Provider for the Lite LLM API."""

import asyncio
import json
from typing import TYPE_CHECKING, Any, cast

import litellm
from litellm import BaseModel, Field, completion, completion_cost, token_counter  # type: ignore
from litellm.caching.caching import Cache
from litellm.integrations.custom_logger import CustomLogger
from loguru import logger

from schwarm.manager.stream_manager import StreamManager, StreamToolManager
from schwarm.models.message import Message, MessageInfo
from schwarm.provider.base.base_llm_provider import BaseLLMProvider, BaseLLMProviderConfig
from schwarm.utils.file import temporary_env_vars

if TYPE_CHECKING:
    pass


class EnvironmentConfig(BaseModel):
    """Configuration for environment variable handling.

    Attributes:
        override: Whether to override environment variables
        variables: Environment variables to override (excluding API_KEY)
    """

    override: bool = Field(default=False, description="Controls whether environment variables should be overridden")
    variables: dict[str, str] = Field(
        default_factory=dict, description="Environment variables to override (excluding API_KEY)"
    )


class LLMConfig(BaseLLMProviderConfig):
    """Configuration for the LiteLLM provider.

    This configuration class manages settings for the LiteLLM provider,
    including environment variable handling and feature flags.

    See LiteLLM documentation for model-specific environment variable requirements.

    Attributes:
        environment: Environment variable configuration
        enable_cache: Whether to enable response caching
        enable_debug: Whether to enable debug mode
        enable_mocking: Whether to enable mock responses
    """

    environment: EnvironmentConfig = Field(
        default_factory=EnvironmentConfig, description="Environment variable configuration"
    )
    enable_cache: bool = Field(default=False, description="Enables response caching for improved performance")
    enable_debug: bool = Field(default=True, description="Enables debug mode for detailed logging")
    enable_mocking: bool = Field(default=False, description="Enables mock responses for testing purposes")
    sleep_on_cache_hit: float = Field(default=5, description="Sleep time in seconds when cache hit is detected")
    streaming: bool = Field(default=False, description="Enable streaming completion")


class LiteLLMError(Exception):
    """Base exception for LiteLLM provider errors."""

    pass


class ConfigurationError(LiteLLMError):
    """Raised when there's an error in the provider configuration."""

    pass


class CompletionError(LiteLLMError):
    """Raised when there's an error during completion."""

    pass


class ConnectionError(LiteLLMError):
    """Raised when there's an error connecting to the LLM service."""

    pass


class LoggingHandler(CustomLogger):
    """Custom handler for logging LiteLLM events.

    This handler captures and formats success events from LiteLLM operations,
    providing detailed logging for monitoring and debugging purposes.
    """

    async def async_log_success_event(
        self, kwargs: dict[str, Any], response_obj: Any, start_time: float, end_time: float
    ) -> None:
        """Log a success event with detailed information.

        Args:
            kwargs: The arguments passed to the LLM call
            response_obj: The response from the LLM service
            start_time: When the request started
            end_time: When the request completed
        """
        # get random number between 1 and sleep on cache hit
        duration = end_time - start_time
        logger.info(f"LiteLLM request completed in {duration:.2f}s")
        logger.info(f"Cache hit: {kwargs.get('cache_hit', False)}")
        if "messages" in kwargs:
            logger.debug(f"Request messages: {kwargs['messages']}")


class LLMProvider(BaseLLMProvider):
    """Provider for the Lite LLM API.

    This provider implements the LLMProvider interface using the LiteLLM library,
    which supports multiple LLM providers through a unified interface.

    Attributes:
        provider_name: Identifier for this provider type
        config: Provider configuration
    """

    _provider_id: str = Field(default="lite_llm", description="Provider ID")

    def __init__(self, config: LLMConfig, **data) -> None:
        """Initialize the Lite LLM provider.

        Args:
            config: Provider configuration
            agent: Optional agent context

        Raises:
            ConfigurationError: If the configuration is invalid
        """
        self.config = config
        self.streaming = config.streaming
        self.sleep_on_cache_hit = config.sleep_on_cache_hit
        if config.enable_cache:
            self._setup_caching()
        litellm.drop_params = True
        super().__init__(config=config)
        self.initialize()

    def initialize(self) -> None:
        """Initialize the provider.

        This method sets up caching, logging, and debugging based on configuration.
        It also validates the connection to ensure the provider is properly configured.

        Raises:
            ConfigurationError: If the connection test fails
            ConnectionError: If unable to connect to the LLM service
        """
        try:
            if not self.test_connection():
                raise ConfigurationError("Failed to connect to LLM service")

            config = cast(LLMConfig, self.config)

            if config.enable_debug:
                litellm.set_verbose = True  # type: ignore
                logger.info("Debug mode enabled for LiteLLM provider")

        except Exception as e:
            raise ConnectionError(f"Failed to initialize provider: {e!s}") from e

    def _setup_caching(self) -> None:
        """Configure caching for the provider.

        Sets up disk-based caching and logging handlers for cache operations.
        """
        litellm.cache = Cache(type="disk", disk_cache_dir=".llm_cache")  # type: ignore
        customHandler_caching = LoggingHandler()
        litellm.callbacks = [customHandler_caching]
        logger.info("Caching enabled for LiteLLM provider")

    def test_connection(self) -> bool:
        """Test connection to Lite LLM provider.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            msg = Message(role="user", content="Test connection")
            self.complete(messages=[msg], streaming=False)
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e!s}")
            return False

    def _prepare_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Prepare messages for LiteLLM API.

        Args:
            messages: List of messages to prepare

        Returns:
            List of formatted message dictionaries
        """
        return [
            {
                "role": message.role,
                "content": message.content,
                "tool_calls": message.tool_calls,
                "tool_call_id": message.tool_call_id,
            }
            for message in messages
        ]

    def _create_completion_response(self, response: Any, model: str, message_list: list[dict[str, Any]]) -> Message:
        """Create a Message from a completion response."""
        try:
            choices = getattr(response, "choices", [])
            if not choices:
                choices = [{"message": {"content": "", "role": "assistant", "tool_calls": []}}]

            try:
                cost = completion_cost(completion_response=response)
            except Exception as e:
                logger.warning(f"Failed to calculate completion cost: {e}")
                cost = 0

            try:
                token_count = token_counter(model, messages=message_list)
            except Exception as e:
                logger.warning(f"Failed to count tokens: {e}")
                token_count = 0

            info = MessageInfo(token_counter=token_count, completion_cost=cost)

            choice = choices[0]
            message = getattr(choice, "message", {}) or {}
            if isinstance(message, dict):
                content = message.get("content", "")
                role = message.get("role", "assistant")
                tool_calls = message.get("tool_calls", [])
            else:
                content = getattr(message, "content", "")
                role = getattr(message, "role", "assistant")
                tool_calls = getattr(message, "tool_calls", [])

            return Message(
                content=content or "",
                role=role,  # type: ignore
                name=model,
                tool_calls=tool_calls,
                info=info,
                additional_info={"raw_response": response},
            )

        except Exception as e:
            logger.error(f"Error creating completion response: {e}")
            raise CompletionError(f"Failed to process LLM response: {e!s}")

    # async def _handle_streaming(self, response, messages: list[dict[str, Any]], model: str) -> Message:
    #     """Handle streaming response from LiteLLM."""
    #     chunks = []
    #     full_response = ""
    #     stream_manager = StreamManager()
    #     stream_tool_manager = StreamToolManager()
    #     tool_calls = []
    #     try:
    #         for part in response:
    #             time.sleep(0.1)
    #             if not part or not part.choices:
    #                 continue
    #             delta = part.choices[0].delta
    #             chunk = {"choices": [{"delta": {}}]}

    #             if delta and delta.content:
    #                 content = delta.content
    #                 # Process the content chunk as needed
    #                 if content:
    #                     logger.debug(f"Chunks content: {json.dumps(content, indent=2)}")
    #                     await stream_manager.write(content)
    #                     full_response += content
    #                     chunk["choices"][0]["delta"]["content"] = content

    #             elif delta and delta.function_call:
    #                 function_call_data = {
    #                     "name": delta.function_call.name,
    #                     "arguments": delta.function_call.arguments,
    #                 }
    #                 logger.debug(f"Chunks function_call_data: {json.dumps(function_call_data, indent=2)}")
    #                 await stream_tool_manager.write(
    #                     str(delta.function_call.arguments)
    #                 )  # Write function_call to the stream
    #                 chunk["choices"][0]["delta"]["function_call"] = function_call_data
    #             elif delta and delta.tool_calls:
    #                 tool_calls_list = []
    #                 for tool_call in delta.tool_calls:
    #                     tool_call_data = {
    #                         "id": tool_call.id,
    #                         "function": {
    #                             "name": tool_call.function.name,
    #                             "arguments": tool_call.function.arguments,
    #                         },
    #                     }
    #                     logger.debug(f"Chunks tool_call_data: {json.dumps(tool_call_data, indent=2)}")
    #                     tool_calls_list.append(tool_call_data)
    #                     await stream_tool_manager.write(str(tool_call.function.arguments))

    #                 chunk["choices"][0]["delta"]["tool_calls"] = tool_calls_list

    #             if chunk["choices"][0]["delta"]:
    #                 chunks.append(part)

    #     except Exception as e:
    #         logger.error(f"Error during streaming: {e}")
    #         raise CompletionError(f"Streaming failed: {e}") from e
    #     finally:
    #         await stream_manager.close()
    #         await stream_tool_manager.close()

    #     msg = litellm.stream_chunk_builder(chunks, messages=messages)

    #     return self._create_completion_response(msg, model, messages)

    async def _handle_streaming(self, response, messages: list[dict[str, Any]], model: str, agent_name: str) -> Message:
        """Handle streaming response from LiteLLM.

        Args:
            response: The streaming response from LiteLLM
            messages: List of message dictionaries
            model: The model name being used

        Returns:
            Message: A complete message built from all chunks

        Raises:
            CompletionError: If streaming fails
        """
        chunks = []
        full_response = ""
        stream_manager = None
        stream_tool_manager = None

        try:
            # Initialize stream managers
            stream_manager = StreamManager()
            stream_tool_manager = StreamToolManager()

            for part in response:
                if not part or not part.choices:
                    continue

                delta = part.choices[0].delta
                chunk = {"choices": [{"delta": {}}]}

                try:
                    # Handle content streaming
                    if delta and delta.content:
                        content = delta.content
                        if content:
                            logger.debug(f"Chunks content: {json.dumps(content, indent=2)}")
                            try:
                                await stream_manager.write(content, agent_name)
                                full_response += content
                                chunk["choices"][0]["delta"]["content"] = content
                            except Exception as e:
                                logger.error(f"Error writing content chunk: {e}")
                                # Continue processing even if one chunk fails

                    # Handle function call streaming
                    elif delta and delta.function_call:
                        function_call_data = {
                            "name": delta.function_call.name,
                            "arguments": delta.function_call.arguments,
                        }
                        logger.debug(f"Chunks function_call_data: {json.dumps(function_call_data, indent=2)}")
                        try:
                            await stream_tool_manager.write(str(delta.function_call.arguments), agent_name)
                            chunk["choices"][0]["delta"]["function_call"] = function_call_data
                        except Exception as e:
                            logger.error(f"Error writing function call chunk: {e}")
                            # Continue processing even if one chunk fails

                    # Handle tool calls streaming
                    elif delta and delta.tool_calls:
                        tool_calls_list = []
                        for tool_call in delta.tool_calls:
                            tool_call_data = {
                                "id": tool_call.id,
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                },
                            }
                            logger.debug(f"Chunks tool_call_data: {json.dumps(tool_call_data, indent=2)}")
                            tool_calls_list.append(tool_call_data)
                            try:
                                await stream_tool_manager.write(str(tool_call.function.arguments), agent_name)
                            except Exception as e:
                                logger.error(f"Error writing tool call chunk: {e}")
                                # Continue processing even if one chunk fails

                        chunk["choices"][0]["delta"]["tool_calls"] = tool_calls_list

                    if chunk["choices"][0]["delta"]:
                        chunks.append(part)

                except Exception as e:
                    logger.error(f"Error processing stream chunk: {e}")
                    # Continue processing other chunks even if one fails

                # Small delay to prevent overwhelming the stream
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            raise CompletionError(f"Streaming failed: {e}") from e

        finally:
            # Ensure both managers are properly closed
            if stream_manager:
                try:
                    await stream_manager.close()
                except Exception as e:
                    logger.error(f"Error closing stream manager: {e}")

            if stream_tool_manager:
                try:
                    await stream_tool_manager.close()
                except Exception as e:
                    logger.error(f"Error closing stream tool manager: {e}")

        # Build final message from chunks
        try:
            msg = litellm.stream_chunk_builder(chunks, messages=messages)
            return self._create_completion_response(msg, model, messages)
        except Exception as e:
            logger.error(f"Error building final message: {e}")
            raise CompletionError(f"Failed to build message from chunks: {e}")

    def _complete(
        self,
        messages: list[Message],
        override_model: str | None = None,
        tools: list[dict[str, Any]] = [],
        tool_choice: str = "",
        parallel_tool_calls: bool = True,
        agent_name: str = "",
        streaming: bool = True,
    ) -> Message:
        """Internal completion method."""
        import nest_asyncio

        nest_asyncio.apply()

        config = cast(LLMConfig, self.config)
        model = override_model or config.name
        message_list = self._prepare_messages(messages)

        try:
            completion_kwargs = {
                "model": model,
                "messages": message_list,
                "caching": config.enable_cache,
                "stream": config.streaming and streaming,
            }
            if tools:
                completion_kwargs.update(
                    {
                        "tools": tools,
                        "tool_choice": tool_choice,
                        "parallel_tool_calls": parallel_tool_calls,
                    }
                )

            if config.streaming and streaming:
                response = completion(**completion_kwargs)
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self._handle_streaming(response, message_list, model, agent_name))

            response = completion(**completion_kwargs)
            return_value = self._create_completion_response(response, model, message_list)
            # sm = StreamManager()
            # asyncio.run(sm.write(str(return_value.content), agent_name))
            return return_value

        except Exception as e:
            if isinstance(e, CompletionError):
                raise
            raise CompletionError(f"Completion failed: {e!s}") from e

    async def async_complete(
        self,
        messages: list[Message],
        override_model: str | None = None,
        tools: list[dict[str, Any]] = [],
        tool_choice: str = "",
        parallel_tool_calls: bool = True,
    ) -> Message:
        """Generate completion for given messages asynchronously.

        This method provides the same functionality as complete() but in an asynchronous manner.

        Args:
            messages: List of messages in the conversation
            override_model: Optional model to use instead of active_model
            tools: List of available tools
            tool_choice: The tool choice to use
            parallel_tool_calls: Whether to make tool calls in parallel

        Returns:
            Message: The completion response

        Raises:
            CompletionError: If the completion fails
            ValueError: If the input messages are invalid
        """
        # For now, we'll use the synchronous implementation
        # TODO: Implement proper async completion when litellm supports it
        return self.complete(
            messages=messages,
            override_model=override_model,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=parallel_tool_calls,
        )

    def complete(
        self,
        messages: list[Message],
        override_model: str | None = None,
        tools: list[dict[str, Any]] = [],
        tool_choice: str = "",
        parallel_tool_calls: bool = True,
        agent_name: str = "",
        streaming: bool = True,
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
            CompletionError: If the completion fails
            ValueError: If the input messages are invalid
        """
        if not messages:
            raise ValueError("At least one message is required")

        config = cast(LLMConfig, self.config)
        if config.environment.variables and config.environment.override:
            with temporary_env_vars(config.environment.variables):
                return self._complete(
                    messages=messages,
                    override_model=override_model,
                    tools=tools,
                    tool_choice=tool_choice,
                    parallel_tool_calls=parallel_tool_calls,
                    agent_name=agent_name,
                    streaming=streaming,
                )
        else:
            return self._complete(
                messages=messages,
                override_model=override_model,
                tools=tools,
                tool_choice=tool_choice,
                parallel_tool_calls=parallel_tool_calls,
                agent_name=agent_name,
                streaming=streaming,
            )
