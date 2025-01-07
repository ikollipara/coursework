"""
models.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-02

Data Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from pickle import dump, load, loads
from typing import BinaryIO, Self, overload

from coursework.loaders import Configuration, User


class _CanBePickled:
    @overload
    def to_pickle(self, fp: BinaryIO) -> None:
        """Pickle the object into the file pointer/IO buffer."""

    @overload
    def to_pickle(self, fp: Path) -> None:
        """Pickle the object into the given file path."""

    def to_pickle(self, fp: BinaryIO | Path) -> None:
        if isinstance(fp, Path):
            with fp.open("wb+") as f:
                dump(self, f)
        else:
            dump(self, fp)

    @overload
    @classmethod
    def from_pickle(cls, fp: bytes) -> Self:
        """Deserialize from the pickled byte string."""

    @overload
    @classmethod
    def from_pickle(cls, fp: BinaryIO) -> Self:
        """Deserialize from the pickled file pointer/IO buffer."""

    @overload
    @classmethod
    def from_pickle(cls, fp: Path) -> Self:
        """Deserialize from the given file path."""

    @classmethod
    def from_pickle(cls, fp: BinaryIO | Path | bytes) -> Self:
        if isinstance(fp, bytes):
            return loads(fp)
        if isinstance(fp, Path):
            with fp.open("rb") as f:
                return load(f)
        else:
            return load(fp)


@dataclass(frozen=True)
class TestCaseResult(_CanBePickled):
    """
    # TestCaseResult.

    The result of running a particular test case.
    It includes details such as hints, the number of points, and if the test was successful.
    """

    name: str
    was_successful: bool
    points: int
    hint: str = ""


@dataclass(frozen=True)
class RunnerResult(_CanBePickled):
    """
    # RunnerResult.

    The result of an overal submission run. It includes various details such as:
    - the user who ran it.
    - the time it was ran.
    - The course
    - The assignment
    - the collection of test case results.
    """

    user: User
    ran_at: datetime
    course: Configuration.Course
    assignment: Configuration.Assignment
    test_case_results: list[TestCaseResult] = field(default_factory=list)
