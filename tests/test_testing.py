"""
test_testing.py
Ian Kollipara <ian.kollipara@cune.edu>
2025-01-03

Test coursework.testing
"""

from unittest import TestCase

from coursework import testing


class TestAssignment(TestCase):
    def test_gather_assessments(self):
        class ExampleAssignment(testing.Assignment):
            @testing.name("My test case")
            @testing.hint("This should always pass!")
            @testing.points(15)
            def test_example_test(self):
                self.assertTrue(True)

        self.assertEqual(len(ExampleAssignment.__assessments__), 1)
        self.assertEqual(ExampleAssignment.__assessments__[0].points, 15)
        self.assertEqual(ExampleAssignment.__assessments__[0].name, "My test case")
        self.assertEqual(ExampleAssignment.__assessments__[0].hint, "This should always pass!")
        self.assertTrue(callable(ExampleAssignment.__assessments__[0].method))
