"""Some default provider presets for Schwarm."""

from schwarm.provider.budget_provider import BudgetConfig
from schwarm.provider.debug_provider import DebugConfig
from schwarm.provider.litellm_provider import LiteLLMConfig
from schwarm.provider.web_debug_provider import WebDebugConfig

DEFAULT = [LiteLLMConfig(enable_cache=True, enable_debug=True), DebugConfig(), BudgetConfig(), WebDebugConfig()]

DEFAULT_JUPYTER = [
    LiteLLMConfig(enable_cache=True, enable_debug=True),
    DebugConfig(
        show_budget=False,
        show_function_calls=False,
        show_instructions=False,
        instructions_wait_for_user_input=False,
        function_calls_wait_for_user_input=False,
    ),
    BudgetConfig(),
]
