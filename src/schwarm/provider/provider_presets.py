"""Some default provider presets for Schwarm."""

from schwarm.configs.telemetry_config import TelemetryConfig
from schwarm.provider.information_provider import InformationConfig
from schwarm.provider.litellm_provider import LiteLLMConfig

DEFAULT = [LiteLLMConfig(enable_cache=True, enable_debug=True), TelemetryConfig(), InformationConfig()]
