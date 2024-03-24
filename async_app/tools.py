import asyncio
import time
import json

import psutil
import redis.asyncio as redis

from async_app.logger import logger
import async_app.state as app_state  # for keep_running to be singleton
from async_app.messenger import messenger


async def process_monitor(
    attrs=["pid", "cpu_percent", "memory_percent", "num_fds", "num_threads"]
):
    # It's totally fine to have this blocking
    # In an Intel iMac 2019 this call just takes 10 ns.

    p = psutil.Process()
    with p.oneshot():
        record = p.as_dict(attrs=attrs)
        logger.debug(json.dumps(record, indent=4))
        await messenger.publish("async_app:app_monitor", record)
        await messenger.set("async_app:app_monitor", record)

        return record


async def system_monitor(disk_usage_path="/"):
    mem_info = psutil.virtual_memory()
    disk_usage = psutil.disk_usage(disk_usage_path)
    record = {
        "cpu_percent": psutil.cpu_percent(),
        "mem_percent": mem_info.percent,
        "disk_percent": disk_usage.percent,
    }
    logger.debug(json.dumps(record, indent=4))
    await messenger.publish("async_app:system_monitor", record)
    await messenger.set("async_app:system_monitor", record)

    return record


async def monitoring(
    update_frequency=1,
    attrs=["pid", "cpu_percent", "memory_percent", "num_fds", "num_threads"],
):
    call_every = 1 / update_frequency

    while app_state.keep_running:
        tic = time.perf_counter()
        record = monitor(attrs)
        logger.debug(json.dumps(record, indent=4))

        toc = time.perf_counter()

        logger.info("Still monitoring")
        sleep_for = max(0, call_every - (toc - tic))
        await asyncio.sleep(sleep_for)
