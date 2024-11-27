"""Core package for Schwarm.

This package contains the base classes and implementations for:
- Logging utilities and decorators
- LLM providers and interactions
- Stream handling
- Core tools and functionality
"""

from schwarm.core.logging import log_function_call

__all__ = ["log_function_call"]
