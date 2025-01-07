"""
cli.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-03

CLI Entrypoint
"""

from gettext import gettext as _
from os import getenv
from typing import BinaryIO, TypedDict

import click
from rich.console import Console

from coursework.loaders import Configuration, ImproperlyConfigured, User

# The use of these globals makes sure that the CLI can set them within the context,
# while still using them to allow for conditional commands.
console = None
config = None
user = None


class RichClickException(click.ClickException):
    """
    # RichClickException.

    A specialized sublcass of ClickException that uses Rich to handle the rendering.
    This allows for colorized output.
    """

    def __init__(self, message, console=None):
        super().__init__(message)
        self.console = console

    def get_console(self, file):
        if self.console is not None:
            return self.console
        else:
            return Console(file=file)

    def show(self, file=None):
        # Reimplementation that creates and uses a stderr rich console to do the rendering.
        from click._compat import get_text_stderr

        if file is None:
            file = get_text_stderr()
        console = self.get_console(file)
        console.print(_("[bold Red]Error: [/]{message}".format(message=self.format_message())))


class ContextObj(TypedDict):
    """
    # ContextObj.

    A typed dict used to infer the keys on the context object.
    This is used as a container to get dependencies from in CLI commands.
    """

    console: Console
    config: Configuration
    user: User


@click.group()
@click.pass_context
def cli(ctx: click.Context):
    """
    Coursework.

    Coursework is a hand-in program for use by students at Concordia University.
    """

    ctx.ensure_object(dict)
    ctx.obj["console"] = console
    ctx.obj["config"] = config
    ctx.obj["user"] = user


def main(config_fp: BinaryIO = None):
    # The use of the globals allow for dynamic dependency injection into the cli
    # whilst allowing for use in both future cli(s).
    global console
    global config
    global user

    console = Console(file=click.get_text_stream("stdout"))
    config = _resolve_config(config_fp, console)

    user = User.from_env(config)

    if user.is_instructor:
        import coursework.cli.instructor  # noqa: E402, F401
    else:
        import coursework.cli.student  # noqa: E402, F401

    cli()


def _resolve_config(config_fp: BinaryIO, console: Console):
    """Resolve the configuration value or error out."""

    try:
        # We allow the injection of a particular BinaryIO for testing purposes.
        # However, we do test both branches.
        if config_fp is None:
            with open(getenv("COURSEWORK_CONFIG"), "rb") as f:
                return Configuration.from_toml(f)
        else:
            return Configuration.from_toml(config_fp)

    except TypeError:
        console.print("[bold red]Error: [/][bold]COURSEWORK_CONFIG is not defined. Cannot parse config.[/]\nExiting...")
        exit(1)

    except ImproperlyConfigured:
        console.print(
            "[bold red]Error: [/][bold]There is an issue with the config file. Please fix before continuing.[/]\nExiting..."
        )
        exit(1)
