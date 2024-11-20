from collections.abc import Callable


class ToolValidationMixin:
    """Mixin to add tool validation to Agent class."""

    def validate_tool(self, func: Callable) -> None:
        """Validate that a tool's required providers are available."""
        if not hasattr(func, "required_providers"):
            raise ValueError(f"Function {func.__name__} must be decorated with @with_providers")

        # Get available providers from agent's configuration

        available_providers = {pc.provider_name for pc in self.provider_configurations}  # type: ignore

        # Check for missing providers
        missing_providers = set(func.required_providers) - available_providers
        if missing_providers:
            raise ValueError(
                f"Function {func.__name__} requires providers {missing_providers} "
                f"which are not configured for this agent"
            )
