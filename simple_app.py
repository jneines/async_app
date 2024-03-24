import asyncio

import click

from async_app.logger import logger, set_verbosity
from async_app.app import AsyncApp
from async_app.app_factory import async_app_options
from async_app.tools import process_monitor, system_monitor
import async_app.state as app_state


def say_hello():
    print("Hello")


async def say_good_bye(after=3):
    await asyncio.sleep(after)
    print("GoodBye")
    app_state.keep_running = False


@click.command()
@async_app_options
@click.option(
    "-s",
    "--say-hello-frequency",
    type=int,
    default=1,
    show_default=True,
    help="Set 'say_hello' frequency in Hz. '0' means to not call the callback",
)
@click.option(
    "-a",
    "--after",
    type=int,
    default=3,
    show_default=True,
    help="Say GoodBye after 'after' seconds.",
)
def main(*args, **kwargs):
    logger.debug(f"{args=}")

    # All click options will end up in kwargs
    logger.debug(f"{kwargs=}")

    # create the app
    app = AsyncApp("simple_app")

    # map defaults
    process_monitoring_frequency = kwargs["process_monitoring_frequency"]
    system_monitoring_frequency = kwargs["system_monitoring_frequency"]
    task_monitoring_frequency = kwargs["task_monitoring_frequency"]

    # add provided tasks
    app.add_periodical(process_monitor, process_monitoring_frequency)
    app.add_periodical(system_monitor, system_monitoring_frequency)
    app.add_periodical(app.task_monitor, task_monitoring_frequency)

    # defaults for own tasks
    say_hello_frequency = kwargs["say_hello_frequency"]
    after = kwargs["after"]

    # add own tasks
    app.add_periodical(say_hello, say_hello_frequency)
    app.add_task(say_good_bye, after)

    # run the app

    asyncio.run(app.run(), debug=True)


if __name__ == "__main__":
    main()
