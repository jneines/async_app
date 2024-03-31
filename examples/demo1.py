import asyncio

from async_app.app import AsyncApp
import async_app.state as app_state
from async_app.tools import system_monitor, process_monitor, cpu_monitor

# import async_app.messenger as app_messenger


def say_hello(to="You"):
    print(f"Hello {to}!")


async def exit_after(exit_after):
    print(f"{exit_after=}")
    await asyncio.sleep(exit_after)
    app_state.keep_running = False


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
            "function": exit_after,
            "args": (5,),
        },
    ]

    for task in tasks:
        app.add_task_description(task)

    asyncio.run(app.run(), debug=True)


if __name__ == "__main__":
    main()
