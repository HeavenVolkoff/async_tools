# Internal
from warnings import warn
from contextlib import asynccontextmanager

warn(
    "async_tools.context.async_context_manager is deprecated, use contextlib instead",
    DeprecationWarning,
)

__all__ = ("asynccontextmanager",)
