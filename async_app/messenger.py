import json
from functools import wraps

import redis.asyncio as redis
import msgpack
import asyncio_atexit

from async_app.logger import logger
import async_app.state as app_state  # to make app_state.keep_running a singleton


__safe_exit = False


def safe_exit(f):
    """safe exit for redis connections.

    Used as a decorator, this implementation makes sure that the redis connection
    is closed before the asyncio event loop closes.

    The hook is executed only once, from the very first call in the running loop.
    """
    wraps(f)

    async def wrapper(*args, **kwargs):
        global messenger
        global __safe_exit
        if not __safe_exit:
            asyncio_atexit.register(messenger.exit)
            __safe_exit = True
            await f(*args, **kwargs)

    return wrapper


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

        self.redis = redis.Redis()

    async def exit(self):
        logger.info("Closing redis connection.")
        await self.redis.aclose()

    # Note: setting adds another thread
    @safe_exit
    async def set(self, namespace, data):
        await self.redis.set(namespace, self.packer(data))

    @safe_exit
    async def get(self, namespace):
        return self.unpacker(await self.redis.get(namespace))

    # Note: publishing adds another thread
    @safe_exit
    async def publish(self, namespace, data):
        await self.redis.publish(namespace, self.packer(data))

    @safe_exit
    async def listener(self, namespace, callback):
        async with self.redis.pubsub() as pubsub:
            await pubsub.subscribe(namespace)

            while app_state.keep_running:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    data = self.unpacker(message["data"])
                    callback(data)


messenger = Messenger("json")
