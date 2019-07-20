# Internal
import asyncio

if hasattr(asyncio, "all_tasks"):
    current_task = asyncio.all_tasks
else:
    current_task = asyncio.Task.all_tasks

__all__ = ("all_tasks",)
