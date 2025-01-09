"""
runner.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-03

Test Runners
"""

from __future__ import annotations

import subprocess
from abc import ABC as AbstractBaseClass
from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from os import chdir
from os import environ
from pathlib import Path
from runpy import run_path
from shutil import copyfile
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from typing import Type
from unittest import TestResult

from rich.columns import Columns
from rich.console import Console
from rich.rule import Rule

from coursework.loaders import Configuration
from coursework.loaders import User
from coursework.models import RunnerResult
from coursework.models import TestCaseResult
from coursework.testing import Assignment


class RunnerNotFound(Exception):
    """Raised if a runner instance cannot be found."""


@dataclass
class Runner(AbstractBaseClass):
    """
    # _Runner.

    A runner is a special class used to execute a particular assessment.
    """

    user: User
    course: Configuration.Course
    assignment: Configuration.Assignment
    files: list[Path] = field(default_factory=list)

    @abstractmethod
    def run(self, output_stream: Console) -> RunnerResult:
        """Execute the runner, writing all output to the given output stream."""

    @contextmanager
    def testing_environment(self):
        """
        Create a testing environment with all submitted files.

        The created environment is a flat-structure.
        """

        current_dir = Path.cwd()
        with TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            try:
                chdir(temp_dir)

                for file in self.files:
                    copyfile(file, temp_dir / file.name)

                yield

            finally:
                chdir(current_dir)
                for file in self.files:
                    (temp_dir / file.name).unlink(missing_ok=True)

                temp_dir.rmdir()

    def display_results(self, output_stream: Console, earned_points: int, passed: int, failed: int):
        """Display a summarized results list to the console."""

        output_stream.print(
            Columns(
                [
                    "[bold blue]Points:[/]",
                    f" {earned_points}/{self.assignment.total_points}",
                    "[bold blue]Passed:[/]",
                    f" {passed}",
                    "[bold blue]Failed:[/]",
                    f" {failed}",
                ],
                expand=True,
                title="[bold blue]Summary[/]",
            )
        )
        output_stream.print("\n")


class CmdRunner(Runner):
    def run(self, output_stream):
        with NamedTemporaryFile("ab+") as f:
            earned_points = 0
            passed = 0
            failed = 0
            script = str(Path(self.assignment.test.filename).absolute())
            with self.testing_environment(), self.user.as_root():
                proc = subprocess.Popen(
                    script,
                    shell=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=environ | {"COURSEWORK_RUNNER_OUTPUT": f.name},
                )
                output = proc.stdout.read()
                output_stream.print(output)
                proc.wait()

            contents = f.read()

            # SPLIT is an abitrary value.
            # It doesn't appear naturally, making it an ideal splitting value.
            # To change this adjust the value here, and in `coursework/score.py`.
            test_case_results = [
                TestCaseResult.from_pickle(line)
                # We ignore the last value as its just an empty bytes string.
                for line in contents.split(b"SPLIT")[:-1]
            ]

        output_stream.print(Rule(title=self.assignment.name))
        for result in test_case_results:
            output_stream.print(Rule())
            output_stream.print(f"[bold blue]Running {result.name}...[/]\n")
            if result.was_successful:
                output_stream.print("[bold green]Passed![/]\n")
                earned_points += result.points
                passed += 1
            else:
                output_stream.print("[bold red]Failed![/]\n")
                if result.hint:
                    output_stream.print(f"[bold blue]Hint:[/][bold]{result.hint}[/]\n")
                failed += 1

        self.display_results(output_stream, earned_points, passed, failed)

        return RunnerResult(self.user, datetime.now(), self.course, self.assignment, test_case_results)


class PythonUnittestRunner(Runner):
    class _TestResult(TestResult):
        def __init__(self, stream=None, descriptions=None, verbosity=None):
            super().__init__(stream, descriptions, verbosity)
            self.successes = []

        def addSuccess(self, test):
            self.successes.append(test)

    def run(self, output_stream):
        test_case_results: list[TestCaseResult] = []
        earned_points = passed = failed = 0
        with self.testing_environment(), self.user.as_root():
            for value in run_path(Path(self.assignment.test.filename).absolute()).values():
                if isinstance(value, type) and issubclass(value, Assignment) and value in Assignment.__subclasses__():
                    assessments = value.__assessments__

                    output_stream.print(Rule(title=self.assignment.name))
                    for assessment in assessments:
                        output_stream.print(Rule())
                        output_stream.print(f"[bold blue]Running {assessment.name}...[/]\n")
                        result = assessment.method.run(self._TestResult())

                        if len(result.errors) > 0:
                            output_stream.print("[bold red]Error![/]\n")
                            failed += 1
                            test_case_results.append(
                                TestCaseResult(assessment.name, False, assessment.points, assessment.hint)
                            )

                            for _, exc_info in result.errors:
                                output_stream.print(f"{exc_info}\n")

                        elif len(result.failures) > 0:
                            output_stream.print("[bold red]Failed![/]\n")
                            failed += 1
                            test_case_results.append(
                                TestCaseResult(assessment.name, False, assessment.points, assessment.hint)
                            )

                            for _, exc_info in result.failures:
                                output_stream.print(f"{exc_info}\n")

                        elif len(result.successes) > 0:
                            output_stream.print("[bold green]Passed![/]\n")
                            earned_points += assessment.points
                            passed += 1
                            test_case_results.append(
                                TestCaseResult(assessment.name, True, assessment.points, assessment.hint)
                            )

        self.display_results(output_stream, earned_points, passed, failed)

        return RunnerResult(self.user, datetime.now(), self.course, self.assignment, test_case_results)


class ManualRunner(Runner):
    """A runner for manually graded assignments."""

    def run(self, output_stream):
        output_stream.print(Rule(title=self.assignment.name))
        output_stream.print("[bold blue]This assignment is manually graded.[/]")

        return RunnerResult(self.user, datetime.now(), self.course, self.assignment, [])


_RUNNER_MAP: dict[str, Runner] = {"cmd": CmdRunner, "py": PythonUnittestRunner, "manual": ManualRunner}


def get_runner_by_name(name: str) -> Type[Runner]:
    """Get the runner based upon its short name."""

    try:
        return _RUNNER_MAP[name]
    except KeyError as e:
        raise RunnerNotFound from e
