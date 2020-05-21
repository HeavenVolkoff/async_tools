# Standard
import asyncio

if hasattr(asyncio, "current_task"):
    current_task = asyncio.current_task
else:
    current_task = asyncio.Task.current_task

__all__ = ("current_task",)
