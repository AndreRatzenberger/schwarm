"""Tests for CLI-style tool functionality."""

import pytest
from typing import List, Optional

from schwarm.context.context import Context
from schwarm.agents.agent_builder import AgentBuilder
from schwarm.functions.cli import CLIFunction, Parameter
from schwarm.functions.cli.command import Command
from schwarm.functions.cli.decorators import cli_command, cli_param, is_cli_function
from schwarm.providers.cli_llm_provider import CLILLMProvider


# Test helper functions
async def image_function(context: Context, p: str, style: str = "realistic") -> str:
    """Test function that simulates image generation."""
    return f"Generated {style} image from prompt: {p}"


def test_command_parsing():
    """Test CLI command parsing."""
    command = Command(
        name="image-gen",
        description="Generate images from text",
        parameters=[
            Parameter("-p", "prompt text", required=True),
            Parameter("--style", "style to use", choices=["realistic", "anime"])
        ]
    )
    
    # Test valid command without quotes
    success, result = command.parse("image-gen -p cat-photo --style realistic")
    assert success
    assert isinstance(result, dict)
    assert result["-p"] == "cat-photo"
    assert result["--style"] == "realistic"
    
    # Test missing required parameter
    success, result = command.parse("image-gen --style realistic")
    assert not success
    assert isinstance(result, str)
    assert "Missing required parameters: -p" in result
    
    # Test invalid choice
    success, result = command.parse("image-gen -p cat-photo --style cartoon")
    assert not success
    assert isinstance(result, str)
    assert "Value must be one of: realistic, anime" in result


def test_cli_function_creation():
    """Test creating a CLIFunction."""
    cli_function = CLIFunction(
        name="image-gen",
        implementation=image_function,
        description="Generate images from text",
        parameters=[
            Parameter("-p", "prompt text", required=True),
            Parameter("--style", "style to use", choices=["realistic", "anime"])
        ]
    )
    
    assert cli_function.name == "image-gen"
    assert cli_function.description == "Generate images from text"
    
    # Test help text formatting
    help_text = cli_function.get_help()
    assert "Command: image-gen" in help_text
    assert "Parameters:" in help_text
    assert "-p: prompt text (required)" in help_text
    assert "--style: style to use (choices: realistic, anime)" in help_text


@pytest.mark.asyncio
async def test_cli_function_execution():
    """Test executing a CLIFunction."""
    cli_function = CLIFunction(
        name="image-gen",
        implementation=image_function,
        description="Generate images from text",
        parameters=[
            Parameter("-p", "prompt text", required=True),
            Parameter("--style", "style to use", choices=["realistic", "anime"])
        ]
    )
    
    context = Context()
    
    # Test successful execution
    result = await cli_function.execute_cli(
        context,
        "image-gen -p cat-photo --style anime"
    )
    assert result == "Generated anime image from prompt: cat-photo"
    
    # Test invalid command
    with pytest.raises(ValueError) as exc_info:
        await cli_function.execute_cli(
            context,
            "image-gen -p cat-photo --style cartoon"
        )
    assert "Invalid command" in str(exc_info.value)


def test_explicit_decorator():
    """Test CLI function creation with explicit decorators."""
    @cli_command(
        name="image-gen",
        description="Generate images from text"
    )
    @cli_param("-p", "prompt text", required=True)
    @cli_param("--style", "style to use", choices=["realistic", "anime"])
    async def generate_image(
        context: Context,
        p: str,
        style: str = "realistic"
    ) -> str:
        """Generate an image from text."""
        return f"Generated {style} image from prompt: {p}"
    
    assert is_cli_function(generate_image)
    assert isinstance(generate_image, CLIFunction)
    assert generate_image.name == "image-gen"
    assert len(generate_image.command.parameters) == 2
    
    param_p = generate_image.command.parameters[0]
    assert param_p.flag == "-p"
    assert param_p.required is True
    
    param_style = generate_image.command.parameters[1]
    assert param_style.flag == "--style"
    assert param_style.choices == ["realistic", "anime"]


