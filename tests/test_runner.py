"""
test_runner.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-03

Test coursework.runner
"""

from datetime import datetime
from os import close
from os import devnull
from os import write
from pathlib import Path
from tempfile import mkstemp
from unittest import TestCase

from rich.console import Console

from coursework import runner
from coursework.loaders import Configuration
from coursework.loaders import TestSpec
from coursework.loaders import User


class TestPythonUnittestRunner(TestCase):
    def setUp(self):
        test_assignment_fd, test_example_file = mkstemp()
        test_assignment_file = Path(test_example_file)
        self.addCleanup(lambda: close(test_assignment_fd))
        self.addCleanup(test_assignment_file.unlink)
        write(
            test_assignment_fd,
            "\n".join(
                [
                    "from coursework.testing import Assignment, points, name",
                    "from coursework import testing",
                    "",
                    "class MyAssignment(Assignment):",
                    "    @points(15)",
                    "    def test_should_fail(self):",
                    "        self.assertEqual(1, 2)",
                    "",
                    "    @points(15)",
                    "    def test_should_pass(self):",
                    "        self.assertEqual(1, 1)",
                    "",
                    "    @name('This test should error')",
                    "    @points(15)",
                    "    def test_should_error(self):",
                    "        raise Exception()",
                ]
            ).encode(),
        )
        example_file_fd, self.example_file = mkstemp()
        self.example_file = Path(self.example_file)
        self.addCleanup(lambda: close(example_file_fd))
        self.addCleanup(self.example_file.unlink)
        write(example_file_fd, b"Example Test")

        self.assignment = Configuration.Assignment(
            "My assignment",
            "My assignment desc.",
            datetime.now(),
            45,
            TestSpec("py", str(test_assignment_file.absolute())),
        )
        self.course = Configuration.Course("My course", ["ian"], ["ian"], {"My assignment": self.assignment})
        self.user = User("ian", "student")
        self.devnull = Path(devnull).open("w")
        self.addCleanup(self.devnull.close)

    def test_run(self):
        console = Console(file=self.devnull)
        test_runner = runner.PythonUnittestRunner(self.user, self.course, self.assignment, [self.example_file])
        result = test_runner.run(console)

        self.assertEqual(len(result.test_case_results), 3)
        self.assertEqual(result.assignment, self.assignment)


class TestRunnerHelpers(TestCase):
    def test_get_runner_by_name__success(self):
        self.assertTrue(issubclass(runner.get_runner_by_name("py"), runner.Runner))

    def test_get_runner_by_name__fail(self):
        with self.assertRaises(runner.RunnerNotFound):
            runner.get_runner_by_name("not_a_runner")
