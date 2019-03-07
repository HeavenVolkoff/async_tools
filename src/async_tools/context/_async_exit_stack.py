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

EXIT_CALLBACK_t = T.Callable[
    [T.Optional[T.Type[BaseException]], T.Optional[BaseException], T.Optional[TracebackType]],
    T.Optional[bool],
]

ASYNC_EXIT_CALLBACK_t = T.Callable[
    [T.Optional[T.Type[BaseException]], T.Optional[BaseException], T.Optional[TracebackType]],
    T.Coroutine[T.Any, T.Any, T.Optional[bool]],
]

EXIT_CALLBACK_METHOD_t = T.Callable[
    [
        T.ContextManager[T.Any],
        T.Optional[T.Type[BaseException]],
        T.Optional[BaseException],
        T.Optional[TracebackType],
    ],
    T.Optional[bool],
]

ASYNC_EXIT_CALLBACK_METHOD_t = T.Callable[
    [
        T.AsyncContextManager[T.Any],
        T.Optional[T.Type[BaseException]],
        T.Optional[BaseException],
        T.Optional[TracebackType],
    ],
    T.Awaitable[T.Optional[bool]],
]

K = T.TypeVar("K", EXIT_CALLBACK_t, T.ContextManager[T.Any])
L = T.TypeVar("L")
M = T.TypeVar("M", bound=T.Callable[..., T.Any])
N = T.TypeVar("N", bound=T.Callable[..., T.Coroutine[T.Any, T.Any, T.Any]])
O = T.TypeVar("O", ASYNC_EXIT_CALLBACK_t, T.AsyncContextManager[T.Any])


class _BaseExitStack:
    """A base class for ExitStack and AsyncExitStack."""

    @staticmethod
    def _create_cb_wrapper(
        callback: T.Callable[..., T.Any], *args: T.Any, **kwargs: T.Any
    ) -> EXIT_CALLBACK_t:
        def _exit_wrapper(_: T.Any, __: T.Any, ___: T.Any) -> bool:
            callback(*args, **kwargs)
            return False

        return _exit_wrapper

    def __init__(self) -> None:
        self._exit_callbacks: T.Deque[
            T.Tuple[bool, T.Union[EXIT_CALLBACK_t, ASYNC_EXIT_CALLBACK_t]]
        ] = deque()

    def _push_cm_exit(self, cm: T.ContextManager[T.Any], cm_exit: EXIT_CALLBACK_METHOD_t) -> None:
        """Helper to correctly register callbacks to __exit__ methods."""
        self._push_exit_callback(MethodType(cm_exit, cm), True)

    def _push_exit_callback(
        self, callback: T.Union[EXIT_CALLBACK_t, ASYNC_EXIT_CALLBACK_t], is_sync: bool = True
    ) -> None:
        self._exit_callbacks.append((is_sync, callback))

    def pop_all(self) -> "_BaseExitStack":
        """Preserve the context stack by transferring it to a new instance."""
        new_stack = type(self)()
        new_stack._exit_callbacks = self._exit_callbacks
        self._exit_callbacks = deque()
        return new_stack

    def push(self, exit_cb: K) -> K:
        """Registers a callback with the standard __exit__ method signature.
        Can suppress exceptions the same way __exit__ method can.
        Also accepts any object with an __exit__ method (registering a call
        to the method instead of the object itself).
        """
        # We use an unbound method rather than a bound method to follow
        # the standard lookup behaviour for special methods.
        _cb_type = type(exit_cb)

        try:
            exit_method = _cb_type.__exit__  # type: ignore
        except AttributeError:
            # Not a context manager, so assume it's a callable.
            self._push_exit_callback(T.cast(EXIT_CALLBACK_t, exit_cb))
        else:
            self._push_cm_exit(T.cast(T.ContextManager[T.Any], exit_cb), exit_method)

        return exit_cb  # Allow use as a decorator.

    def enter_context(self, cm: T.ContextManager[L]) -> L:
        """Enters the supplied context manager.
        If successful, also pushes its __exit__ method as a callback and
        returns the result of the __enter__ method.
        """
        # We look up the special methods on the type to match the with
        # statement.
        _cm_type = type(cm)
        _exit = _cm_type.__exit__
        result = _cm_type.__enter__(cm)
        self._push_cm_exit(cm, _exit)
        return result

    def callback(self, callback: M, *args: T.Any, **kwargs: T.Any) -> M:
        """Registers an arbitrary callback and arguments.
        Cannot suppress exceptions.
        """
        _exit_wrapper = self._create_cb_wrapper(callback, *args, **kwargs)

        # We changed the signature, so using @wraps is not appropriate, but
        # setting __wrapped__ may still help with introspection.
        _exit_wrapper.__wrapped__ = callback  # type: ignore
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


