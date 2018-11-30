# modified from: https://github.com/python/cpython/pull/8895

__all__ = ("anext",)

# Internal
import typing as T

# Generic Types
K = T.TypeVar["K"]
L = T.TypeVar["L"]

_NOT_PROVIDED = object()  # sentinel object to detect when a kwarg was not given


async def anext(async_iterator: T.AsyncIterator[K], default: L = _NOT_PROVIDED) -> T.Union[K, L]:
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
