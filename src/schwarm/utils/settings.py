"""Simple settings management using python-decouple."""

import os
from pathlib import Path
from typing import ClassVar

from decouple import config as decouple_config


def get_config(key: str, default: str = "") -> str:
    """Wrapper to ensure string values from config."""
    try:
        return str(decouple_config(key, default=default))  # type: ignore
    except Exception:
        return default


def get_environment():
    """Get the environment path for the current execution"""
    if os.path.exists("index.html"):
        return Path(".")
    else:
        return Path(__file__).resolve().parent


class Settings:
    """Simple settings management using python-decouple."""

    _defaults: ClassVar[dict[str, str]] = {
        "DATA_FOLDER": ".data/",
        "TELEMETRY": ".telemetry/",
        "CONTEXT_VARS_KEY": "context_variables",
        "SYSTEM_ROLE": "system",
        "ASSISTANT_ROLE": "assistant",
        "USER_ROLE": "user",
    }

    def __init__(self, env_path: str = ".env") -> None:
        """Initialize settings and ensure defaults exist in .env."""
        self._write_back = False
        self._env_path = env_path

        # Read current env file
        try:
            with open(self._env_path) as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []

        # Track which defaults need to be added
        existing_keys = {line.split("=")[0].strip() for line in lines if line.strip() and not line.startswith("#")}
        missing_defaults = {key: value for key, value in self._defaults.items() if key not in existing_keys}

        # Add missing defaults to .env (always write defaults on init)
        if missing_defaults:
            with open(self._env_path, "a") as f:
                if lines and not lines[-1].endswith("\n"):
                    f.write("\n")
                for key, value in missing_defaults.items():
                    f.write(f"{key}={value}\n")
                    os.environ[key] = value

    def enable_write_back(self) -> None:
        """Enable writing back to .env file."""
        self._write_back = True

    def disable_write_back(self) -> None:
        """Disable writing back to .env file."""
        self._write_back = False

    def __getattr__(self, name: str) -> str:
        """Get setting value from env or defaults."""
        if name.upper() == "WRITE_BACK":
            return str(self._write_back).lower()

        upper_name = name.upper()
        default = self._defaults.get(upper_name, "")
        return get_config(upper_name, default=default)

    def __setattr__(self, name: str, value: str) -> None:
        """Set setting value and update .env file if WRITE_BACK is True."""
        if name == "_defaults":
            super().__setattr__(name, value)
            return

        if name == "_write_back":
            super().__setattr__(name, value)
            return

        if name.upper() == "WRITE_BACK":
            super().__setattr__("_write_back", value.lower() == "true")
            return

        upper_name = name.upper()
        # env_path = ".env"

        # Always update environment
        os.environ[upper_name] = str(value)

        # Only write to .env if WRITE_BACK is True
        if not self._write_back:
            return

        # Read current env file
        try:
            with open(self._env_path) as f:
                lines: list[str] = f.readlines()
        except FileNotFoundError:
            lines = []

        # Find and update or append setting
        found = False
        new_lines: list[str] = []
        for line in lines:
            if line.strip() and not line.startswith("#"):
                key = line.split("=")[0].strip()
                if key == upper_name:
                    new_lines.append(f"{upper_name}={value}\n")
                    found = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"{upper_name}={value}\n")

        # Write back to env file
        with open(self._env_path, "w") as f:
            f.writelines(new_lines)


# Create global instance
APP_SETTINGS = Settings()
