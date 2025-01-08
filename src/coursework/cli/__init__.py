"""
cli.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-03

CLI Entrypoint
"""

from typing import TypedDict

from rich.console import Console

from coursework.loaders import Configuration
from coursework.loaders import User


class ContextObj(TypedDict):
    """
    # ContextObj.

    A typed dict used to infer the keys on the context object.
    This is used as a container to get dependencies from in CLI commands.
    """

    console: Console
    config: Configuration
    user: User
