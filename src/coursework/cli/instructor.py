"""
instructor.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-03

Instructor Commands
"""

import os
from io import BytesIO
from pathlib import Path

import click
from rich.progress import track

from coursework import report
from coursework.cli import ContextObj, cli, converters
from coursework.loaders import Configuration
from coursework.models import RunnerResult


@cli.command("report")
@click.argument("course", type=converters.CourseParamType())
@click.argument("assignment", type=converters.AssignmentParamType())
@click.option("-s", "--student", type=click.STRING, help="The student to generate the report for.", default=None)
@click.pass_obj
def report_assignment(
    ctx: ContextObj, course: Configuration.Course, assignment: Configuration.Assignment, student: str | None = None
):
    """Generate a pdf report for the given ASSIGNMENT in the given COURSE. Optionally specify a student using the --student flag."""

    config = ctx["config"]
    console = ctx["console"]
    user = ctx["user"]

    if not student:
        reports: list[BytesIO] = []
        for student in track(
            course.students, description="Generating for students...", total=len(course.students), console=console
        ):
            submission_path = Path(
                config.submission.format(student=student, course=course.name, assignment=assignment.name)
            )

            if not submission_path.exists():
                console.print(f"[bold red]{student} has not submitted {assignment.name}[/]")
                continue

            result = RunnerResult.from_pickle(submission_path / ".runner-output")

            reports.append(
                report.make(result, [file for file in submission_path.glob("*") if ".runner-output" not in str(file)])
            )

        save_path = Path(config.collection.format(instructor=user.name, course=course.name, assignment=assignment.name))
        save_path.mkdir(parents=True, exist_ok=True)
        for report_ in reports:
            (save_path / f"{student}.pdf").write_bytes(report_.getbuffer())

        console.print("[bold green]Reports generated![/]")

    else:
        submission_path = Path(
            config.submission.format(student=student, course=course.name, assignment=assignment.name)
        )
        if not submission_path.exists():
            console.print(f"[bold red]{student} has not submitted {assignment.name}[/]")
            exit(1)

        result = RunnerResult.from_pickle(submission_path / ".runner-output")
        save_path = Path(config.collection.format(instructor=user.name, course=course.name, assignment=assignment.name))
        save_path.mkdir(parents=True, exist_ok=True)

        (save_path / f"{student}.pdf").write_bytes(
            report.make(result, [file for file in submission_path.glob("*") if ".runner-ouput" not in str(file)])
        )
        console.print(f"[bold green]Report generated for {student}![/]")


@cli.command("edit")
@click.pass_obj
def edit(ctx: ContextObj):
    """Edit the COURSEWORK_CONFIG."""

    console = ctx["console"]

    filename = os.getenv("COURSEWORK_CONFIG")

    click.edit(filename=filename)

    console.print("[bold green]Edits saved![/]")
