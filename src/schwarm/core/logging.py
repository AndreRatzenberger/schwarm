"""Logging utilities for Schwarm.

This module provides logging functionality and decorators for tracking function calls,
execution times, and handling exceptions. It uses the loguru library for logging
and includes color formatting for better visual distinction in console output.
"""

import enum
import functools
import inspect
import time
from collections.abc import Callable
from typing import Any, Literal, TypeVar, cast

from loguru import logger

from schwarm.utils.settings import APP_SETTINGS

# Set up logging to a file
logger.add(
    APP_SETTINGS.DATA_FOLDER + "/logs/debug.log", format="{time} {level} {message}", level="DEBUG", rotation="10 MB"
)


T = TypeVar("T")

# Valid log levels for loguru
LogLevel = Literal["trace", "debug", "info", "success", "warning", "error", "critical"]


class ConsoleColor(enum.StrEnum):
    """ANSI color codes for console output."""

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"
    RESET_COLOR = "\033[39m"


def truncate_string(text: str, max_length: int = 200) -> str:
    """Truncate a string if it exceeds the maximum length.

    Args:
        text: The string to truncate.
        max_length: Maximum length of the string before truncation.

    Returns:
        The original string if shorter than max_length, or a truncated version
        with ellipsis if longer.
    """
    return (
        text
        if (len(text) <= max_length or max_length == -1)
        else f"{text[:max_length]}...{ConsoleColor.YELLOW}(+{len(text) - max_length} chars){ConsoleColor.RESET_COLOR}"
    )


def setup_logging(
    is_logging_enabled: bool = True,
    log_level: LogLevel = "trace",
) -> None:
    """Set up logging with the specified log level.

    Args:
        log_level: The logging level to use ("trace", "debug", "info", "success",
                  "warning", "error", "critical"). Case-insensitive.

    Raises:
        ValueError: If an invalid log level is provided.
    """
    if not is_logging_enabled:
        # Disable logging
        logger.info("Disabling console logging")
        logger.remove()
        return
    logger.info("Setting up console logging")
    # Convert log level to lowercase and validate
    normalized_level = log_level.lower()
    if not hasattr(logger, normalized_level):
        valid_levels = ["trace", "debug", "info", "success", "warning", "error", "critical"]
        raise ValueError(f"Invalid log level: {log_level}. Valid levels are: {', '.join(valid_levels)}")

    # Set the log level
    # logger.remove()
    logger.add(
        APP_SETTINGS.DATA_FOLDER + "/logs/debug.log",
        format="{time} {level} {message}",
        level=normalized_level.upper(),
        rotation="10 MB",
    )


def format_args(func: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[str, str]:
    """Format the arguments of a function call for logging.

    Args:
        func: The function being called.
        args: Positional arguments.
        kwargs: Keyword arguments.

    Returns:
        A tuple of (formatted_args, formatted_kwargs).
    """
    try:
        # Get the signature of the function
        sig = inspect.signature(func)

        # If this is a method, remove 'self' from the args
        if args and inspect.ismethod(func):
            args = args[1:]  # Remove 'self' argument

        # Bind the arguments to the signature
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Format args and kwargs
        formatted_args: list[str] = []
        formatted_kwargs: dict[str, str] = {}

        for param_name, value in bound_args.arguments.items():
            param = sig.parameters[param_name]
            if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                formatted_args.append(repr(value))
            else:
                formatted_kwargs[param_name] = repr(value)

        args_str = ", ".join(formatted_args)
        kwargs_str = ", ".join(f"{k}={v}" for k, v in formatted_kwargs.items())

        return args_str, kwargs_str
    except Exception as e:
        logger.warning(f"Error formatting arguments: {e}")
        return str(args), str(kwargs)


def log_function_call(log_level: str = "info") -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for logging function calls with timing and error handling.

    Args:
        log_level: The logging level to use ("trace", "debug", "info", "success",
                  "warning", "error", "critical"). Case-insensitive.

    Returns:
        A decorator function that wraps the original function with logging capabilities.

    Raises:
        ValueError: If an invalid log level is provided.
    """
    # Convert log level to lowercase and validate
    normalized_level = log_level.lower()
    if not hasattr(logger, normalized_level):
        valid_levels = ["trace", "debug", "info", "success", "warning", "error", "critical"]
        raise ValueError(f"Invalid log level: {log_level}. Valid levels are: {', '.join(valid_levels)}")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Format the arguments
            args_str, kwargs_str = format_args(func, args, kwargs)

            # Prepare the log messages
            func_name = f"{func.__module__}.{func.__qualname__}"
            start_msg = (
                f"{ConsoleColor.CYAN}START {func_name}:{ConsoleColor.RESET_COLOR}\n"
                f"  args: {truncate_string(args_str)}\n"
                f"  kwargs: {truncate_string(kwargs_str)}"
            )

            # Get the logger method using the normalized level
            log = cast(Callable[..., None], getattr(logger, normalized_level))
            log(start_msg)

            start_time = time.time()

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Calculate execution time
                execution_time = time.time() - start_time
                execution_time_str = f"{ConsoleColor.YELLOW}{execution_time:.4f} seconds{ConsoleColor.RESET_COLOR}"

                # Log the result
                result_str = truncate_string(str(result))
                end_msg = (
                    f"{ConsoleColor.CYAN}RETURNED {func_name}:{ConsoleColor.RESET_COLOR}\n"
                    f"  result: {result_str}\n"
                    f"  time: {execution_time_str}"
                )
                log(end_msg)

                return result

            except Exception as exc:
                # Log the exception with full traceback
                logger.exception(
                    f"Exception in {func_name}:\n"
                    f"  args: {truncate_string(args_str)}\n"
                    f"  kwargs: {truncate_string(kwargs_str)}\n"
                    f"  error: {exc}"
                )
                raise

        return wrapper

    return decorator


# Export the decorator
__all__ = ["log_function_call"]
