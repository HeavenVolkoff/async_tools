"""
Modified from: https://github.com/python/cpython/pull/8895
"""

# Internal
import typing as T

# Generic Types
K = T.TypeVar("K")

_NOT_PROVIDED = object()  # sentinel object to detect when a kwarg was not given


@T.overload
def aiter(iterable: T.AsyncIterable[K]) -> T.AsyncIterator[K]:
    ...


@T.overload
def aiter(iterable: T.Callable[[], T.Awaitable[K]], sentinel: T.Any) -> T.AsyncIterator[K]:
    ...


def aiter(
    iterable: T.Union[T.AsyncIterable[K], T.Callable[[], T.Awaitable[K]]],
    sentinel: T.Any = _NOT_PROVIDED,
) -> T.AsyncIterator[K]:
    """Like the iter() builtin but for async iterables and callables.

    Arguments:
        iterable: AsyncIterable or Callable
        sentinel: Condition for callable iterator to stop

    Raises:

    Returns:
        AsyncIterator for given AsyncIterable or Callable (if sentinel was also given)

    """
    if sentinel is _NOT_PROVIDED:
        if not isinstance(iterable, T.AsyncIterable):
            raise TypeError(f"aiter expected an AsyncIterable, got {type(iterable)}")

        if isinstance(iterable, T.AsyncIterator):
            return iterable

        return iterable.__aiter__()

    if not callable(iterable):
        raise TypeError(f"aiter expected an async callable, got {type(iterable)}")

    async def ait() -> T.AsyncIterator[K]:
        while True:
            value = await T.cast(T.Callable[[], T.Awaitable[K]], iterable)()
            if value == sentinel:
                break
            yield value

    return ait()


__all__ = ("aiter",)
