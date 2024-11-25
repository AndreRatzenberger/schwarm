"""Some default provider presets for Schwarm."""

from schwarm.provider.litellm_provider import LiteLLMConfig

DEFAULT = [LiteLLMConfig(enable_cache=True)]
