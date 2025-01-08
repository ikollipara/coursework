"""
test_cli_instructor.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-08

test coursework.cli.instructor
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from click.testing import CliRunner

from coursework.cli.instructor import cli
from coursework.cli.student import cli as student_cli


class TestInstructorCli(TestCase):
    def setUp(self):
        self.temp_dir = Path(self.enterContext(TemporaryDirectory()))
        self.config_buffer__ok = "\n".join(
            [
                "[coursework]",
                'admins = ["ian"]',
                'admin_group = "ian"',
                'submission = "' + str(self.temp_dir) + '/{student}/{course}/{assignment}"',
                'collection =  "' + str(self.temp_dir) + '/collection/{instructor}/{course}/{assignment}"',
                "",
                "[courses.cs141]",
                'instructors = ["ian"]',
                'students = ["ian", "not_real"]',
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
        self.config_buffer__bad = "\n".join(
            [
                "[coursework]",
                "admins = []",
                'admin_group = "ian"',
                'submission = "' + str(self.temp_dir) + '/{student}/{course}/{assignment}"',
                'collection =  "' + str(self.temp_dir) + '/collection/{instructor}/{course}/{assignment}"',
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
        (self.temp_dir / "coursework.toml").write_text(self.config_buffer__ok)
        (self.temp_dir / "coursework_bad.toml").write_text(self.config_buffer__bad)
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
        self.config__ok = str((self.temp_dir / "coursework.toml").absolute())
        self.config__bad = str((self.temp_dir / "coursework_bad.toml").absolute())
        self.runner = CliRunner()

    def test_if_not_admin(self):
        result = self.runner.invoke(cli, ["edit"], env={"COURSEWORK_CONFIG": self.config__bad})

        self.assertIn("You are not an admin!", result.stdout)

    def test_edit(self):
        result = self.runner.invoke(cli, ["edit"], env={"COURSEWORK_CONFIG": self.config__ok})

        self.assertIn("Edits saved", result.output)

    def test_report(self):
        result = self.runner.invoke(
            student_cli,
            ["submit", "cs141", "assignment1", str(self.temp_dir / "example.txt")],
            env={"COURSEWORK_CONFIG": self.config__ok},
        )
        result = self.runner.invoke(cli, ["report", "cs141", "assignment1"], env={"COURSEWORK_CONFIG": self.config__ok})
        self.assertIn("Reports generated!", result.output)
        self.assertIn("not_real has not submitted assignment1", result.output)
        self.assertIn(
            str(self.temp_dir / "collection" / "ian" / "cs141" / "assignment1" / "ian.pdf"),
            [str(file) for file in self.temp_dir.rglob("*")],
        )
