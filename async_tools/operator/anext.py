"""
Modified from: https://github.com/python/cpython/pull/8895
"""

# Standard
import typing as T

# Generic types
K = T.TypeVar("K")
L = T.TypeVar("L")

_NOT_PROVIDED = object()  # sentinel object to detect when a kwarg was not given


@T.overload
async def anext(async_iterator: T.AsyncGenerator[K, T.Any]) -> K:
    ...


@T.overload
async def anext(async_iterator: T.AsyncGenerator[K, T.Any], default: L) -> T.Union[K, L]:
    ...


async def anext(
    async_iterator: T.AsyncGenerator[K, T.Any], default: T.Union[L, object] = _NOT_PROVIDED
) -> T.Union[K, L, object]:
    """Return the next item from the async iterator.

    Arguments:
        async_iterator: AsyncIterator that will be iterated.
        default: Default parameter to be returned instead of raising StopAsyncIteration.

    """
    if not isinstance(async_iterator, T.AsyncIterator):
        raise TypeError(f"anext expected an AsyncIterator, got {type(async_iterator)}")

    async_next = async_iterator.__anext__

    try:
        return await async_next()
    except StopAsyncIteration:
        if default is _NOT_PROVIDED:
            raise

        return default


__all__ = ("anext",)
