"""Decorators for creating CLI-style functions."""

import inspect
from collections.abc import Callable
from typing import Any, TypeVar, cast

from ...context.context import Context
from .cli_function import CLIFunction
from .command import Parameter

T = TypeVar("T", bound=Callable[..., Any])


def cli_command(name: str | None = None, description: str | None = None, lazy: bool = False) -> Callable[[T], T]:
    """Decorator to mark a function as a CLI command.

    This decorator creates a CLIFunction from any callable. Parameters
    can be added using the cli_param decorator, or automatically derived
    from the function signature if lazy=True.

    Args:
        name: Optional name for the command (defaults to function name)
        description: Optional description (defaults to function docstring)
        lazy: If True, automatically create parameters from function signature

    Example:
        # Explicit parameter definition
        @cli_command(
            name="image-gen",
            description="Generate images from text"
        )
        @cli_param("-p", "prompt text", required=True)
        @cli_param("--style", "style to use", choices=["realistic", "anime"])
        async def generate_image(context: Context, p: str, style: str = "realistic") -> str:
            return f"Generated {style} image from prompt: {p}"

        # Lazy parameter creation from signature
        @cli_command(lazy=True)
        async def search(
            context: Context,
            query: str,  # Required parameter (no default)
            limit: int = 10,  # Optional parameter with default
            sort: str = "relevance"  # Optional parameter with default
        ) -> list[str]:
            '''Search for items in the database.

    Args:
                query: The search query
                limit: Maximum number of results
                sort: Sort order (relevance, date, etc.)
            '''
            pass
    """

    def decorator(func: T) -> T:
        func_description = description or func.__doc__ or "No description provided"

        # Get or create the parameters list
        if not hasattr(func, "_cli_params"):
            func._cli_params = []  # type: ignore

        # If lazy mode, create parameters from signature
        if lazy:
            sig = inspect.signature(func)
            doc = inspect.getdoc(func) or ""
            param_docs = _parse_docstring_args(doc)

            # Skip first parameter if it's context
            params = list(sig.parameters.items())
            if params and params[0][1].annotation == Context:
                params = params[1:]

            for param_name, param in params:
                # Get description from docstring if available
                param_desc = param_docs.get(param_name, f"{param_name} parameter")

                # Required if no default value
                required = param.default == inspect.Parameter.empty

                # Create parameter
                cli_param = Parameter(
                    flag=f"--{param_name}" if len(param_name) > 1 else f"-{param_name}",
                    description=param_desc,
                    required=required,
                )
                func._cli_params.append(cli_param)  # type: ignore

        # Create the CLIFunction
        cli_func = CLIFunction(
            name=name or func.__name__,
            implementation=func,
            description=func_description,
            parameters=func._cli_params,  # type: ignore
        )

        # Store the CLIFunction on the original function
        func._cli_function = cli_func  # type: ignore

        return cast(T, cli_func)

    return decorator


def cli_param(
    flag: str, description: str, required: bool = False, choices: list[str] | None = None
) -> Callable[[T], T]:
    """Decorator to add a CLI parameter to a function.

    This decorator must be used with the cli_command decorator.
    Parameters are added in the order they are decorated.

    Args:
        flag: The parameter flag (e.g., "-p", "--style")
        description: Description of the parameter
        required: Whether the parameter is required
        choices: Optional list of valid choices

    Example:
        @cli_command()
        @cli_param("-p", "prompt text", required=True)
        @cli_param("--style", "style to use", choices=["realistic", "anime"])
        async def generate_image(context: Context, p: str, style: str = "realistic") -> str:
            return f"Generated {style} image from prompt: {p}"
    """

    def decorator(func: T) -> T:
        # Create the parameter
        param = Parameter(flag=flag, description=description, required=required, choices=choices)

        # Get or create the parameters list
        if not hasattr(func, "_cli_params"):
            func._cli_params = []  # type: ignore

        # Add the parameter
        func._cli_params.append(param)  # type: ignore

        return func

    return decorator


def is_cli_function(func: Any) -> bool:
    """Check if a function has been decorated as a CLI function.

    Args:
        func: The function to check

    Returns:
        True if the function is a CLI function
    """
    return hasattr(func, "_cli_function") and isinstance(func, CLIFunction)


def get_cli_function(func: Any) -> CLIFunction | None:
    """Get the CLIFunction for a decorated function.

    Args:
        func: The decorated function

    Returns:
        The CLIFunction if the function is decorated, None otherwise
    """
    return getattr(func, "_cli_function", None) if is_cli_function(func) else None


def _parse_docstring_args(docstring: str) -> dict[str, str]:
    """Parse argument descriptions from a docstring.

    Args:
        docstring: The function's docstring

    Returns:
        Dictionary mapping parameter names to their descriptions
    """
    result = {}
    lines = docstring.split("\n")
    in_args = False
    current_arg = None

    for line in lines:
        line = line.strip()

        # Look for Args section
        if line.lower().startswith("args:"):
            in_args = True
            continue

        # Exit Args section if we hit another section
        if in_args and line and line.endswith(":"):
            in_args = False
            continue

        # Parse argument descriptions
        if in_args and line:
            if line[0].isspace():  # Continuation of previous arg
                if current_arg and line.strip():
                    result[current_arg] += " " + line.strip()
            else:  # New argument
                parts = line.split(":", 1)
                if len(parts) == 2:
                    current_arg = parts[0].strip()
                    result[current_arg] = parts[1].strip()

    return result
