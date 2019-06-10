"""Work derived from cpython.

Reference:
    https://github.com/python/cpython/blob/52698c7ad9eae9feb35839fde17a7d1da8036a9b/Lib/contextlib.py
See original licenses in:
    https://github.com/python/cpython/blob/9a69ae8a78785105ded02b083b2e5cd2dd939307/LICENSE
"""

# Internal
import sys
import typing as T
from types import MethodType, TracebackType
from collections import deque

# External
import typing_extensions as Te

# Generic types
L = T.TypeVar("L")
M = T.TypeVar("M", bound=T.Callable[..., T.Any])
N = T.TypeVar("N", bound=T.Callable[..., Te.Coroutine[T.Any, T.Any, T.Any]])


class ExitCallback(Te.Protocol):
    def __call__(
        self,
        exc_type: T.Optional[Te.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> T.Optional[bool]:
        ...


@Te.runtime
class SupportsExit(Te.Protocol):
    __exit__: ExitCallback


class AsyncExitCallback(Te.Protocol):
    async def __call__(
        self,
        exc_type: T.Optional[Te.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> T.Optional[bool]:
        ...


@Te.runtime
class SupportsAsyncExit(Te.Protocol):
    __aexit__: AsyncExitCallback


class _BaseExitStack:
    """A base class for ExitStack and AsyncExitStack."""

    @staticmethod
    def _create_cb_wrapper(
        callback: T.Callable[..., T.Any], *args: T.Any, **kwargs: T.Any
    ) -> ExitCallback:
        def _exit_wrapper(exc_type: T.Any, exc_value: T.Any, traceback: T.Any) -> bool:
            callback(*args, **kwargs)
            return False

        return _exit_wrapper

    def __init__(self) -> None:
        self._exit_callbacks: Te.Deque[
            T.Tuple[bool, T.Union[ExitCallback, AsyncExitCallback]]
        ] = deque()

    def _push_exit_callback(
        self, callback: T.Union[ExitCallback, AsyncExitCallback], is_sync: bool = True
    ) -> None:
        self._exit_callbacks.append((is_sync, callback))

    def pop_all(self) -> "_BaseExitStack":
        """Preserve the context stack by transferring it to a new instance."""
        new_stack = type(self)()
        new_stack._exit_callbacks = self._exit_callbacks
        self._exit_callbacks = deque()
        return new_stack

    @Te.overload
    def push(self, exit_cb: ExitCallback) -> ExitCallback:
        ...

    @Te.overload
    def push(self, exit_cb: SupportsExit) -> SupportsExit:
        ...

    def push(
        self, exit_cb: T.Union[ExitCallback, SupportsExit]
    ) -> T.Union[ExitCallback, SupportsExit]:
        """Registers a callback with the standard __exit__ method signature.
        Can suppress exceptions the same way __exit__ method can.
        Also accepts any object with an __exit__ method (registering a call
        to the method instead of the object itself).
        """
        # We use an unbound method rather than a bound method to follow
        # the standard lookup behaviour for special methods.
        if hasattr(type(exit_cb), "__exit__"):
            assert isinstance(exit_cb, SupportsExit)
            self._push_exit_callback(MethodType(type(exit_cb).__exit__, exit_cb))
        else:
            # Not a context manager, so assume it's a callable.
            self._push_exit_callback(T.cast(ExitCallback, exit_cb))

        return exit_cb  # Allow use as a decorator.

    def enter_context(self, cm: Te.ContextManager[L]) -> L:
        """Enters the supplied context manager.
        If successful, also pushes its __exit__ method as a callback and
        returns the result of the __enter__ method.
        """
        # We look up the special methods on the type to match the with
        # statement.
        cm_type = type(cm)
        result: L = MethodType(cm_type.__enter__, cm)()
        self._push_exit_callback(MethodType(cm_type.__exit__, cm), True)
        return result

    def callback(self, callback: M, *args: T.Any, **kwargs: T.Any) -> M:
        """Registers an arbitrary callback and arguments.
        Cannot suppress exceptions.
        """
        _exit_wrapper = self._create_cb_wrapper(callback, *args, **kwargs)

        # We changed the signature, so using @wraps is not appropriate, but
        # setting __wrapped__ may still help with introspection.
        setattr(_exit_wrapper, "__wrapped__", callback)
        self._push_exit_callback(_exit_wrapper)
        return callback  # Allow use as a decorator


def _fix_exception_context(
    new_exc: BaseException,
    old_exc: T.Optional[BaseException],
    frame_exc: T.Optional[BaseException],
) -> None:
    # Context may not be correct, so find the end of the chain
    while 1:
        exc_context = new_exc.__context__
        if exc_context is old_exc:
            # Context is already set correctly (see issue 20317)
            return
        if exc_context is None or exc_context is frame_exc:
            break
        new_exc = exc_context
    # Change the end of the chain to point to the exception
    # we expect it to reference
    new_exc.__context__ = old_exc


class AsyncExitStack(_BaseExitStack, Te.AsyncContextManager["AsyncExitStack"]):
    """Async context manager for dynamic management of a stack of exit
    callbacks.
    For example:
        async with AsyncExitStack() as stack:
            connections = [await stack.enter_async_context(get_connection())
                for i in range(5)]
            # All opened connections will automatically be released at the
            # end of the async with statement, even if attempts to open a
            # connection later in the list raise an exception.
    """

    @staticmethod
    def _create_async_cb_wrapper(
        callback: T.Callable[..., Te.Coroutine[T.Any, T.Any, T.Any]], *args: T.Any, **kwargs: T.Any
    ) -> AsyncExitCallback:
        async def _exit_wrapper(exc_type: T.Any, exc_value: T.Any, traceback: T.Any) -> bool:
            await callback(*args, **kwargs)
            return False

        return _exit_wrapper

    async def __aenter__(self) -> "AsyncExitStack":
        return self

    async def __aexit__(
        self,
        exc_type: T.Optional[Te.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> T.Optional[bool]:
        # We manipulate the exception state so it behaves as though
        # we were actually nesting multiple with statements
        frame_exc = sys.exc_info()[1]

        # Cached if there was an original exception
        received_exc = exc_type is not None

        # Callbacks are invoked in LIFO order to match the behaviour of
        # nested context managers
        pending_raise = False
        suppressed_exc = False
        while self._exit_callbacks:
            is_sync, cb = self._exit_callbacks.pop()
            try:
                cb_awaitable = cb(exc_type, exc_value, traceback)
                if is_sync:
                    assert not isinstance(cb_awaitable, Te.Awaitable)
                    cb_suppress = cb_awaitable
                else:
                    assert isinstance(cb_awaitable, Te.Awaitable)
                    cb_suppress = await cb_awaitable

                if cb_suppress:
                    pending_raise = False
                    suppressed_exc = True
                    exc_type, exc_value, traceback = (None, None, None)
            except BaseException:
                new_exc_details = sys.exc_info()
                assert isinstance(new_exc_details[1], BaseException)
                # simulate the stack of exceptions by setting the context
                _fix_exception_context(new_exc_details[1], exc_value, frame_exc)
                pending_raise = True
                exc_type, exc_value, traceback = new_exc_details

        if pending_raise:
            assert isinstance(exc_value, BaseException)
            fixed_ctx = exc_value.__context__
            try:
                # bare "raise exc_details[1]" replaces our carefully
                # set-up context
                raise exc_value
            except BaseException:
                exc_value.__context__ = fixed_ctx
                raise

        return received_exc and suppressed_exc

    async def enter_async_context(self, cm: Te.AsyncContextManager[L]) -> L:
        """Enters the supplied async context manager.
        If successful, also pushes its __aexit__ method as a callback and
        returns the result of the __aenter__ method.
        """
        cm_type = type(cm)
        result: L = await MethodType(cm_type.__aenter__, cm)()
        self._push_exit_callback(MethodType(cm_type.__aexit__, cm), False)
        return result

    @Te.overload
    def push_async_exit(self, exit_cb: AsyncExitCallback) -> AsyncExitCallback:
        ...

    @Te.overload
    def push_async_exit(self, exit_cb: SupportsAsyncExit) -> SupportsAsyncExit:
        ...

    def push_async_exit(
        self, exit_cb: T.Union[AsyncExitCallback, SupportsAsyncExit]
    ) -> T.Union[AsyncExitCallback, SupportsAsyncExit]:
        """Registers a callback with the standard __exit__ method signature.
        Can suppress exceptions the same way __exit__ method can.
        Also accepts any object with an __exit__ method (registering a call
        to the method instead of the object itself).
        """
        # We use an unbound method rather than a bound method to follow
        # the standard lookup behaviour for special methods.
        if hasattr(type(exit_cb), "__aexit__"):
            assert isinstance(exit_cb, SupportsAsyncExit)
            self._push_exit_callback(MethodType(type(exit_cb).__aexit__, exit_cb), False)
        else:
            # Not an async context manager, so assume it's a coroutine function
            self._push_exit_callback(T.cast(AsyncExitCallback, exit_cb), False)

        return exit_cb  # Allow use as a decorator.

    def push_async_callback(*args: T.Any, **kwargs: T.Any) -> N:
        """Registers an arbitrary coroutine function and arguments.

        Cannot suppress exceptions.
        """
        callback: N

        if len(args) >= 2:
            self, callback, *args = args  # type: ignore
        elif not args:
            raise TypeError(
                "descriptor 'push_async_callback' of " "'AsyncExitStack' object needs an argument"
            )
        elif "callback" in kwargs:
            callback = kwargs.pop("callback")
            self, *args = args  # type: ignore
            import warnings

            warnings.warn(
                "Passing 'callback' as keyword argument is deprecated in Python 3.8",
                DeprecationWarning,
                stacklevel=2,
            )
        else:
            raise TypeError(
                "push_async_callback expected at least 1 "
                "positional argument, got %d" % (len(args) - 1)
            )

        _exit_wrapper = self._create_async_cb_wrapper(callback, *args, **kwargs)

        # We changed the signature, so using @wraps is not appropriate, but
        # setting __wrapped__ may still help with introspection.
        setattr(_exit_wrapper, "__wrapped__", callback)
        self._push_exit_callback(_exit_wrapper, False)
        return callback  # Allow use as a decorator

    push_async_callback.__text_signature__ = "($self, callback, /, *args, **kwds)"  # type: ignore

    async def aclose(self) -> None:
        """Immediately unwind the context stack."""
        await self.__aexit__(None, None, None)


__all__ = ("AsyncExitStack",)
