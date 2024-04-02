#!/usr/bin/env python

"""Tests for `async_app` package."""


import unittest

from async_app.app import AsyncApp

class TestAddTaskDescriptions(unittest.TestCase):

    def test_add_one_continuous_task(self):
        task_descriptions = [
                {
                    "kind": "continuous",
                    "function": lambda :print("Hello"),
                    }
                ]
        app = AsyncApp()
        for task_description in task_descriptions:
            app.add_task_description(task_description)

        self.assertEqual(len(app.task_descriptions["continuous"]), 1)

    def test_add_one_periodic_task(self):
        task_descriptions = [
                {
                    "kind": "periodic",
                    "function": lambda :print("Hello"),
                    "frequency": 1,
                    }
                ]
        app = AsyncApp()
        for task_description in task_descriptions:
            app.add_task_description(task_description)

        self.assertEqual(len(app.task_descriptions["periodic"]), 1)


