"""
score.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-05

coursework-score utility script
"""

from io import BufferedWriter

import click

from coursework.models import TestCaseResult


@click.command()
@click.argument("name", type=click.STRING)
@click.argument("points", type=click.IntRange(min=0))
@click.argument("was_successful", type=click.BOOL)
@click.option(
    "-m", "--message", type=click.STRING, help="An optional hint (message) to provide to the student.", default=""
)
@click.option(
    "--output",
    type=click.File("ab+"),
    envvar="COURSEWORK_RUNNER_OUTPUT",
    help="The file to output to.",
)
def main(name: str, points: int, was_successful: bool, message: str, output: BufferedWriter):
    """
    coursework-score

    A utility used when writing coursework bash assessment scripts.

    NAME: The name of the test case.

    POINTS: How many points the test case is worth.

    WAS_SUCCESSFUL: If the case was passed or not.
    """

    TestCaseResult(name, was_successful, points, message).to_pickle(output)
    output.write(b"SPLIT")


if __name__ == "__main__":
    main()
