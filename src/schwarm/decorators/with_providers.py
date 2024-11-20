from collections.abc import Callable
from functools import wraps
from typing import (
    Any,
    Concatenate,  # for Python < 3.10
    ParamSpec,
    TypeVar,
)

from schwarm.models.types import Result
from schwarm.provider.base.base_provider import BaseProvider

P = ParamSpec("P")
R = TypeVar("R", bound=Result)


def with_providers(*provider_names: str) -> Callable:
    """Decorator to inject providers into tool functions.

    Example:
        @with_providers('zep', 'vector_store')
        def my_tool(providers: dict[str, BaseProvider],
                   context_variables: dict[str, Any],
                   some_arg: str) -> Result:
            zep = providers['zep']
            # ... rest of code
    """

    def decorator(func: Callable[Concatenate[dict[str, BaseProvider], P], R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(p: dict, context_variables: dict[str, Any], *args: P.args, **kwargs: P.kwargs) -> R:
            # Extract providers from context_variables
            providers = {}
            for name in provider_names:
                provider_key = f"{name}_provider"
                if provider_key not in context_variables:
                    raise ValueError(f"Required provider '{name}' not found in context")
                providers[name] = context_variables[provider_key]

            # Call original function with providers injected
            return func(providers, context_variables, *args, **kwargs)

        # Store provider requirements for introspection
        wrapper.required_providers = provider_names
        return wrapper

    return decorator
