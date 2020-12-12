# Internal
from asyncio import all_tasks
from warnings import warn

warn("async_tools.all_tasks is deprecated, use asyncio.all_tasks instead", DeprecationWarning)

__all__ = ("all_tasks",)
