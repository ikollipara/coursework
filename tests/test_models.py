"""
test_models.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-02

Test coursework.models
"""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from tempfile import mktemp
from unittest import TestCase

from coursework import loaders
from coursework import models


class TestTestCaseResult(TestCase):
    def setUp(self):
        self.fp = BytesIO()
        self.path = Path(mktemp())
        self.path.touch(exist_ok=True)
        self.addCleanup(self.path.unlink)

    def test_to_pickle__fp(self):
        instance = models.TestCaseResult("My test case", True, 15)
        instance.to_pickle(self.fp)

        self.assertGreater(self.fp.tell(), 0)

    def test_to_pickle__path(self):
        instance = models.TestCaseResult("My test case", True, 15)
        instance.to_pickle(self.path)

        self.assertGreater(len(self.path.read_bytes()), 0)

    def test_from_pickle__fp(self):
        instance = models.TestCaseResult("My test case", True, 15)
        instance.to_pickle(self.fp)
        self.fp.seek(0)

        resolved_instance = models.TestCaseResult.from_pickle(self.fp)

        self.assertIsInstance(resolved_instance, models.TestCaseResult)

    def test_from_pickle__path(self):
        instance = models.TestCaseResult("My test case", True, 15)
        instance.to_pickle(self.path)

        resolved_instance = models.TestCaseResult.from_pickle(self.path)

        self.assertIsInstance(resolved_instance, models.TestCaseResult)


class TestRunnerResult(TestCase):
    def setUp(self):
        self.user = loaders.User("ian", "instructor")
        self.course = loaders.Configuration.Course("cs141", ["ian"], ["ian"], ["assignment1"])
        self.assignment = loaders.Configuration.Assignment(
            "assignment1", "My assignment", datetime.now(), 15, ("cmd", "my_script.sh")
        )
        self.fp = BytesIO()
        self.path = Path(mktemp())
        self.path.touch(exist_ok=True)
        self.addCleanup(self.path.unlink)

    def test_to_pickle__fp(self):
        instance = models.RunnerResult(self.user, datetime.now(), self.course, self.assignment)
        instance.to_pickle(self.fp)

        self.assertGreater(self.fp.tell(), 0)

    def test_to_pickle__path(self):
        instance = models.RunnerResult(self.user, datetime.now(), self.course, self.assignment)
        instance.to_pickle(self.path)

        self.assertGreater(len(self.path.read_bytes()), 0)

    def test_from_pickle__fp(self):
        instance = models.RunnerResult(self.user, datetime.now(), self.course, self.assignment)
        instance.to_pickle(self.fp)
        self.fp.seek(0)

        resolved_instance = models.RunnerResult.from_pickle(self.fp)

        self.assertIsInstance(resolved_instance, models.RunnerResult)

    def test_from_pickle__path(self):
        instance = models.RunnerResult(self.user, datetime.now(), self.course, self.assignment)
        instance.to_pickle(self.path)

        resolved_instance = models.RunnerResult.from_pickle(self.path)

        self.assertIsInstance(resolved_instance, models.RunnerResult)
