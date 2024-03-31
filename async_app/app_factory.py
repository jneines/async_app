#!/usr/bin/env python3
import sys
import functools

import click

from async_app.logger import logger, set_verbosity
from async_app.app import AsyncApp

_async_app_options = [
    click.option(
        "-v",
        "--verbose",
        envvar="VERBOSE",
        count=True,
        callback=set_verbosity,
        help="Increase verbosity",
    ),
    click.option(
        "-pmf",
        "--process-monitoring-frequency",
        envvar="PROCESS_MONITORING_FREQUENCY",
        type=int,
        default=0,
        show_default=True,
        help="Set process monitoring frequency in Hz. '0' means to not monitor at all. ",
    ),
    click.option(
        "-smf",
        "--system-monitoring-frequency",
        envvar="SYSTEM_MONITORING_FREQUENCY",
        type=int,
        default=0,
        show_default=True,
        help="Set system monitoring frequency in Hz. '0' means to not monitor at all. ",
    ),
    click.option(
        "-tmf",
        "--task-monitoring-frequency",
        envvar="TASK_MONITORING_FREQUENCY",
        type=int,
        default=0,
        show_default=True,
        help="Set task monitoring frequency in Hz. '0' means to not monitor at all. ",
    ),
    click.option(
        "-rmf",
        "--periodicals-monitoring-frequency",
        envvar="PERIODICALS_MONITORING_FREQUENCY",
        type=int,
        default=0,
        show_default=True,
        help="Set periodicals monitoring frequency in Hz. '0' means to not monitor at all. ",
    ),
]


def async_app_options(func):
    for option in reversed(_async_app_options):
        func = option(func)
    return func
