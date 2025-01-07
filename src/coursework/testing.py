"""
testing.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-03

Testing utilities.

This module exists to provide utilities for decorating python unittests.
This is used by the "py:" runner of coursework.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass
from unittest import TestCase


class Assignment(TestCase):
    """
    # Assignment.

    An assignment is a special class used to create unittest-style assessments.
    Assignment includes semantics for collecting all test cases and for running said test cases.
    """

    @dataclass
    class _Assessment:
        """
        A private dataclass used to model an assessment test case.
        """

        name: str
        method: TestCase
        points: int
        hint: str = ""

    def __init_subclass__(cls):
        cls.__assessments__ = [
            cls._Assessment(
                name=getattr(func, "__testname__", name),
                method=cls(name),
                points=func.__points__,
                hint=getattr(func, "__hint__", ""),
            )
            for name in dir(cls)
            if name.startswith("test_") and callable(func := getattr(cls, name, None)) and hasattr(func, "__points__")
        ]


def points(value: int):
    """Set the number of points to award/lose for this test case."""

    def inner(func: typing.Callable):
        func.__points__ = value

        return func

    return inner


def name(value: str):
    """Set an optional name for the test."""

    def inner(func: typing.Callable):
        func.__testname__ = value

        return func

    return inner


def hint(value: str):
    """Provide an optional hint to show the student."""

    def inner(func: typing.Callable):
        func.__hint__ = value

        return func

    return inner
