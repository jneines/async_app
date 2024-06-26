import asyncio
import json
from functools import wraps
import os

import redis.asyncio as redis
import msgpack
import asyncio_atexit

from async_app.logger import logger
import async_app.state as app_state  # to make app_state.keep_running a singleton

# use most versatile approach as default. Set to 'json' for something more human readable
serializer = "msgpack"
if "ASYNC_APP_REDIS_SERIALIZER" in os.environ.keys():
    serializer = os.environ["ASYNC_APP_REDIS_SERIALIZER"]

logger.debug(f"Using {serializer=}")

# make sure a clean exit from redis is done
_clean_exit_enabled = False


if serializer == "msgpack":
    packer = msgpack.packb
    unpacker = msgpack.unpackb
else:
    packer = json.dumps
    unpacker = json.loads


_r = redis.Redis()


async def enable_clean_exit():
    global _clean_exit_enabled

    if _clean_exit_enabled:
        return
    asyncio_atexit.register(close_redis)
    _clean_exit_enabled = True


async def set(namespace, data):
    await enable_clean_exit()
    await _r.set(namespace, packer(data))


async def get(namespace):
    await enable_clean_exit()
    value = unpacker(await _r.get(namespace))
    return value


async def publish(namespace, data):
    await enable_clean_exit()
    await _r.publish(namespace, packer(data))


async def listener(namespace, callback):
    await enable_clean_exit()

    callback_is_async = True if asyncio.iscoroutinefunction(callback) else False

    async with _r.pubsub() as pubsub:
        await pubsub.subscribe(namespace)

        while app_state.keep_running:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message is not None:
                data = unpacker(message["data"])
                if callback_is_async:
                    await callback(data)
                else:
                    callback(data)
            else:
                # be nice to the system
                # TODO: make this configurable to allow adjusting the responsiveness
                await asyncio.sleep(0.05)


async def close_redis():
    await _r.aclose()
