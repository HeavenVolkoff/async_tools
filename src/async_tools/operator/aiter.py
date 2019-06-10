"""
Modified from: https://github.com/python/cpython/pull/8895
"""

# Internal
import typing as T

# External
import typing_extensions as Te

# Generic types
K = T.TypeVar("K")

_NOT_PROVIDED = object()  # sentinel object to detect when a kwarg was not given


@Te.overload
def aiter(iterable: Te.AsyncIterable[K]) -> Te.AsyncIterator[K]:
    ...


@Te.overload
def aiter(iterable: T.Callable[[], Te.Awaitable[K]], sentinel: T.Any) -> Te.AsyncIterator[K]:
    ...


def aiter(
    iterable: T.Union[Te.AsyncIterable[K], T.Callable[[], Te.Awaitable[K]]],
    sentinel: T.Any = _NOT_PROVIDED,
) -> Te.AsyncIterator[K]:
    """Like the iter() builtin but for async iterables and callables.

    Arguments:
        iterable: AsyncIterable or Callable
        sentinel: Condition for callable iterator to stop

    Raises:

    Returns:
        AsyncIterator for given AsyncIterable or Callable (if sentinel was also given)

    """
    if sentinel is _NOT_PROVIDED:
        if not isinstance(iterable, Te.AsyncIterable):
            raise TypeError("aiter expected an AsyncIterable, got {}".format(type(iterable)))

        if isinstance(iterable, Te.AsyncIterator):
            return iterable

        async def to_aiter() -> Te.AsyncGenerator[K, None]:
            assert isinstance(iterable, Te.AsyncIterable)
            async for i in iterable:
                yield i

        return to_aiter()

    async def ait() -> Te.AsyncIterator[K]:
        if not callable(iterable):
            raise TypeError("aiter expected an async callable, got {}".format(type(iterable)))

        while True:
            value = await iterable()
            if value == sentinel:
                break
            yield value

    return ait()


__all__ = ("aiter",)
