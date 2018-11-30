# modified from: https://github.com/python/cpython/pull/8895

__all__ = ("aiter",)

# Internal
import typing as T

# Generic Types
K = T.TypeVar["K"]

_NOT_PROVIDED = object()  # sentinel object to detect when a kwarg was not given


def aiter(
    obj: T.Union[T.AsyncIterable[K], T.Callable[[], T.Awaitable[K]]], sentinel=_NOT_PROVIDED
) -> T.AsyncIterator[K]:
    """Like the iter() builtin but for async iterables and callables.

    Arguments:
        obj: AsyncIterable or Callable
        sentinel: Condition for callable iterator to stop

    Raises:

    Returns:
        AsyncIterator for given AsyncIterable or Callable (if sentinel was also given)

    """
    if sentinel is _NOT_PROVIDED:
        if not isinstance(obj, T.AsyncIterable):
            raise TypeError(f"aiter expected an AsyncIterable, got {type(obj)}")

        if isinstance(obj, T.AsyncIterator):
            return obj

        return (i async for i in obj)

    if not callable(obj):
        raise TypeError(f"aiter expected an async callable, got {type(obj)}")

    async def ait():
        while True:
            value = await obj()
            if value == sentinel:
                break
            yield value

    return ait()
