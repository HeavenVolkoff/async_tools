"""
Modified from: https://github.com/python/cpython/pull/8895
"""

# Internal
import typing as T

# Generic types
K = T.TypeVar("K")

_undefined = object()  # sentinel object to detect when a kwarg was not given


@T.overload
def aiter(iterable: T.AsyncIterable[K]) -> T.AsyncIterator[K]:
    ...


@T.overload
def aiter(iterable: T.Callable[[], T.Awaitable[K]], sentinel: T.Any) -> T.AsyncIterator[K]:
    ...


def aiter(
    iterable: T.Union[T.AsyncIterable[K], T.Callable[[], T.Awaitable[K]]],
    sentinel: T.Any = _undefined,
) -> T.AsyncIterator[K]:
    """Like the iter() builtin but for async iterables and callables.

    Arguments:
        iterable: AsyncIterable or Callable
        sentinel: Condition for callable iterator to stop

    Raises:

    Returns:
        AsyncIterator for given AsyncIterable or Callable (if sentinel was also given)

    """
    if sentinel is _undefined:
        if not isinstance(iterable, T.AsyncIterable):
            raise TypeError(f"aiter expected an AsyncIterable, got {type(iterable)}")

        if isinstance(iterable, T.AsyncIterator):
            return iterable

        async def to_aiter() -> T.AsyncGenerator[K, None]:
            assert isinstance(iterable, T.AsyncIterable)
            async for i in iterable:
                yield i

        return to_aiter()

    async def ait() -> T.AsyncIterator[K]:
        if not callable(iterable):
            raise TypeError(f"aiter expected an async callable, got {type(iterable)}")

        while True:
            value = await iterable()
            if value == sentinel:
                break
            yield value

    return ait()


__all__ = ("aiter",)
