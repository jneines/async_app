#!/usr/bin/env python3
import asyncio
from collections import deque
from collections import defaultdict
import json
import functools
import uuid
import time
import datetime as dt

import numpy as np
import asyncio_atexit

from async_app.logger import logger
from async_app.patterns import periodical
from async_app.tools import app_name, log_indent, process_monitor, system_monitor
import async_app.state as app_state  # for keep_running to make it singleton

import async_app.messenger as app_messenger


class AsyncApp(object):
    def __init__(self, **kwargs):
        self.name = app_name
        logger.info(f"Initializing AsyncApp {self.name}")

        logger.debug(f"My kwargs: {kwargs}")

        self.task_descriptions = {
            "init": [],
            "continuous": [],
            "periodic": [],
            "cleanup": [],
        }
        self.tasks = []
        self.results = []

        self.periodicals = {}
        self.periodicals_timing = {}
        self.periodicals_timing_maxlen = 21

        self.process_default_options(**kwargs)

    def process_default_options(self, **kwargs):
        logger.info("Processing default async_app options.")
        monitor_mapping = {
            "process_monitoring_frequency": process_monitor,
            "system_monitoring_frequency": system_monitor,
            "task_monitoring_frequency": self.task_monitor,
            "periodicals_monitoring_frequency": self.periodicals_monitor,
        }

        for key, monitoring_function in monitor_mapping.items():
            # if the async_app_options are not used, the expected values might not have been set.
            if not key in kwargs.keys():
                continue

            monitoring_frequency = kwargs[key]
            if monitoring_frequency > 0:
                task_description = {
                    "kind": "periodic",
                    "function": monitoring_function,
                    "frequency": monitoring_frequency,
                }
                self.add_task_description(task_description)

    def add_monitoring_ts(self, uid):
        self.periodicals_timing[uid].append(time.perf_counter())

    def add_task_description(self, task_description):
        """Add a task to todo list including args and kwargs."""
        logger.info(f"Adding new task with {task_description=}")
        task_description["name"] = task_description["function"].__name__
        task_description["uid"] = str(uuid.uuid4())

        # normalize task descriptions. Make sure expected properties exist
        # re-write task kinds
        kind = task_description["kind"]
        if kind.lower() in ("init", "initialize"):
            task_description["kind"] = "init"
            self.task_descriptions["init"].append(task_description)
        elif kind.lower() in ("continuous", "continuously"):
            task_description["kind"] = "continuous"
            self.task_descriptions["continuous"].append(task_description)
        elif kind.lower() in ("periodic", "periodical", "periodically"):
            task_description["kind"] = "periodic"

            if "call_every" in task_description.keys():
                task_description["frequency"] = 1 / task_description["call_every"]

            self.task_descriptions["periodic"].append(task_description)
        elif kind.lower() in ("cleanup", "teardown"):
            task_description["kind"] = "cleanup"
            self.task_descriptions["cleanup"].append(task_description)
        else:
            logger.error(f"Unknown task kind '{kind}' detected. Not adding task.")
            return

    async def create_tasks(self, kind):
        """Initialize tasks of kind 'kind'."""
        # filter for relevant tasks
        task_descriptions = self.task_descriptions[kind]
        print(task_descriptions)

        tasks = []
        for task_description in task_descriptions:
            logger.debug(f"Creating asyncio task for {task_description=}")

            # mandatory properties for 'continuous' and 'periodical' tasks
            kind = task_description["kind"]
            function = task_description["function"]
            name = task_description["name"]
            uid = task_description["uid"]

            # optional properties
            args = task_description.get("args", ())
            kwargs = task_description.get("kwargs", {})

            # derived properties
            f_is_async = asyncio.iscoroutinefunction(function)

            if kind == "init":
                if f_is_async:
                    task = asyncio.create_task(function(*args, **kwargs), name=name)
                else:
                    task = asyncio.create_task(
                        asyncio.to_thread(function(*args, **kwargs)), name=name
                    )
                # self.model["init"]["tasks"].append(task)
                tasks.append(task)

            elif kind == "continuous":
                if f_is_async:
                    task = asyncio.create_task(function(*args, **kwargs), name=name)
                else:
                    task = asyncio.create_task(
                        asyncio.to_thread(function(*args, **kwargs)), name=name
                    )
                # self.model["main"]["tasks"].append(task)
                tasks.append(task)

            elif kind == "periodic":
                # mandatory properties for 'periodical' tasks
                frequency = task_description["frequency"]

                # optional properties for 'periodical' tasks
                monitor = task_description.get("monitor", False)

                if monitor:
                    # add callback to monitor performance
                    self.periodicals_timing[uid] = deque(
                        [float("nan")] * self.periodicals_timing_maxlen,
                        maxlen=self.periodicals_timing_maxlen,
                    )
                    monitoring_callback = functools.partial(self.add_monitoring_ts, uid)
                else:
                    monitoring_callback = None
                task = asyncio.create_task(
                    periodical(frequency, monitoring_callback)(function)(
                        *args, **kwargs
                    ),
                    name=name,
                )
                tasks.append(task)
                # self.model["main"]["tasks"].append(task)
                self.periodicals[uid] = name
            elif kind == "cleanup":
                cleanup_function = functools.partial(function, *args, **kwargs)
                asyncio_atexit.register(cleanup_function)

            else:
                # will never be reached
                logger.warning(
                    f"Unknown task kind detected: {kind=}. Task will not be executed!"
                )

        # extend self.tasks for the task monitor to work properly
        self.tasks.extend(tasks)
        return tasks

    async def run_tasks(self, tasks):
        """Run tasks of kind 'kind'."""

        logger.info(f"Processing tasks")

        try:
            for coro in asyncio.as_completed(tasks):
                try:
                    await coro
                    status = "completed"
                except Exception as e:
                    status = "failed"
                finally:
                    task_name = coro.__name__
                    now = dt.datetime.now()
                    logger.debug(f"Task {task_name} {status} at {now.isoformat()}")

        except asyncio.CancelledError:
            logger.info(f"Task {task_name} was cancelled")

    async def run(self):
        # make sure to initialize cleanup tasks first
        tasks = await self.create_tasks("cleanup")

        # Next would be init tasks run first
        tasks = await self.create_tasks("init")
        await self.run_tasks(tasks)

        # only after that run the main tasks
        continuous_tasks = await self.create_tasks("continuous")
        periodic_tasks = await self.create_tasks("periodic")
        await self.run_tasks(continuous_tasks + periodic_tasks)

        logger.info("All work is done. Here's the outcome")
        # logger.info(f"Results: {json.dumps(self.results, indent=log_indent)}")

        results = []
        for task in self.tasks:
            result = {
                "name": task.get_name(),
                "result": None,
                "exception": None,
            }
            try:
                # In case of a manual exit, before anything has been completed, neither an exception nor a result has been set
                # querying these will lead to an exception ...
                if not task.exception():
                    result["result"] = task.result()
                else:
                    result["exception"] = str(task.exception())
            except asyncio.exceptions.InvalidStateError:
                logger.warning(
                    f"Task {task.get_name()} could not be queried for results or exceptions."
                )
            finally:
                results.append(result)
        logger.info(f"Results: {json.dumps(results, indent=log_indent)}")

    async def task_monitor(self):
        """A tasks monitor."""
        tasks_running = []
        tasks_done = []
        tasks_failed = []

        for task in self.tasks:
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
        logger.debug(json.dumps(record, indent=4))
        await app_messenger.publish(f"{app_name}:task_monitor", record)
        await app_messenger.set(f"{app_name}:task_monitor", record)

    def periodicals_monitor(self):
        record = {}
        for _uuid, periodical_timing in self.periodicals_timing.items():
            ts = np.array(periodical_timing)
            f = 1 / np.diff(ts).mean()
            task_name = self.periodicals[_uuid]
            record[task_name] = f
        logger.debug(json.dumps(record, indent=log_indent))

    def exit(self, *args):
        """Exit hook."""
        logger.info("Exit requested. GoodBye")
        app_state.keep_running = False