class AsyncExitStack(_BaseExitStack, T.AsyncContextManager["AsyncExitStack"]):
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
        callback: T.Callable[..., T.Coroutine[T.Any, T.Any, T.Any]], *args: T.Any, **kwargs: T.Any
    ) -> ASYNC_EXIT_CALLBACK_t:
        async def _exit_wrapper(_: T.Any, __: T.Any, ___: T.Any) -> bool:
            await callback(*args, **kwargs)
            return False

        return _exit_wrapper

    async def __aenter__(self) -> "AsyncExitStack":
        return self

    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
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
                if is_sync:
                    cb_suppress = cb(exc_type, exc_value, traceback)
                else:
                    cb_suppress = await cb(exc_type, exc_value, traceback)

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

    def _push_async_cm_exit(
        self, cm: T.AsyncContextManager[T.Any], cm_exit: ASYNC_EXIT_CALLBACK_METHOD_t
    ) -> None:
        """Helper to correctly register coroutine function to __aexit__
        method."""
        self._push_exit_callback(MethodType(cm_exit, cm), False)

    async def enter_async_context(self, cm: T.AsyncContextManager[L]) -> L:
        """Enters the supplied async context manager.
        If successful, also pushes its __aexit__ method as a callback and
        returns the result of the __aenter__ method.
        """
        _cm_type = type(cm)
        _exit = _cm_type.__aexit__
        result = await _cm_type.__aenter__(cm)
        self._push_async_cm_exit(cm, _exit)
        return result

    def push_async_exit(self, exit_cb: O) -> O:
        """Registers a coroutine function with the standard __aexit__ method
        signature.
        Can suppress exceptions the same way __aexit__ method can.
        Also accepts any object with an __aexit__ method (registering a call
        to the method instead of the object itself).
        """
        _cb_type = type(exit_cb)
        try:
            exit_method = _cb_type.__aexit__  # type: ignore
        except AttributeError:
            # Not an async context manager, so assume it's a coroutine function
            self._push_exit_callback(T.cast(ASYNC_EXIT_CALLBACK_t, exit_cb), False)
        else:
            self._push_async_cm_exit(T.cast(T.AsyncContextManager[T.Any], exit_cb), exit_method)
        return exit_cb  # Allow use as a decorator

    def push_async_callback(self, callback: N, *args: T.Any, **kwargs: T.Any) -> N:
        """Registers an arbitrary coroutine function and arguments.
        Cannot suppress exceptions.
        """
        _exit_wrapper = self._create_async_cb_wrapper(callback, *args, **kwargs)

        # We changed the signature, so using @wraps is not appropriate, but
        # setting __wrapped__ may still help with introspection.
        _exit_wrapper.__wrapped__ = callback  # type: ignore
        self._push_exit_callback(_exit_wrapper, False)
        return callback  # Allow use as a decorator

    async def aclose(self) -> None:
        """Immediately unwind the context stack."""
        await self.__aexit__(None, None, None)


__all__ = ("AsyncExitStack",)
