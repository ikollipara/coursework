"""
test_score.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-07

Test coursework.score
"""

from tempfile import NamedTemporaryFile
from unittest import TestCase

from click.testing import CliRunner

from coursework.models import TestCaseResult
from coursework.score import main as score_cli


class TestScore(TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def test_main(self):
        file = self.enterContext(NamedTemporaryFile("ab+"))
        self.runner.invoke(score_cli, ["My test", "10", "t"], env={"COURSEWORK_RUNNER_OUTPUT": file.name})

        for line in file.read().split(b"SPLIT")[:-1]:
            r = TestCaseResult.from_pickle(line)

        self.assertEqual(r.name, "My test")
        self.assertEqual(r.points, 10)
        self.assertTrue(r.was_successful)
