"""CLI-focused LLM provider implementation."""

from schwarm.functions.cli.cli_function import CLIFunction
from schwarm.providers.simple_llm_provider import SimpleLLMProvider


class CLILLMProvider(SimpleLLMProvider):
    """LLM provider specialized for CLI-style tool interactions.

    This provider implements a two-step process for tool usage:
    1. Tool selection based on user request
    2. Parameter generation in CLI format

    Example:
        provider = CLILLMProvider(
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        await provider.initialize()

        # First step: Select tool
        tool_name = await provider.select_tool(
            "Generate an anime-style image of a cat",
            available_tools
        )

        # Second step: Generate command
        command = await provider.generate_command(
            "Generate an anime-style image of a cat",
            selected_tool
        )
    """

    async def select_tool(self, user_request: str, available_tools: list[CLIFunction]) -> str:
        """Select the most appropriate tool for a user request.

        Args:
            user_request: The user's original request
            available_tools: List of available CLI functions

        Returns:
            The name of the selected tool
        """
        # Format tool descriptions for the prompt
        tool_descriptions = "\n\n".join(f"Tool: {tool.name}\n{tool.description}" for tool in available_tools)

        prompt = f"""Based on the user's request, select the most appropriate tool from the following options:

{tool_descriptions}

User Request: {user_request}

Respond with ONLY the name of the selected tool, nothing else."""

        response = await self.execute(prompt)
        return response.strip()

    async def generate_command(self, user_request: str, selected_tool: CLIFunction) -> str:
        """Generate a CLI command for the selected tool.

        Args:
            user_request: The user's original request
            selected_tool: The selected CLI function

        Returns:
            A properly formatted CLI command string
        """
        prompt = f"""Generate a CLI command for the following tool based on the user's request.

Tool Help:
{selected_tool.get_help()}

User Request: {user_request}

Requirements:
1. The command must start with the tool name: {selected_tool.name}
2. All required parameters must be included
3. Parameter values must match any specified choices
4. Respond with ONLY the command, no explanation

Generate command:"""

        response = await self.execute(prompt)
        return response.strip()

    async def validate_command(self, command: str, tool: CLIFunction) -> tuple[bool, str | None]:
        """Validate a generated command.

        Args:
            command: The command string to validate
            tool: The CLI function to validate against

        Returns:
            A tuple of (is_valid, error_message)
        """
        success, result = tool.command.parse(command)
        if not success:
            return False, str(result)
        return True, None

    async def fix_command(self, command: str, error: str, tool: CLIFunction) -> str:
        """Fix an invalid command based on error feedback.

        Args:
            command: The invalid command string
            error: The error message from validation
            tool: The CLI function to fix the command for

        Returns:
            A corrected command string
        """
        prompt = f"""The following command is invalid:
{command}

Error: {error}

Tool Help:
{tool.get_help()}

Requirements:
1. The command must start with the tool name: {tool.name}
2. All required parameters must be included
3. Parameter values must match any specified choices
4. Respond with ONLY the fixed command, no explanation

Generate fixed command:"""

        response = await self.execute(prompt)
        return response.strip()
