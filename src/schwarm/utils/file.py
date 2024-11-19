"""Utility functions for saving and loading research results."""

import os
from typing import Any

import orjson

from schwarm.utils.settings import APP_SETTINGS


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
