import sys
import os
import asyncio
import time
import json
from pathlib import Path

import psutil
import redis.asyncio as redis

from async_app.logger import logger
import async_app.state as app_state  # for keep_running to be singleton
import async_app.messenger as app_messenger


app_name = Path(sys.argv[0]).stem
app_env_prefix = app_name.upper()


log_indent_env_name = f"{app_env_prefix}_LOG_INDENT"
log_indent = os.environ.get(log_indent_env_name, None)
if log_indent:
    try:
        log_indent = int(log_indent)
    except (TypeError, ValueError) as e:
        logger.error(
            f"The value for the environment variable {log_indent_env_name} - if set - must be a positive integer number."
            f"Error message was {e}."
        )


async def process_monitor(
    attrs=["pid", "cpu_percent", "memory_percent", "num_fds", "num_threads"],
):
    # It's totally fine to have this blocking
    # In an Intel iMac 2019 this call just takes 10 ns.
    # Although for the same reason, it might not provide the results expected in an async environment

    p = psutil.Process()
    with p.oneshot():
        record = p.as_dict(attrs=attrs)

    await app_messenger.publish("async_app:app_monitor", record)
    await app_messenger.set("async_app:app_monitor", record)

    logger.debug(json.dumps(record, indent=log_indent))

    return record


async def cpu_monitor():
    record = {}
    p = psutil.Process()
    record[p.name()] = p.cpu_percent(0.1)
    for c in p.children():
        record[c.name()] = c.cpu_percent(0.1)

    logger.debug(json.dumps(record, indent=log_indent))


async def system_monitor(disk_usage_path="/"):
    mem_info = psutil.virtual_memory()
    disk_usage = psutil.disk_usage(disk_usage_path)
    record = {
        "cpu_percent": psutil.cpu_percent(),
        "mem_percent": mem_info.percent,
        "disk_percent": disk_usage.percent,
    }
    logger.debug(json.dumps(record, indent=log_indent))
    await app_messenger.publish("async_app:system_monitor", record)
    await app_messenger.set("async_app:system_monitor", record)

    return record
