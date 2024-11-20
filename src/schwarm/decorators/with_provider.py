from collections.abc import Callable
from functools import wraps
from typing import Any, Concatenate, ParamSpec, TypedDict, TypeVar

from schwarm.models.types import Result
from schwarm.provider.litellm_provider import LiteLLMProvider
from schwarm.provider.provider_manager import ProviderManager
from schwarm.provider.zep_provider import ZepProvider

# Type variables for generic function signatures
P = ParamSpec("P")
R = TypeVar("R", bound=Result)


# Provider type mapping
class ProviderMap(TypedDict, total=False):
    """Type-safe provider mapping.

    Add your provider types here for type checking:
    zep: ZepProvider
    vector_store: VectorStoreProvider
    litellm: LiteLLMProvider
    etc.
    """

    zep: "ZepProvider"

    litellm: "LiteLLMProvider"


def with_providers(*provider_names: str) -> Callable:
    """Decorator to inject providers into tool functions.

    Example:
        @with_providers('zep', 'vector_store')
        def search_memory(
            providers: ProviderMap,
            context_variables: dict[str, Any],
            query: str
        ) -> Result:
            zep = providers['zep']  # Fully typed
            vector_store = providers['vector_store']  # Fully typed

            # Use providers with full IDE support
            memory_results = zep.search_memory(query)
            vector_results = vector_store.search(query)
            return Result(...)
    """

    def decorator(
        func: Callable[Concatenate[ProviderMap, dict[str, Any], P], R],
    ) -> Callable[Concatenate[ProviderMap, dict[str, Any], P], R]:
        # Store provider requirements for introspection
        func.required_providers = provider_names

        @wraps(func)
        def wrapper(pmap: ProviderMap, context_variables: dict[str, Any], *args: P.args, **kwargs: P.kwargs) -> R:
            if "agent_id" not in context_variables:
                raise ValueError("agent_id must be in context_variables")

            agent_id = context_variables["agent_id"]
            manager = ProviderManager()

            # Get providers with type safety
            providers: ProviderMap = {}
            for name in provider_names:
                provider = manager.get_provider(agent_id, name)
                if provider is None:
                    raise ValueError(f"Required provider '{name}' not found for agent {agent_id}")
                providers[name] = provider

            # Call original function with providers
            return func(providers, context_variables, *args, **kwargs)

        return wrapper

    return decorator
