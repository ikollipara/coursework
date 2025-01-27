"""
student.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-03

Student Cli commands
"""

from io import BufferedReader
from pathlib import Path
from shutil import chown
from shutil import copy2
from shutil import rmtree

import click
from rich.columns import Columns
from rich.console import Console
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import track
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table

from coursework.cli import ContextObj
from coursework.cli import converters
from coursework.loaders import Configuration
from coursework.loaders import User
from coursework.runner import get_runner_by_name

# https://click.palletsprojects.com/en/stable/arguments/#multiple-arguments
# Click represents an arbitrary number of arguments as -1.
ARBITRARY_NARGS = -1

# Root User ID for Linux
ROOT_UID = 0


@click.group(name="coursework")
@click.option("--config", type=click.File("br"), hidden=True, envvar="COURSEWORK_CONFIG")
@click.pass_context
def cli(ctx: click.Context, config: BufferedReader):
    """
    Coursework.

    Coursework is a hand-in program for use by students at Concordia University.
    """

    ctx.ensure_object(dict)
    console = Console(file=click.get_text_stream("stdout"))
    configuration = Configuration.from_toml(config)
    user = User.from_env(configuration)

    ctx.obj["console"] = console
    ctx.obj["config"] = configuration
    ctx.obj["user"] = user


@cli.command("list")
@click.pass_obj
def list_assigments(ctx: ContextObj):
    """List all current assignments."""

    console = ctx["console"]

    user_courses = [course for course in ctx["config"].courses.values() if ctx["user"].name in course.students]
    user_assignments = [(assignment, course) for course in user_courses for assignment in course.assignments.values()]
    user_assignments = sorted(user_assignments, key=lambda x: x[1].name)

    table = Table(
        "Name", "Course", "Due Date", title=f"Current Assignments for {ctx['user'].name}", expand=True, show_edge=False
    )

    for assignment, course in user_assignments:
        table.add_row(
            f"[bold blue]{assignment.name}[/]",
            f"[bold green]{course.name}[/]",
            f"{assignment.due_date.strftime('%Y-%m-%d %I:%M %p')}",
        )

    console.print(table)


@cli.command("detail")
@click.argument("COURSE", type=converters.CourseParamType())
@click.argument("ASSIGNMENT", type=converters.AssignmentParamType())
@click.pass_obj
def detail(ctx: ContextObj, course: Configuration.Course, assignment: Configuration.Assignment):
    """Provide extra details about a particular ASSIGNMENT in a given COURSE."""

    column = Columns(
        ["[bold]Due Date:[/]", assignment.due_date.strftime("%Y-%m-%d %I:%M %p")],
    )

    description = Markdown(assignment.description)

    panel = Panel(
        Group(column, Rule("[bold white]Description[/]"), description),
        title=f"{course.name} - {assignment.name}",
        expand=True,
    )

    ctx["console"].print(panel)


@cli.command("submit")
@click.argument("COURSE", type=converters.CourseParamType())
@click.argument("ASSIGNMENT", type=converters.AssignmentParamType())
@click.argument(
    "FILES",
    nargs=ARBITRARY_NARGS,
    type=click.Path(exists=False, resolve_path=True, allow_dash=False, path_type=Path),
)
@click.pass_obj
def submit(
    ctx: ContextObj, course: Configuration.Course, assignment: Configuration.Assignment, files: tuple[Path, ...]
):
    """Create a submission for the given ASSIGNMENT from its COURSE. You may submit 0 or more FILES with your submission."""

    console = ctx["console"]
    config = ctx["config"]
    user = ctx["user"]
    files = [f.absolute().expanduser() for f in files]

    with user.as_root():
        files = [f for f in files if f.exists() and not f.is_dir()]

    save_path = Path(
        config.submission.format(student=user.name, course=course.name, assignment=assignment.name)
    ).absolute()

    # We do this check to avoid keeping files from a past submission.
    with user.as_root():
        if save_path.exists():
            response = Prompt.ask(
                "A submission already exists. Do you want to continue and overwrite your previous submission?",
                console=console,
                choices=["y", "n"],
                default="n",
            )
            if response == "n":
                exit(1)
            else:
                rmtree(save_path)

    runner = get_runner_by_name(assignment.test.runner)
    result = runner(user, config, course, assignment, files).run(console)

    with user.as_root():
        save_path.mkdir(parents=True, exist_ok=True)
        result.to_pickle(save_path / ".runner-output")

        # chown(save_path, ROOT_UID, config.admin_group.gr_gid)
        # chown(save_path / ".runner-output", ROOT_UID, config.admin_group.gr_gid)

        for file in track(files, "Saving submitted files...", total=len(files), console=console):
            # We use copy2 instead of copy since copy2 is supposed to perserve file metadata
            # https://docs.python.org/3/library/shutil.html#shutil.copy2
            copy2(file.absolute(), save_path / file.name)
            # chown(save_path / file.name, ROOT_UID, config.admin_group.gr_gid)

    console.print(f"[bold green]{assignment.name} was successfully submitted![/]")


def main(argv=None):  # pragma: no cover
    cli.main(prog_name="coursework", args=argv)
