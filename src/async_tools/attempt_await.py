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


async def attempt_await(awaitable: T.Union[Te.Awaitable[K], K]) -> K:
    try:
        result_fut = ensure_future(T.cast(Te.Awaitable[K], awaitable), loop=get_running_loop())
    except TypeError:
        return T.cast(K, awaitable)  # Not an awaitable
    else:
        return await result_fut


__all__ = ("attempt_await",)
