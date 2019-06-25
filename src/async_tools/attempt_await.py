# Internal
import typing as T
from asyncio import AbstractEventLoop, ensure_future

# External
import typing_extensions as Te

# Project
from .get_running_loop import get_running_loop

# Generic types
K = T.TypeVar("K")


@T.overload
async def attempt_await(awaitable: Te.Awaitable[K]) -> K:
    ...


@T.overload
async def attempt_await(awaitable: K) -> K:
    ...


async def attempt_await(awaitable: T.Any, loop: T.Optional[AbstractEventLoop] = None) -> T.Any:
    if loop is None:
        loop = get_running_loop()
    else:
        from warnings import warn

        warn("attempt_await's loop argument will be removed in version 2.0", DeprecationWarning)

    try:
        result_fut = ensure_future(T.cast(Te.Awaitable[T.Any], awaitable), loop=loop)
    except TypeError:
        return awaitable  # Not an awaitable
    else:
        return await result_fut


__all__ = ("attempt_await",)
