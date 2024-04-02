# Usage

To use Async App in a project:

```
import asyncio

from async_app.app import AsyncApp


app = AsyncApp()

app.add_task_description({"kind": "continuous", "function": lambda: print("Hello"),})

asyncio.run(app.run())
```
