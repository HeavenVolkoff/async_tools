# Internal
import typing as T

# Generic Types
from asyncio import AbstractEventLoop, ensure_future

K = T.TypeVar("K")


@T.overload
async def attempt_await(awaitable: T.Awaitable[K], loop: AbstractEventLoop) -> K:
    ...


@T.overload
async def attempt_await(awaitable: K, loop: AbstractEventLoop) -> K:
    ...


async def attempt_await(awaitable: T.Any, loop: AbstractEventLoop) -> K:
    try:
        result_fut = ensure_future(T.cast(T.Awaitable[K], awaitable), loop=loop)
    except TypeError:
        return T.cast(K, awaitable)  # Not an awaitable
    else:
        return await result_fut


__all__ = ("attempt_await",)
