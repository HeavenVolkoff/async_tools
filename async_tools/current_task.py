# Internal
from asyncio import current_task
from warnings import warn

warn(
    "async_tools.current_task is deprecated, use asyncio.current_task instead", DeprecationWarning
)

__all__ = ("current_task",)
