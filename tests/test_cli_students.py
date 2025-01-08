"""
test_cli_students.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-08

test coursework.cli.students
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from click.testing import CliRunner

from coursework.cli.student import cli


class TestStudentCli(TestCase):
    def setUp(self):
        self.temp_dir = Path(self.enterContext(TemporaryDirectory()))
        self.config_buffer = "\n".join(
            [
                "[coursework]",
                'admins = ["ian"]',
                'admin_group = "ian"',
                'submission = "' + str(self.temp_dir) + '/{student}/{course}/{assignment}"',
                'collection =  "' + str(self.temp_dir) + '/{instructor}/{course}/{assignment}"',
                "",
                "[courses.cs141]",
                'instructors = ["ian"]',
                'students = ["ian"]',
                'assignments = ["assignment1"]',
                "",
                "",
                "[assignments.assignment1]",
                'description = "My first assignment"',
                'due_date = "2025-01-06 14:00"',
                "total_points = 15",
                'test = "py:/tmp/my_assignment"',
            ]
        )
        (self.temp_dir / "coursework.toml").write_text(self.config_buffer)
        test_script = Path("/tmp/my_assignment")
        test_script.write_text(
            "\n".join(
                [
                    "from coursework import testing",
                    "",
                    "class MyAssignment(testing.Assignment):",
                    "    @testing.points(15)",
                    "    def test_should_fail(self):",
                    "        self.assertEqual(1, 2)",
                    "",
                    "    @testing.points(15)",
                    "    def test_should_pass(self):",
                    "        self.assertEqual(1, 1)",
                    "",
                    "    @testing.name('This test should error')",
                    "    @testing.points(15)",
                    "    def test_should_error(self):",
                    "        raise Exception()",
                ]
            )
        )
        self.addCleanup(test_script.unlink)
        (self.temp_dir / "example.txt").touch()
        self.config = str((self.temp_dir / "coursework.toml").absolute())
        self.runner = CliRunner()

    def test_list_assignments(self):
        result = self.runner.invoke(cli, ["list"], env={"COURSEWORK_CONFIG": self.config})

        self.assertIn("assignment1", result.stdout)

    def test_detail(self):
        result = self.runner.invoke(cli, ["detail", "cs141", "assignment1"], env={"COURSEWORK_CONFIG": self.config})

        self.assertIn("assignment1", result.output)

    def test_submit(self):
        result = self.runner.invoke(
            cli,
            ["submit", "cs141", "assignment1", str(self.temp_dir / "example.txt")],
            env={"COURSEWORK_CONFIG": self.config},
        )

        self.assertIn("assignment1 was successfully submitted!", result.output)
        self.assertIn(
            str(self.temp_dir / "ian" / "cs141" / "assignment1" / ".runner-output"),
            [str(file) for file in self.temp_dir.rglob("*")],
        )
        self.assertIn(
            str(self.temp_dir / "ian" / "cs141" / "assignment1" / "example.txt"),
            [str(file) for file in self.temp_dir.rglob("*")],
        )

    def test_submit_with_existing_submission__no(self):
        self.runner.invoke(
            cli,
            ["submit", "cs141", "assignment1", str(self.temp_dir / "example.txt")],
            env={"COURSEWORK_CONFIG": self.config},
        )

        result = self.runner.invoke(
            cli,
            ["submit", "cs141", "assignment1", str(self.temp_dir / "example.txt")],
            env={"COURSEWORK_CONFIG": self.config},
            input="n",
        )

        self.assertEqual(result.exit_code, 1)

    def test_submit_with_existing_submission__yes(self):
        self.runner.invoke(
            cli,
            ["submit", "cs141", "assignment1", str(self.temp_dir / "example.txt")],
            env={"COURSEWORK_CONFIG": self.config},
        )

        result = self.runner.invoke(
            cli,
            ["submit", "cs141", "assignment1", str(self.temp_dir / "example.txt")],
            env={"COURSEWORK_CONFIG": self.config},
            input="y",
        )

        self.assertIn("assignment1 was successfully submitted!", result.output)
        self.assertIn(
            str(self.temp_dir / "ian" / "cs141" / "assignment1" / ".runner-output"),
            [str(file) for file in self.temp_dir.rglob("*")],
        )
        self.assertIn(
            str(self.temp_dir / "ian" / "cs141" / "assignment1" / "example.txt"),
            [str(file) for file in self.temp_dir.rglob("*")],
        )
