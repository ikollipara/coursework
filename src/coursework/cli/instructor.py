"""
instructor.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-03

Instructor Commands
"""

import os
from io import BufferedReader, BytesIO
from pathlib import Path
from shutil import chown

import click
from rich.console import Console
from rich.progress import track

from coursework import report
from coursework.cli import ContextObj, converters
from coursework.loaders import Configuration, User
from coursework.models import RunnerResult


@click.group()
@click.option("--config", type=click.File("br"), hidden=True, envvar="COURSEWORK_CONFIG")
@click.pass_context
def cli(ctx: click.Context, config: BufferedReader):
    """
    Coursework Admin.

    Coursework is a hand-in program for use by students at Concordia University.
    This admin application can be used by instructors to handle administrative tasks
    such as editing the configuration or generating reports.
    """

    ctx.ensure_object(dict)
    console = Console(file=click.get_text_stream("stdout"))
    configuration = Configuration.from_toml(config)
    user = User.from_env(configuration)

    ctx.obj["console"] = console
    ctx.obj["config"] = configuration
    ctx.obj["user"] = user

    if not ctx.obj["user"].is_instructor:
        raise click.ClickException("You are not an admin!")


@cli.command("report")
@click.argument("course", type=converters.CourseParamType())
@click.argument("assignment", type=converters.AssignmentParamType())
@click.pass_obj
def report_assignment(ctx: ContextObj, course: Configuration.Course, assignment: Configuration.Assignment):
    """Generate a pdf report for the given ASSIGNMENT in the given COURSE. Optionally specify a student using the --student flag."""

    config = ctx["config"]
    console = ctx["console"]
    user = ctx["user"]

    reports: list[BytesIO] = []
    for student in track(
        course.students, description="Generating for students...", total=len(course.students), console=console
    ):
        submission_path = Path(
            config.submission.format(student=student, course=course.name, assignment=assignment.name)
        )

        with user.as_root():
            if not submission_path.exists():
                console.print(f"[bold red]{student} has not submitted {assignment.name}[/]")
                continue

            result = RunnerResult.from_pickle(submission_path / ".runner-output")

            reports.append(
                (
                    student,
                    report.make(
                        result, [file for file in submission_path.glob("*") if ".runner-output" not in str(file)]
                    ),
                )
            )

    with user.as_root():
        save_path = Path(config.collection.format(instructor=user.name, course=course.name, assignment=assignment.name))
        save_path.mkdir(parents=True, exist_ok=True)
        chown(save_path, user.name, config.admin_group.gr_gid)

        for student, report_ in reports:
            (save_path / f"{student}.pdf").write_bytes(report_.getbuffer())
            chown(save_path / f"{student}.pdf", user.name, config.admin_group.gr_gid)

    console.print("[bold green]Reports generated![/]")


@cli.command("edit")
@click.pass_obj
def edit(ctx: ContextObj):
    """Edit the COURSEWORK_CONFIG."""

    console = ctx["console"]

    filename = os.getenv("COURSEWORK_CONFIG")
    click.edit(filename=filename)

    # This loop makes sure the configuration stays valid,
    # since the entire CLI will break if this isn't the case.
    while not Configuration.validate(console, filename):
        click.edit(filename=filename)

    console.print("[bold green]Edits saved![/]")


if __name__ == "__main__":  # pragma: no cover
    cli()
