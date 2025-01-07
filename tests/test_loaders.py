"""
test_loaders.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-02

Test coursework.loaders
"""

import io
from unittest import TestCase

from coursework import loaders


class TestConfiguration(TestCase):
    def setUp(self):
        self.correct_toml = "\n".join(
            [
                "[coursework]",
                'admins = ["ian"]',
                'submission = "/tmp/{student}/{course}/{assignment}"',
                'collection = "/tmp/{instructor}/{course}/{assignment}"',
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
                'test = "cmd:test_script.sh" # "py:my_assignment"',
            ]
        ).encode()
        self.key_error_toml = "\n".join(
            [
                "[coursework]",
                'admins = ["ian"]',
                'submission = "/tmp/{student}/{course}/{assignment}"',
                'collection = "/tmp/{instructor}/{course}/{assignment}"',
                "",
                "[courses.cs141]",
                'instructors = ["ian"]',
                'students = ["ian"]',
                'assignments = ["assignment2"]',
                "",
                "",
                "[assignments.assignment1]",
                'description = "My first assignment"',
                'due_date = "2025-01-06 14:00"',
                "total_points = 15",
                'test = "cmd:test_script.sh" # "py:my_assignment"',
            ]
        ).encode()
        self.value_error_toml = "\n".join(
            [
                "[coursework]",
                'admins = ["ian"]',
                'submission = "/tmp/{student}/{course}/{assignment}"',
                'collection = "/tmp/{instructor}/{course}/{assignment}"',
                "",
                "[courses.cs141]",
                'instructors = ["ian"]',
                'students = ["ian"]',
                'assignments = ["assignment1"]',
                "",
                "",
                "[assignments.assignment1]",
                'description = "My first assignment"',
                'due_date = "Invalid date"',
                "total_points = 15",
                'test = "cmd:test_script.sh" # "py:my_assignment"',
            ]
        ).encode()
        self.warning_toml = "\n".join(
            [
                "[coursework]",
                'admins = ["ian"]',
                'submission = "/tmp/{student}/{course}/{assignment}"',
                'collection = "/tmp/{instructor}/{course}/{assignment}"',
            ]
        ).encode()
        self.fp = io.BytesIO()

    def test_load_from_toml__success(self):
        self.fp.write(self.correct_toml)
        self.fp.seek(0)

        result = loaders.Configuration.from_toml(self.fp)

        self.assertIsInstance(result, loaders.Configuration)
        self.assertIn("ian", result.admins)

    def test_load_from_toml__value_error(self):
        self.fp.write(self.value_error_toml)
        self.fp.seek(0)

        with self.assertRaises(loaders.ImproperlyConfigured):
            loaders.Configuration.from_toml(self.fp)

    def test_load_from_toml__key_error(self):
        self.fp.write(self.key_error_toml)
        self.fp.seek(0)

        with self.assertRaises(loaders.ImproperlyConfigured):
            loaders.Configuration.from_toml(self.fp)

    def test_load_from_toml__warning(self):
        self.fp.write(self.warning_toml)
        self.fp.seek(0)

        with self.assertWarns(UserWarning):
            loaders.Configuration.from_toml(self.fp)


class TestUser(TestCase):
    def setUp(self):
        correct_toml = "\n".join(
            [
                "[coursework]",
                'admins = ["ian"]',
                'submission = "/tmp/{student}/{course}/{assignment}"',
                'collection = "/tmp/{instructor}/{course}/{assignment}"',
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
                'test = "cmd:test_script.sh" # "py:my_assignment"',
            ]
        ).encode()
        fp = io.BytesIO()
        fp.write(correct_toml)
        fp.seek(0)
        self.configuration = loaders.Configuration.from_toml(fp)

    def test_from_env(self):
        user = loaders.User.from_env(self.configuration, name="ian")
        self.assertIsInstance(user, loaders.User)
        self.assertTrue(user.is_instructor)
