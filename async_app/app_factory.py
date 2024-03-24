#!/usr/bin/env python3
import sys
import functools

import click
from async_app.logger import logger, set_verbosity

_async_app_options = [
    click.option(
        "-v", "--verbose", count=True, callback=set_verbosity, help="Increase verbosity"
    ),
    click.option(
        "-pmf",
        "--process-monitoring-frequency",
        type=int,
        default=0,
        show_default=True,
        # callback=enable_process_monitoring,
        help="Set process monitoring frequency in Hz. '0' means to not monitor at all. ",
    ),
    click.option(
        "-smf",
        "--system-monitoring-frequency",
        type=int,
        default=0,
        show_default=True,
        # callback=enable_process_monitoring,
        help="Set system monitoring frequency in Hz. '0' means to not monitor at all. ",
    ),
    click.option(
        "-tmf",
        "--task-monitoring-frequency",
        type=int,
        default=0,
        show_default=True,
        # callback=enable_process_monitoring,
        help="Set task monitoring frequency in Hz. '0' means to not monitor at all. ",
    ),
]


def async_app_options(func):
    for option in reversed(_async_app_options):
        func = option(func)
    return func
