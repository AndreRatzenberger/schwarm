"""CLI-style command handling for LLM tool interactions."""

from dataclasses import dataclass


@dataclass
class Parameter:
    """Represents a CLI-style parameter for a command.

    Example:
        Parameter("-p", "prompt text")
        Parameter("--style", "style to use", choices=["realistic", "anime"])
    """

    flag: str
    description: str
    choices: list[str] | None = None
    required: bool = False

    def validate(self, value: str) -> tuple[bool, str | None]:
        """Validate a value for this parameter.

        Args:
            value: The value to validate

        Returns:
            A tuple of (is_valid, error_message)
        """
        if self.choices and value not in self.choices:
            return False, f"Value must be one of: {', '.join(self.choices)}"
        return True, None


@dataclass
class Command:
    """Represents a CLI-style command that can be executed by an LLM.

    Example:
        Command(
            name="image-gen",
            description="Generate images from text",
            parameters=[
                Parameter("-p", "prompt text"),
                Parameter("--style", choices=["realistic", "anime"])
            ]
        )
    """

    name: str
    description: str
    parameters: list[Parameter]

    def format_help(self) -> str:
        """Format help text for this command.

        Returns:
            A string containing usage information
        """
        help_text = [f"Command: {self.name}", f"Description: {self.description}", "\nParameters:"]

        for param in self.parameters:
            choices = f" (choices: {', '.join(param.choices)})" if param.choices else ""
            required = " (required)" if param.required else ""
            help_text.append(f"  {param.flag}: {param.description}{choices}{required}")

        return "\n".join(help_text)

    def parse(self, command_str: str) -> tuple[bool, dict | str]:
        """Parse a command string into parameters.

        Args:
            command_str: The command string to parse

        Returns:
            A tuple of (success, result) where result is either:
            - On success: A dict of parameter values
            - On failure: An error message string
        """
        # Split the command string, preserving quoted strings
        parts = []
        current = []
        in_quotes = False

        for char in command_str:
            if char == '"' or char == "'":
                in_quotes = not in_quotes
            elif char.isspace() and not in_quotes:
                if current:
                    parts.append("".join(current))
                    current = []
            else:
                current.append(char)

        if current:
            parts.append("".join(current))

        # Verify command name
        if not parts or parts[0] != self.name:
            return False, f"Invalid command. Expected '{self.name}'"

        # Parse parameters
        values = {}
        i = 1
        while i < len(parts):
            part = parts[i]

            # Find matching parameter
            param = next((p for p in self.parameters if p.flag == part), None)

            if not param:
                return False, f"Unknown parameter: {part}"

            # Get value (next part)
            if i + 1 >= len(parts):
                return False, f"Missing value for parameter: {part}"

            value = parts[i + 1]
            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            # Validate value
            is_valid, error = param.validate(value)
            if not is_valid:
                return False, f"Invalid value for {part}: {error}"

            # Store value
            values[param.flag] = value
            i += 2

        # Check required parameters
        missing = [p.flag for p in self.parameters if p.required and p.flag not in values]
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"

        return True, values
