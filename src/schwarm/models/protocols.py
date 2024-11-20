from typing import Any, Protocol, TypedDict, runtime_checkable

from schwarm.models.types import Result
from schwarm.provider.litellm_provider import LiteLLMProvider
from schwarm.provider.zep_provider import ZepProvider


class ProviderMap(TypedDict, total=False):
    """Type-safe provider mapping."""

    zep: "ZepProvider"
    litellm: "LiteLLMProvider"
    # Add other providers as needed


@runtime_checkable
class ToolFunction(Protocol):
    """Protocol for tool functions to enable type checking."""

    required_providers: tuple[str, ...]

    def __call__(self, context_variables: dict[str, Any], *args: Any, **kwargs: Any) -> Result: ...
