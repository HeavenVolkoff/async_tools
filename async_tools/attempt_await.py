# Internal
import typing as T
from asyncio import AbstractEventLoop, ensure_future

# Project
from .get_running_loop import get_running_loop

# Generic types
K = T.TypeVar("K")


async def attempt_await(
    maybe_awaitable: T.Union[T.Awaitable[K], K], loop: T.Optional[AbstractEventLoop] = None
) -> K:
    if loop is None:
        loop = get_running_loop()
    else:
        from warnings import warn

        warn(
            "attempt_await's loop argument will be removed in version 2.0 final release",
            DeprecationWarning,
        )

    try:
        result_fut = ensure_future(T.cast(T.Awaitable[K], maybe_awaitable), loop=loop)
    except TypeError:
        assert not isinstance(maybe_awaitable, T.Awaitable)
        return maybe_awaitable  # Not an awaitable
    else:
        assert isinstance(maybe_awaitable, T.Awaitable)
        return await result_fut


__all__ = ("attempt_await",)
