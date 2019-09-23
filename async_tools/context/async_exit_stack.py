try:
    from contextlib import AsyncExitStack
except ImportError:
    from ._async_exit_stack import AsyncExitStack  # type: ignore


__all__ = ("AsyncExitStack",)
