#!/usr/bin/env python3
import asyncio
from collections import defaultdict
import json

from async_app.logger import logger
from async_app.patterns import periodical
from async_app.tools import process_monitor, system_monitor
import async_app.state as app_state  # for keep_running to make it singleton
from async_app.messenger import messenger


class AsyncApp(object):
    def __init__(self, name=None):
        self.name = name if name is not None else self.__class__.__name__
        logger.info(f"Initializing AsyncApp {self.name}")

        self.tasks = []
        self.__tasks = set()
        self.results = defaultdict(list)
        self.exceptions = defaultdict(list)

    def add_task(self, task, *args, **kwargs):
        """Add a task to todo list including args and kwargs."""
        logger.info(f"Adding {task=} with {args=} and {kwargs=}")
        self.tasks.append((task, args, kwargs))

    def add_periodical(self, callback, update_frequency):
        """Add a periodical task."""
        logger.info(f"Creating periodical task for {callback.__name__}")
        if update_frequency > 0:
            __task = periodical(update_frequency)(callback)
            self.add_task(__task)

    async def task_monitor(self):
        """A task monitor."""
        tasks_running = []
        tasks_done = []
        tasks_failed = []

        for task in self.__tasks:
            task_name = task.get_name()
            if task.done():
                if task.exception():
                    tasks_failed.append(task_name)
                else:
                    tasks_done.append(task_name)
            else:
                tasks_running.append(task_name)

        record = {
            "running": {
                "count": len(tasks_running),
                "tasks": tasks_running,
            },
            "done": {
                "count": len(tasks_done),
                "tasks": tasks_done,
            },
            "failed": {
                "count": len(tasks_failed),
                "tasks": tasks_failed,
            },
        }
        logger.debug(json.dumps(record))
        await messenger.publish("async_app:task_monitor", record)
        await messenger.set("async_app:task_monitor", record)

    async def run(self):
        """as_completed based main run method."""
        logger.info("Entering async_apps run.")

        logger.info("Creating asyncio tasks")
        for task, args, kwargs in self.tasks:
            logger.debug(f"Creating asyncio task for {task.__name__}")
            _task = asyncio.create_task(task(*args, **kwargs), name=task.__name__)
            self.__tasks.add(_task)

        logger.info("Waiting for tasks to finish")
        try:
            for coro in asyncio.as_completed(self.__tasks):
                task_name = coro.__name__
                try:
                    result = await coro
                    logger.warning(f"Task {task_name} completed with {result=}")
                    self.results[task_name].append(result)
                except Exception as e:
                    logger.error(f"Task failed with an exception: {e}.")
                    self.exceptions[task_name].append(repr(e))
        except asyncio.CancelledError:
            logger.info(f"Task {task_name} was cancelled")

        logger.info("All work is done. Here's the outcome")
        logger.info(f"Results: {json.dumps(self.results, indent=4)}")
        logger.info(f"Exceptions: {json.dumps(self.exceptions, indent=4)}")

    def exit(self, *args):
        """Exit hook."""
        logger.info("Exit requested. GoodBye")
        app_state.keep_running = False
