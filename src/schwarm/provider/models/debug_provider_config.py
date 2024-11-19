"""Config for the debug provider."""

from pydantic import Field

from schwarm.provider.models import BaseEventHandleProviderConfig


class DebugProviderConfig(BaseEventHandleProviderConfig):
    """Configuration for the debug provider.

    This configuration includes all display and logging settings,
    controlling what information is shown to the user and how.
    """

    show_instructions: bool = Field(default=True, description="Whether to show agent instructions")
    instructions_wait_for_user_input: bool = Field(
        default=True, description="Whether to wait for user input after showing instructions"
    )
    show_function_calls: bool = Field(default=True, description="Whether to show function calls")
    function_calls_wait_for_user_input: bool = Field(
        default=True, description="Whether to wait for user input after showing function calls"
    )
    function_calls_print_context_variables: bool = Field(
        default=True, description="Whether to print context variables with function calls"
    )
    show_budget: bool = Field(default=True, description="Whether to show budget information")
    max_length: int = Field(default=-1, description="Maximum length for displayed text (-1 for no limit)")
    save_logs: bool = Field(default=True, description="Whether to save logs to files")

    def __init__(self, **data):
        """Initialize the debug provider configuration."""
        super().__init__(
            _provider_type="event",  # Debug provider is an event handler
            provider_name="debug",
            provider_lifecycle="scoped",
            **data,
        )
