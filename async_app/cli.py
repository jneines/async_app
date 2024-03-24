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
from async_app.messenger import messenger
import async_app.state as app_state  # to make app_state.keep_running a singleton


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
    await messenger.publish("async_app:ts", ts)


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
def main(args=None):
    """Console script for async_app."""

    max_runtime = 5

    app = AsyncApp("my_async_app")
    signal.signal(signal.SIGINT, app.exit)

    app.add_periodical(app.task_monitor, 1)
    app.add_periodical(process_monitor, 2)
    app.add_periodical(system_monitor, 2)

    app.add_task(waiter, 2 / 10 * max_runtime)
    app.add_task(waiter, 4 / 10 * max_runtime)
    app.add_task(waiter, 6 / 10 * max_runtime)
    app.add_task(waiter, 8 / 10 * max_runtime)

    app.add_task(sleeper)
    app.add_periodical(publish_ts, 1)
    app.add_task(exceptional, max_runtime)
    app.add_task(exit_task, max_runtime)

    return asyncio.run(app.run(), debug=True)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
