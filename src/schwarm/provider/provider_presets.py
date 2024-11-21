"""Some default provider presets for Schwarm."""

from schwarm.provider.debug_provider import DebugConfig
from schwarm.provider.litellm_provider import LiteLLMConfig

DEFAULT = [LiteLLMConfig(enable_cache=True, enable_debug=True), DebugConfig()]
