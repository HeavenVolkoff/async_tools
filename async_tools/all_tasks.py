# Internal
import asyncio

if hasattr(asyncio, "all_tasks"):
    all_tasks = asyncio.all_tasks
else:
    all_tasks = asyncio.Task.all_tasks

__all__ = ("all_tasks",)
