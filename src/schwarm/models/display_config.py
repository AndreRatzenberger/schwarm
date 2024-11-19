"""Provider configuration model."""

from pydantic import BaseModel, Field


class DisplayConfig(BaseModel):
    """Configuration for a rendering service.

    Attributes:
        print_function_calls: display function calls
        wait_for_user_input_on_function_calls: If the process stops and waits for user input on function calls
    """

    show_function_calls: bool = Field(default=False, description="display function calls")
    function_calls_wait_for_user_input: bool = Field(
        default=False, description="If the process stops and waits for user input on function calls"
    )
    function_calls_print_context_variables: bool = Field(
        default=False, description="Print context variables on function calls"
    )
    show_instructions: bool = Field(default=False, description="Show instructions")
    instructions_wait_for_user_input: bool = Field(
        default=False, description="If the process stops and waits for user input on instructions"
    )
    show_budget: bool = Field(default=False, description="Show budget (overrides agent budget display settings)")
    show_budget_table: bool = Field(default=False, description="Show budget table (needs every agent to be registered)")
    max_length: int = Field(default=-1, description="Maximum length of the output. -1 for unlimited")
