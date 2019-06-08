"""Work derived from cpython.

Reference:
    https://github.com/python/cpython/blob/52698c7ad9eae9feb35839fde17a7d1da8036a9b/Lib/contextlib.py
See original licenses in:
    https://github.com/python/cpython/blob/9a69ae8a78785105ded02b083b2e5cd2dd939307/LICENSE
"""

# Internal
import typing as T
from types import TracebackType
from functools import wraps

# Type Generics
K = T.TypeVar("K")


# We extends AsyncContextManager instead of AbstractAsyncContextManager,
# because that is available in python 3.5
class _AsyncGeneratorContextManager(T.Generic[K], T.AsyncContextManager[K]):
    """Helper for @asynccontextmanager."""

    def __init__(
        self, func: T.Callable[..., T.AsyncGenerator[T.Any, K]], args: T.Any, kwargs: T.Any
    ):
        self.gen = func(*args, **kwargs)
        self.func = func
        self.args = args
        self.kwargs = kwargs

        # Issue 19330: ensure context manager instances have good docstrings
        doc = getattr(func, "__doc__", None)
        if doc is None:
            doc = type(self).__doc__
        self.__doc__ = doc
        # Unfortunately, this still doesn't provide good help output when
        # inspecting the created context manager instances, since pydoc
        # currently bypasses the instance docstring and shows the docstring
        # for the class instead.
        # See http://bugs.python.org/issue19404 for more details.

    async def __aenter__(self) -> K:
        from ..operator import anext

        try:
            return await anext(self.gen)
        except StopAsyncIteration:
            raise RuntimeError("generator didn't yield") from None

    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> T.Optional[bool]:
        if exc_type is None:
            try:
                await self.gen.__anext__()
            except StopAsyncIteration:
                return False

            raise RuntimeError("generator didn't stop")

        if exc_value is None:
            # Need to force instantiation so we can reliably
            # tell if we get the same exception back
            exc_value = exc_type()

        try:
            await self.gen.athrow(exc_type, exc_value, traceback)
            raise RuntimeError("generator didn't stop after throw()")
        except StopAsyncIteration as exc:
            # Suppress StopIteration *unless* it's the same exception that
            # was passed to throw().  This prevents a StopIteration
            # raised inside the "with" statement from being suppressed.
            return exc is not exc_value
        except RuntimeError as exc:
            # Don't re-raise the passed in exception. (issue27122)
            # Avoid suppressing if a StopIteration exception
            # was passed to throw() and later wrapped into a RuntimeError
            # (see PEP 479 for sync generators; async generators also
            # have this behavior). But do this only if the exception wrapped
            # by the RuntimeError is actually Stop(Async)Iteration (see
            # issue29692).
            if not (
                exc is exc_value
                or (
                    isinstance(exc_value, (StopIteration, StopAsyncIteration))
                    and exc.__cause__ is exc_value
                )
            ):
                raise
        except BaseException as exc:
            # only re-raise if it's *not* the exception that was
            # passed to throw(), because __exit__() must not raise
            # an exception unless __exit__() itself failed.  But throw()
            # has to raise the exception to signal propagation, so this
            # fixes the impedance mismatch between the throw() protocol
            # and the __exit__() protocol.
            if exc is not exc_value:
                raise

        return False


def asynccontextmanager(func: T.Callable[..., T.Any]) -> T.Callable[..., T.Any]:
    """@asynccontextmanager decorator.
    Typical usage:
        @asynccontextmanager
        async def some_async_generator(<arguments>):
            <setup>
            try:
                yield <value>
            finally:
                <cleanup>
    This makes this:
        async with some_async_generator(<arguments>) as <variable>:
            <body>
    equivalent to this:
        <setup>
        try:
            <variable> = <value>
            <body>
        finally:
            <cleanup>
    """

    @wraps(func)
    def helper(*args: T.Any, **kwargs: T.Any) -> T.Any:
        return _AsyncGeneratorContextManager(func, args, kwargs)

    return helper


__all__ = ("asynccontextmanager",)
