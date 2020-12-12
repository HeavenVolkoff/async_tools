# Internal
from asyncio import get_running_loop
from warnings import warn

warn(
    "async_tools.get_running_loop is deprecated, use asyncio.get_running_loop instead",
    DeprecationWarning,
)

__all__ = ("get_running_loop",)
