import asyncio

from async_app.app import AsyncApp
import async_app.state as app_state
from async_app.tools import system_monitor, process_monitor, cpu_monitor

# import async_app.messenger as app_messenger


async def init_resources(what):
    print(f"Initializing {what} ... Done!")


def say_hello(to="You"):
    print(f"Hello {to}!")


def fast_call():
    pass


async def wait_for(wait_for):
    print(f"{wait_for=}")
    await asyncio.sleep(wait_for)
    print("Done")


async def exceptional(fail_after):
    await asyncio.sleep(fail_after)
    1 / 0


async def return_42():
    await asyncio.sleep(1)
    return 42


async def exit_after(exit_after):
    print(f"{exit_after=}")
    await asyncio.sleep(exit_after)
    app_state.keep_running = False


def thats_was(what="it"):
    print(f"That was {what}")


def main():
    app = AsyncApp()
    tasks = [
        {
            "kind": "periodic",
            "frequency": 5,
            "function": say_hello,
            "args": ("Mate",),
            "kwargs": {},
        },
        {
            "kind": "continuous",
            "function": wait_for,
            "args": (3,),
        },
        {
            "kind": "continuous",
            "function": exit_after,
            "args": (5,),
        },
        {
            "kind": "continuous",
            "function": exceptional,
            "args": (2,),
        },
        {
            "kind": "continuous",
            "function": return_42,
        },
        {
            "kind": "periodic",
            "function": app.task_monitor,
            "frequency": 5,
        },
        # {
        #    "kind": "periodic",
        #    "function": fast_call,
        #    "frequency": 50,
        #    "monitor": True,
        # },
        # {
        #    "kind": "periodic",
        #    "function": app.periodicals_monitor,
        #    "call_every": 1,
        # },
        # {
        #    "kind": "periodic",
        #    "frequency": 1,
        #    "function": system_monitor,
        # },
        # {
        #    "kind": "periodic",
        #    "frequency": 1,
        #    "function": process_monitor,
        # },
        {
            "kind": "cleanup",
            "function": thats_was,
        },
        {
            "kind": "cleanup",
            "function": thats_was,
            "args": ("all",),
        },
        {
            "kind": "init",
            "function": init_resources,
            "args": ("network",),
        },
        # {
        #    "kind": "init",
        #    "function": init_resources,
        #    "args": ("db",),
        # },
        # {
        #    "kind": "periodic",
        #    "frequency": 1,
        #    "function": cpu_percent,
        # },
        # {
        #    "kind": "forever",
        #    "call": new_image_listener,
        #    "args": ("timelapser:picamera6:new_image", new_image),
        #    },
    ]

    for task in tasks:
        app.add_task_description(task)

    asyncio.run(app.run(), debug=True)


if __name__ == "__main__":
    main()
