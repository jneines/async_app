"""Console script for async_app.

Meant for demonstration only.
"""

import sys
import time
import random
import asyncio

import click
import signal

from async_app.logger import logger
from async_app.app import AsyncApp
from async_app.tools import process_monitor, system_monitor
import async_app.messenger as app_messenger
import async_app.state as app_state  # to make app_state.keep_running a singleton

# from async_app.app_factory import async_app_options


#
# some sample tasks
#


async def waiter(wait_for=2):
    """A waiting task."""
    logger.info(f"Will wait for {wait_for} seconds, and then exit.")
    await asyncio.sleep(wait_for)

    return "Done with waiting"


async def sleeper(sleep_for=0.5):
    """A repeating sleeper task."""
    while app_state.keep_running:
        logger.info(f"Message from the sleeper: Sleeping for {sleep_for} seconds.")
        await asyncio.sleep(sleep_for)


async def publish_ts():
    """Publish the current timestamp."""
    ts = time.time()
    await app_messenger.publish("async_app:ts", ts)


async def exceptional(max_runtime):
    """A Task that throws an exception."""
    await asyncio.sleep(max_runtime * random.random())
    1 / 0


async def exit_task(exit_after=10):
    """An exit task."""
    await asyncio.sleep(exit_after)
    logger.warning("Now exiting")
    app_state.keep_running = False


@click.command()
# @async_app_options
def main():
    """Console script for async_app."""

    max_runtime = 5

    app = AsyncApp()
    signal.signal(signal.SIGINT, app.exit)
    task_descriptions = [
        {
            "kind": "periodic",
            "function": app.task_monitor,
            "frequency": 1,
        },
        {
            "kind": "periodic",
            "function": process_monitor,
            "frequency": 2,
        },
        {
            "kind": "periodic",
            "function": system_monitor,
            "frequency": 2,
        },
        {
            "kind": "continuous",
            "function": waiter,
            "args": (2 / 10 * max_runtime,),
        },
        {
            "kind": "continuous",
            "function": waiter,
            "args": (4 / 10 * max_runtime,),
        },
        {
            "kind": "continuous",
            "function": waiter,
            "args": (6 / 10 * max_runtime,),
        },
        {
            "kind": "continuous",
            "function": waiter,
            "args": (8 / 10 * max_runtime,),
        },
        {
            "kind": "continuous",
            "function": sleeper,
        },
        {
            "kind": "periodical",
            "function": publish_ts,
            "frequency": 1,
        },
        {
            "kind": "continuous",
            "function": exceptional,
            "args": (max_runtime,),
        },
        {
            "kind": "continuous",
            "function": exit_task,
            "args": (max_runtime,),
        },
    ]

    for task_description in task_descriptions:
        app.add_task_description(task_description)

    return asyncio.run(app.run(), debug=True)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
