# Internal
import typing as T
from functools import wraps

try:
    from contextlib import asynccontextmanager
except ImportError:

    class _GeneratorContextManagerBase:
        """Shared functionality for @contextmanager and @asynccontextmanager."""

        def __init__(self, func, args, kwds):
            self.gen = func(*args, **kwds)
            self.func, self.args, self.kwds = func, args, kwds
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

    # We extends AsyncContextManager instead of AbstractAsyncContextManager,
    # because that is available from python 3.5
    class _AsyncGeneratorContextManager(_GeneratorContextManagerBase, T.AsyncContextManager):
        """Helper for @asynccontextmanager."""

        async def __aenter__(self):
            try:
                return await self.gen.__anext__()
            except StopAsyncIteration:
                raise RuntimeError("generator didn't yield") from None

        async def __aexit__(self, typ, value, traceback):
            if typ is None:
                try:
                    await self.gen.__anext__()
                except StopAsyncIteration:
                    return
                else:
                    raise RuntimeError("generator didn't stop")
            else:
                if value is None:
                    value = typ()
                # See _GeneratorContextManager.__exit__ for comments on subtleties
                # in this implementation
                try:
                    await self.gen.athrow(typ, value, traceback)
                    raise RuntimeError("generator didn't stop after throw()")
                except StopAsyncIteration as exc:
                    return exc is not value
                except RuntimeError as exc:
                    if exc is value:
                        return False
                    # Avoid suppressing if a StopIteration exception
                    # was passed to throw() and later wrapped into a RuntimeError
                    # (see PEP 479 for sync generators; async generators also
                    # have this behavior). But do this only if the exception wrapped
                    # by the RuntimeError is actually Stop(Async)Iteration (see
                    # issue29692).
                    if isinstance(value, (StopIteration, StopAsyncIteration)):
                        if exc.__cause__ is value:
                            return False
                    raise
                except BaseException as exc:
                    if exc is not value:
                        raise

    def asynccontextmanager(func):
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
        def helper(*args, **kwds):
            return _AsyncGeneratorContextManager(func, args, kwds)

        return helper


__all__ = ("asynccontextmanager",)
