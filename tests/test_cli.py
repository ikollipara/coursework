"""
test_cli.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-03

Test coursework.cli
"""

import tempfile
from io import BytesIO
from pathlib import Path
from shutil import rmtree
from unittest import TestCase

from click import testing

from coursework.cli import cli


class TestCli(TestCase):
    def setUp(self):
        self.working_dir = Path(tempfile.mkdtemp())
        self.config_buffer = BytesIO(
            b"\n".join(
                [
                    b"[coursework]",
                    b'admins = ["ian"]',
                    b'submission = "/tmp/{student}/{course}/{assignment}"',
                    b'collection = "/tmp/{instructor}/{course}/{assignment}"',
                    b"",
                    b"[courses.cs141]",
                    b'instructors = ["ian"]',
                    b'students = ["ian"]',
                    b'assignments = ["assignment1"]',
                    b"",
                    b"",
                    b"[assignments.assignment1]",
                    b'description = "My first assignment"',
                    b'due_date = "2025-01-06 14:00"',
                    b"total_points = 15",
                    b'test = "cmd:test_script.sh" # "py:my_assignment"',
                ]
            )
        )

        (self.working_dir / "coursework.toml").write_bytes(self.config_buffer.getbuffer())
        self.addCleanup(lambda: rmtree(self.working_dir, ignore_errors=True))

    def test_cli_version(self):
        runner = testing.CliRunner(env={"COURSEWORK_CONFIG": str(self.working_dir / "coursework.toml")})

        with runner.isolated_filesystem(self.working_dir):
            result = runner.invoke(cli, ["--version"])
            self.assertIn("0.0.1", result.stdout)
