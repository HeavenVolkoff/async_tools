# Internal
import asyncio

all_tasks = getattr(asyncio, "all_tasks", asyncio.Task.all_tasks)

__all__ = ("all_tasks",)
