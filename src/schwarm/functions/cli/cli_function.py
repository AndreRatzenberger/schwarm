"""CLI-style function wrapper for the Function class."""

from typing import Any, Callable, Dict, List, Optional

from ...context.context import Context
from ...functions.function import Function
from .command import Command, Parameter


class CLIFunction(Function):
    """A Function wrapper that supports CLI-style parameter handling.
    
    This class extends the base Function class to support CLI-style
    parameter definitions and parsing. It handles the two-step LLM
    process of tool selection and parameter generation.
    
    Example:
        def generate_image(context: Context, prompt: str, style: str) -> str:
            # Implementation
            pass
            
        cli_function = CLIFunction(
            name="image-gen",
            implementation=generate_image,
            description="Generate images from text",
            parameters=[
                Parameter("-p", "prompt text", required=True),
                Parameter("--style", "image style", 
                         choices=["realistic", "anime"])
            ]
        )
    """
    
    def __init__(
        self,
        name: str,
        implementation: Callable[..., Any],
        description: str,
        parameters: List[Parameter],
    ) -> None:
        """Initialize a new CLI function.
        
        Args:
            name: The name of the function
            implementation: The callable that implements the function
            description: Description of what the function does
            parameters: List of CLI-style parameters
        """
        super().__init__(
            name=name,
            implementation=implementation,
            description=description
        )
        self.command = Command(
            name=name,
            description=description,
            parameters=parameters
        )
        self._param_map = {p.flag: p for p in parameters}
        
    def get_help(self) -> str:
        """Get formatted help text for this function.
        
        Returns:
            A string containing usage information
        """
        return self.command.format_help()
        
    async def execute_cli(
        self,
        context: Context,
        command_str: str
    ) -> Any:
        """Execute the function using a CLI-style command string.
        
        Args:
            context: The shared context object
            command_str: The command string to parse and execute
            
        Returns:
            The result of executing the function
            
        Raises:
            ValueError: If the command string is invalid
        """
        # Parse the command string
        success, result = self.command.parse(command_str)
        
        if not success:
            raise ValueError(f"Invalid command: {result}")
            
        # Convert CLI parameters to function arguments
        kwargs = self._convert_params_to_kwargs(result)
        
        # Execute the function
        return await super().execute(context, **kwargs)
        
    def _convert_params_to_kwargs(self, params: Dict[str, str]) -> Dict[str, Any]:
        """Convert CLI parameters to function keyword arguments.
        
        Args:
            params: Dictionary of parameter values from CLI parsing
            
        Returns:
            Dictionary of keyword arguments for the implementation
        """
        # Convert CLI flags to parameter names
        return {
            flag.lstrip('-'): value
            for flag, value in params.items()
        }
