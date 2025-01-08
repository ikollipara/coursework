"""
loaders.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-02

Load Contextual Data
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from getpass import getuser
from grp import getgrnam
from grp import struct_group
from os import geteuid
from os import getuid
from os import seteuid
from tomllib import load
from typing import BinaryIO
from typing import Literal
from typing import NamedTuple
from warnings import warn

from click import ClickException

# Runner defines the current possible
# runners. Currently Python Unittests
# and bash scripts are supported.
RUNNER = Literal["cmd", "py"]


class TestSpec(NamedTuple):
    runner: RUNNER
    filename: str


class ImproperlyConfigured(ClickException):
    """Represents an improper configuration, leading to a parse error."""


@dataclass(frozen=True)
class Configuration:
    """
    # Configuration

    Configuration defines a pythonic representation of the coursework config file.
    Importantly, it contains one method: `from_toml` that can be used to load the
    configuration from a given file pointer.
    """

    admins: list[str]
    admin_group: struct_group
    submission: str
    collection: str
    courses: dict[str, Course]

    @dataclass(frozen=True)
    class Course:
        """
        # Course

        A course in coursework defines a set of assignments, students, and instructors.
        Students are able to view and submit for the given assignments.
        Instructors may run reporting commands on the given assignments.
        """

        name: str
        instructors: list[str] = field(default_factory=list)
        students: list[str] = field(default_factory=list)
        assignments: dict[str, Configuration.Assignment] = field(default_factory=dict)

    @dataclass(frozen=True)
    class Assignment:
        """
        # Assignment

        An assignment in coursework defines what students will see.
        An assignment contains metadata such as description, due_date, and total_points, as well as
        the execution path and runner to actually assess the student.
        """

        name: str
        description: str
        due_date: datetime
        total_points: int
        test: TestSpec

    @classmethod
    def from_toml(cls, fp: BinaryIO):
        """Load the configuration from the given file pointer. Raise ImproperlyConfigured upon failure."""

        parsed = load(fp)

        parsed.setdefault("coursework", {})
        parsed.setdefault("assignments", {})
        parsed.setdefault("courses", {})
        parsed["coursework"].setdefault("admin_group", "sysman")
        parsed["coursework"].setdefault(
            "submission",
            "/home/stu/{student}/.local/share/coursework/{course}/{assignment}",
        )
        parsed["coursework"].setdefault("collection", "/home/fs/{instructor}/coursework/{course}/{assignment}")
        parsed["coursework"].setdefault("admins", [])

        assignments = cls._load_assignments(parsed)
        courses = cls._load_courses(parsed, assignments)

        if len(courses) == 0:
            warn("No courses defined. Consider defining courses.")

        try:
            return cls(
                admins=parsed["coursework"]["admins"],
                admin_group=getgrnam(parsed["coursework"]["admin_group"]),
                submission=parsed["coursework"]["submission"],
                collection=parsed["coursework"]["collection"],
                courses=courses,
            )
        except KeyError as e:
            raise ImproperlyConfigured(f"admin group {parsed['coursework']['admin_group']} does not exist") from e

    @classmethod
    def _load_assignments(cls, parsed: dict):
        try:
            return {
                name: (
                    cls.Assignment(
                        name,
                        description=values.get("description", ""),
                        due_date=datetime.strptime(values["due_date"], "%Y-%m-%d %H:%M"),
                        total_points=values.get("total_points", 0),
                        test=TestSpec(*values.get("test", " : ").split(":")),
                    )
                )
                for name, values in parsed["assignments"].items()
            }
        except (ValueError, KeyError) as e:
            raise ImproperlyConfigured("Error parsing due date.") from e

    @classmethod
    def _load_courses(cls, parsed: dict, assignments: dict[str, Configuration.Assignment]):
        try:
            return {
                name: cls.Course(
                    name,
                    instructors=values.get("instructors", []),
                    students=values.get("students", []),
                    assignments={assignment: assignments[assignment] for assignment in values.get("assignments", [])},
                )
                for name, values in parsed["courses"].items()
            }
        except KeyError as e:
            raise ImproperlyConfigured("Assignment does not exist") from e


@dataclass(frozen=True)
class User:
    """
    # User

    A user in coursework is whatever user is currently running the program.
    This is used to inform certain command availability.
    """

    name: str
    role: Literal["instructor", "student"]

    @property
    def is_instructor(self) -> bool:
        return self.role == "instructor"

    @classmethod
    def from_env(cls, config: Configuration, *, name=None):
        name = name or getuser()
        return cls(name=name, role=("instructor" if name in config.admins else "student"))

    @contextmanager
    def as_root(self):
        """Elevate the permissions of the user."""

        real_user_id = getuid()
        effective_user_id = geteuid()

        try:
            seteuid(real_user_id)
            yield

        finally:
            seteuid(effective_user_id)
