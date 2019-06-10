# Internal
import typing as T
from asyncio import AbstractEventLoop, ensure_future

# External
import typing_extensions as Te

# Generic types
K = T.TypeVar("K")


@Te.overload
async def attempt_await(awaitable: Te.Awaitable[K], loop: AbstractEventLoop) -> K:
    ...


@Te.overload
async def attempt_await(awaitable: K, loop: AbstractEventLoop) -> K:
    ...


async def attempt_await(awaitable: T.Union[Te.Awaitable[K], K], loop: AbstractEventLoop) -> K:
    try:
        result_fut = ensure_future(T.cast(Te.Awaitable[K], awaitable), loop=loop)
    except TypeError:
        return T.cast(K, awaitable)  # Not an awaitable
    else:
        return await result_fut


__all__ = ("attempt_await",)