def test_lazy_decorator():
    """Test CLI function creation with lazy parameter inference."""
    @cli_command(lazy=True)
    async def search(
        context: Context,
        query: str,
        limit: int = 10,
        sort: str = "relevance",
        tags: Optional[List[str]] = None
    ) -> List[str]:
        """Search for items in the database.
        
        Args:
            query: The search query string
            limit: Maximum number of results
            sort: Sort order (relevance, date)
            tags: Optional tags to filter by
        """
        return []
    
    assert is_cli_function(search)
    assert isinstance(search, CLIFunction)
    assert search.name == "search"
    
    # Check inferred parameters
    params = {p.flag: p for p in search.command.parameters}
    
    assert "--query" in params
    assert params["--query"].required is True
    assert "search query string" in params["--query"].description.lower()
    
    assert "--limit" in params
    assert params["--limit"].required is False
    
    assert "--sort" in params
    assert params["--sort"].required is False
    
    assert "--tags" in params
    assert params["--tags"].required is False


def test_lazy_decorator_minimal_docs():
    """Test lazy decorator with minimal docstring."""
    @cli_command(lazy=True)
    async def summarize(
        context: Context,
        text: str,
        max_length: int = 100
    ) -> str:
        """Summarize text to a specified length."""
        return ""
    
    assert is_cli_function(summarize)
    assert isinstance(summarize, CLIFunction)
    
    # Check inferred parameters
    params = {p.flag: p for p in summarize.command.parameters}
    
    assert "--text" in params
    assert params["--text"].required is True
    
    assert "--max-length" in params
    assert params["--max-length"].required is False


def test_agent_builder_cli_integration():
    """Test AgentBuilder integration with CLI functions."""
    # Create builder with CLI function
    builder = (
        AgentBuilder("TestAgent")
        .with_cli_function(
            name="image-gen",
            implementation=image_function,
            description="Generate images from text",
            parameters=[
                Parameter("-p", "prompt text", required=True),
                Parameter("--style", "style to use", choices=["realistic", "anime"])
            ]
        )
    )
    
    # Build agent
    agent = builder.build()
    
    # Verify CLI function was added
    assert len(agent._functions) == 1
    assert isinstance(agent._functions["image-gen"], CLIFunction)
    
    # Verify CLILLMProvider was auto-added
    assert len(agent._providers) == 1
    assert isinstance(agent._providers[0], CLILLMProvider)


def test_agent_builder_multiple_cli_functions():
    """Test adding multiple CLI functions to an agent."""
    # Create decorated functions
    @cli_command(lazy=True)
    async def search(
        context: Context,
        query: str,
        limit: int = 10
    ) -> List[str]:
        """Search for items."""
        return []
    
    @cli_command(
        name="image-gen",
        description="Generate images"
    )
    @cli_param("-p", "prompt text", required=True)
    @cli_param("--style", "style to use", choices=["realistic", "anime"])
    async def generate_image(
        context: Context,
        p: str,
        style: str = "realistic"
    ) -> str:
        return ""
    
    # Create builder with both functions
    builder = (
        AgentBuilder("TestAgent")
        .with_function(search)
        .with_function(generate_image)
    )
    
    # Build agent
    agent = builder.build()
    
    # Verify both functions were added
    assert len(agent._functions) == 2
    assert isinstance(agent._functions["search"], CLIFunction)
    assert isinstance(agent._functions["image-gen"], CLIFunction)
    
    # Verify only one CLILLMProvider was added
    assert len(agent._providers) == 1
    assert isinstance(agent._providers[0], CLILLMProvider)


@pytest.mark.asyncio
async def test_cli_llm_provider():
    """Test CLILLMProvider functionality."""
    provider = CLILLMProvider(
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    
    # Create a test CLI function
    cli_function = CLIFunction(
        name="image-gen",
        implementation=image_function,
        description="Generate images from text",
        parameters=[
            Parameter("-p", "prompt text", required=True),
            Parameter("--style", "style to use", choices=["realistic", "anime"])
        ]
    )
    
    # Test command validation
    is_valid, error = await provider.validate_command(
        "image-gen -p cat-photo --style realistic",
        cli_function
    )
    assert is_valid
    assert error is None
    
    is_valid, error = await provider.validate_command(
        "image-gen -p cat-photo --style cartoon",
        cli_function
    )
    assert not is_valid
    assert error is not None
    assert "Value must be one of: realistic, anime" in error
