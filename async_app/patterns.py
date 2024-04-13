import asyncio
import time
from functools import wraps

from async_app.logger import logger
import async_app.state as app_state  # to make app_state.keep_running a singleton


def every(every):
    return 1 / frequency


def frequency(frequency):
    return frequency


def periodical(frequency=1, monitoring_cb=None):
    """A decorator to call a function periodically"""

    call_every = 1 / frequency

    def inner_func(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            f_is_async = True if asyncio.iscoroutinefunction(f) else False
            while app_state.keep_running:
                tic = time.perf_counter()
                if f_is_async:
                    await f(*args, **kwargs)
                else:
                    f(*args, **kwargs)
                if monitoring_cb:
                    monitoring_cb()
                toc = time.perf_counter()

                sleep_for = max(0, call_every - (toc - tic))

                await asyncio.sleep(sleep_for)

        return wrapper

    return inner_func


if __name__ == "__main__":
    from functools import partial

    # The following two approaches are identical.
    # The first is simpler for a direct use.
    # The latter will be used in the AsyncApp for periodic task creation
    @periodical(2)
    def hello(name="You"):
        print(f"Hello {name}")

    print(hello.__name__)

    # asyncio.run(hello("All"))

    def hello2(name="You"):
        print(f"Hello {name}")

    def watcher():
        print("I'm watching you.")

    asyncio.run(periodical(frequency(10), watcher)(hello2)("Sir"))
