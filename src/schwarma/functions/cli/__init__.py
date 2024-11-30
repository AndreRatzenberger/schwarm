"""CLI-style tool handling for LLM interactions.

This package provides a natural way for LLMs to interact with tools using
CLI-style commands - a format they deeply understand from training data.

Example:
    from schwarm.functions.cli import CLIFunction, Parameter

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

from .cli_function import CLIFunction
from .command import Command, Parameter

__all__ = ["CLIFunction", "Command", "Parameter"]
