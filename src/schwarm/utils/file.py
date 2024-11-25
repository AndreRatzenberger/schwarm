"""Utility functions for saving and loading research results."""

import os
from contextlib import contextmanager
from typing import Any

import orjson

from schwarm.utils.settings import APP_SETTINGS


@contextmanager
def temporary_env_vars(new_env_vars):
    """Temporarily set environment variables and revert to their original values.

    Args:
        new_env_vars (dict): A dictionary of environment variables to set.

    Usage:
        with temporary_env_vars({'MY_VAR': 'new_value'}):
            # Do something with the new environment variables
            pass
        # Environment variables are restored here
    """
    # Backup current values of the environment variables
    backup_env_vars = {key: os.environ.get(key) for key in new_env_vars}

    # Set the new environment variables
    try:
        os.environ.update(new_env_vars)
        yield
    finally:
        # Revert environment variables to their original values
        for key, value in backup_env_vars.items():
            if value is None:
                os.environ.pop(key, None)  # Remove variable if it didn't exist
            else:
                os.environ[key] = value


def save_dictionary_list(file_name: str, dic_list: list[dict[str, Any]]):
    """Save the research result to a file."""
    if not os.path.exists(APP_SETTINGS.DATA_FOLDER):
        os.makedirs(APP_SETTINGS.DATA_FOLDER)
    output = orjson.dumps(dic_list, option=orjson.OPT_INDENT_2)
    file_path = os.path.join(APP_SETTINGS.DATA_FOLDER, file_name)
    with open(file_path, "wb") as f:
        f.write(output)


def load_dictionary_list(file_name: str) -> list[dict[str, Any]]:
    """Load the research result from a file."""
    if not os.path.exists(APP_SETTINGS.DATA_FOLDER):
        os.makedirs(APP_SETTINGS.DATA_FOLDER)
    file_path = os.path.join(APP_SETTINGS.DATA_FOLDER, file_name)

    if not os.path.exists(file_path):
        return []
    with open(file_path, "rb") as f:
        json = f.read()
    return orjson.loads(json)


def save_text_to_file(file_name: str, title: str = "", content: str = "") -> None:
    """Save the content to a file."""
    if not os.path.exists(APP_SETTINGS.DATA_FOLDER):
        os.makedirs(APP_SETTINGS.DATA_FOLDER)
    file_path = os.path.join(APP_SETTINGS.DATA_FOLDER, file_name)

    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"{content}\n\n")
