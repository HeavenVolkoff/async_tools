# Internal
import typing as T
from asyncio import AbstractEventLoop, ensure_future

# Project
from .get_running_loop import get_running_loop

# Generic types
K = T.TypeVar("K")


@T.overload
async def attempt_await(awaitable: T.Awaitable[K], loop: T.Optional[AbstractEventLoop] = None) -> K:
    ...


@T.overload
async def attempt_await(awaitable: K, loop: T.Optional[AbstractEventLoop] = None) -> K:
    ...


async def attempt_await(awaitable: T.Any, loop: T.Optional[AbstractEventLoop] = None) -> T.Any:
    if loop is None:
        loop = get_running_loop()
    else:
        from warnings import warn

        warn("attempt_await's loop argument will be removed in version 2.0", DeprecationWarning)

    try:
        result_fut = ensure_future(T.cast(T.Awaitable[T.Any], awaitable), loop=loop)
    except TypeError:
        return awaitable  # Not an awaitable
    else:
        return await result_fut


__all__ = ("attempt_await",)
