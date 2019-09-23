try:
    from contextlib import asynccontextmanager
except ImportError:
    from ._async_context_manager import asynccontextmanager


__all__ = ("asynccontextmanager",)
