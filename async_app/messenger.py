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


async def close_redis():
    await _r.aclose()


"""

class Messenger(object):
    def __init__(self, engine="msgpack"):
        self.engine = engine
        if engine == "msgpack":
            self.packer = msgpack.packb
            self.unpacker = msgpack.unpackb
        else:
            logger.warning(
                "The json based packer approach cannot serialize binary objects"
            )
            self.packer = json.dumps
            self.unpacker = json.loads

    # Note: setting adds another thread
    async def set(self, namespace, data):
        r = redis.Redis()
        await r.set(namespace, self.packer(data))
        await r.aclose()

    async def get(self, namespace):
        r = redis.Redis()
        value = self.unpacker(await r.get(namespace))
        await r.aclose()
        return value

    # Note: publishing adds another thread
    async def publish(self, namespace, data):
        r = redis.Redis()
        await r.publish(namespace, self.packer(data))
        await r.aclose()

    async def listener(self, namespace, callback):
        callback_is_async = True if asyncio.iscoroutinefunction(callback) else False

        r = redis.Redis()

        async with r.pubsub() as pubsub:
            await pubsub.subscribe(namespace)

            while app_state.keep_running:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    data = self.unpacker(message["data"])
                    if callback_is_async:
                        await callback(data)
                    else:
                        callback(data)
        await r.aclose()


json_messenger = Messenger("json")
messenger = Messenger()

"""
