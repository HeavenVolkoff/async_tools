# Internal
import sys
import typing as T
from enum import Flag, auto
from asyncio import Future, CancelledError, ensure_future
from platform import python_implementation
from collections import defaultdict

# External
import typing_extensions as Te

# Python 3.7+ dicts are ordered by default, and they are slightly faster than OrderedDicts
if sys.version_info >= (3, 7) or (
    sys.version_info >= (3, 6) and python_implementation() == "CPython"
):
    OrderedDict = dict
else:
    from collections import OrderedDict

# Type Generics
K = T.TypeVar("K")
L = T.TypeVar("L", contravariant=True)


class ListenerCb(Te.Protocol[L]):
    def __call__(self, __event_data: L) -> T.Optional[T.Awaitable[None]]:
        ...


class ListenerOpts(Flag):
    NOP = 0
    ONCE = auto()


class NewListener(T.NamedTuple):
    """`async_tools.emitter.Emitter` emits this event whenever there is a new registration of a
    listener.
    """

    event: type
    """Event type to which the listener was registered"""
    listener: ListenerCb[T.Any]
    """Registered listener"""


class ListenerFutureError(RuntimeError):
    """Exception referent to when a listener returned awaitable resolves with failure."""

    pass


class ListenerExecutionError(RuntimeError):
    """Exception referent to when a listener execution fails."""

    pass


class Emitter:
    """Async-aware event emitter for Python.

    Enables [event-driven programming](https://en.wikipedia.org/wiki/Event-driven_programming) by
    providing the basic interface needed for registering listeners and emitting events.

    ```python
    from async_tools import Emitter

    emitter = Emitter()
    ```

    .. topics::
        [TOC]

    ## Events

    Events are any user-defined class or Exception subclass.

    ```python
    from typing import NamedTuple

    # An event
    class UserRegisteredEvent(NamedTuple):
        id: int
        name: str
        email: str
    ```

    The method `async_tools.emitter.Emitter.emit` enables arbitrary event emission.
    It receives a single argument that is an instance of the event to be emitted, and returns a
    boolean indicating whether it executed any listener.

    ```python
    listener_executed = emitter.emit(
        UserRegisteredEvent(
            69, 'Michael Scott', 'whatshesaid@dundermifflin.com'
        )
    )

    # listener_executed is False
    # That is because there is no listener registered for this event
    assert not listener_executed
    ```
    .. important::
        `async_tools.emitter.Emitter.emit` is a synchronous call, that blocks until it finishes
        executing all listeners registered for the received event.

    ## Listeners

    Listeners are any callable that receives a single argument (an instance of the event type) and
    returns `None` or `Awaitable[None]`.
    A listener can be registered for an event via `async_tools.emitter.Emitter.on`.

    - A callable object as listener:

    ```python
    class UserRegistry:
        def __init__() -> None:
            self.registry: T.List[UserRegisteredEvent] = []

        def __call__(event: UserRegisteredEvent) -> None:
            self.registry.append(event)

    user_registry = UserRegistry()

    # Register listener
    emitter.on(UserRegisteredEvent, user_registry)
    ```

    - A lambda as listener:

    ```python
    # Register listener
    emitter.on(
        UserRegisteredEvent,
        lambda event: print(
            f"User<id={event.id}, name={event.name}, email={event.email}>"
             "registered"
        )
    )
    ```

    - A function as listener:

    ```python
    # Another approach to example 1
    user_registry: T.List[UserRegisteredEvent] = []

    # Register listener
    @emitter.on(UserRegisteredEvent)
    def register_user(event: UserRegisteredEvent) -> None:
        user_registry.append(event)
    ```

    - An asynchronous function as listener:

    ```python
    import asyncpg

    # Register listener
    @emitter.on(UserRegisteredEvent)
    async def write_user(event: UserRegisteredEvent) -> None:
        conn = await asyncpg.connect(
            host='127.0.0.1'
            user='user',
            password='password',
            database='database',
        )

        await conn.execute(
            'INSERT INTO users(id, name, email) VALUES($1, $2, $3)',
            event.id, event.name, event.email
        )

        await conn.close()
    ```

    .. important::
        The execution of event listeners occurs synchronously and follows insertion order.

        `async_tools.emitter.Emitter` schedules any awaitable returned by a listener in the current
        Thread's loop.
        No effort whatsoever is done to ensure resolution order between awaitables.

    ### `async_tools.emitter.Emitter` special events:

    - `async_tools.emitter.NewListener`:

        Whenever there is a new listener attached to an event, `async_tools.emitter.Emitter`
        internally fires this event. It contains the attached event type and listener.

    - `async_tools.emitter.ListenerExecutionError`:

        Whenever a listener execution raises an Exception, `async_tools.emitter.Emitter` internally
        fires this event. It is an Exception subclass, with the raised Exception added to it's
        `__cause__`.

    - `async_tools.emitter.ListenerFutureError`:

        Whenever a listener returned Awaitable resolves with an Exception,
        `async_tools.emitter.Emitter` internally fires this event. It is an Exception subclass,
        with the resolved Exception added to it's `__cause__`.

    - `Exception` and it's subclasses:

        These are the only builtin types that are accepted as event types by
        `async_tools.emitter.Emitter`.
        Their behaviour is equivalent to a user-defined event type, with the sole difference being
        when there are no listeners registered to handle an emission of it. In those cases,
        `async_tools.emitter.Emitter` will raise the Exception back to the user context that fired
        the event.

    ## Scopes

    Scope is a feature that allow limiting the execution of listeners to specific instances of an
    event emission.

    A scoped listener definition requires passing the `scope` argument to
    `async_tools.emitter.Emitter.on`. It's default value is the empty scope, which is the one where
    all listeners registered under it are guarantee to be executed when there is any emission of
    their attached event.
    ```python
    @emitter.on(UserRegisteredEvent, scope="permission.manager")
    async def write_admin_permission(event: UserRegisteredEvent) -> None:
        conn = await asyncpg.connect(
            host='127.0.0.1'
            user='user',
            password='password',
            database='database',
        )

        await con.execute(
            'UPDATE users SET admin=$2 WHERE id=$1',
            event.id, True
        )

        await conn.close()
    ```
    Scope is a dot separated string. Each dot constrained name defines a more specif scope that
    must also be specified when emitting an event to enable the execution of the registered scoped
    listener.
    Scoped events will execute all listeners from the most generic scope (the empty scope) till the
    specified scope.
    ```python
    emitter.emit(
        UserRegisteredEvent(
            69,
            'Michael Scott',
            'whatshesaid@dundermifflin.com'
        ),
        scope="permission.manager"
    )
    ```
    The call above will execute all 5 listeners that were registered in the event. Being 4 of them
    unscoped (or empty scoped), and the last one scoped under `permission.manager`.

    ## Event inheritance

    Event inheritance allows specialization of events and their listeners.

    When there is an emission of an event the `async_tools.emitter.Emitter` will retrieve all
    superclasses that this event inherits from, filter them by the ones that have registered
    unscoped listeners and emit their events passing the inherited event.

    ```python
    from dataclass import dataclass
    from collections import Counter
    from async_tools import Emitter

    emitter = Emitter()
    metrics = set()
    total_error = Counter()

    @dataclass
    class Metric:
        name: str
        value: int

        def __hash__(self):
            return hash(self.name)

    @emitter.on(Metric):
    def register_metric(event: Metric):
        metrics.add(event)

    @dataclass
    class ErrorMetric(Metric):
        error: T.Type[Exception]

    @emitter.on(Metric):
    def calculate_total_error(event: ErrorMetric):
        total_error[event.error] += 1

    emitter.emit(ErrorMetric(name="error", value=1, error=RuntimeError))
    ```
    """

    @staticmethod
    def _limit_scope(
        scope: T.Optional[str], listeners: T.Iterable[T.Tuple[T.Tuple[str, ...], K]],
    ) -> T.Iterable[T.Tuple[T.Tuple[str, ...], K]]:
        if scope:
            event_scope = tuple(scope.split("."))
            listeners = filter(
                lambda scope_and_listener: event_scope >= scope_and_listener[0], listeners
            )

        return listeners

    @staticmethod
    def _validate_event_type(event_type: type) -> None:
        if not isinstance(event_type, type) or issubclass(event_type, type):
            raise ValueError("Event type must be an instance of type")

        if event_type.__module__ == "builtins":
            raise ValueError("Event type can't be builtins")

    def __init__(self) -> None:
        self._listeners: T.MutableMapping[
            type,
            T.MutableMapping[T.Tuple[str, ...], T.MutableMapping[ListenerCb[T.Any], ListenerOpts]],
        ] = defaultdict(lambda: defaultdict(OrderedDict))

    def _future_callback(self, future: "Future[None]") -> None:
        try:
            future.result()
        except CancelledError:
            pass
        except Exception as exc:
            # Chain any listener raised Exceptions with a ListenerFutureError and raise it's
            # respective event
            internal_exc = ListenerFutureError(
                "A listener's future raised an exception on resolution"
            )
            internal_exc.__cause__ = exc
            self.emit(internal_exc)

    def _emit(self, cls: type, instance: object, scope: T.Tuple[str, ...]) -> bool:
        if isinstance(instance, BaseException) and not isinstance(instance, Exception):
            # Instance of BaseException are re-raised, because Emitter can't handle BaseException
            # events due to how it handles Exceptions internally.
            raise instance

        if not isinstance(instance, cls):
            raise ValueError("Event instance must be an instance of event type")

        self._validate_event_type(cls)

        try:
            # Retrieve the closest event superclass in mro that has unscoped listeners registered
            s_cls = next(
                s_cls
                for s_cls in reversed(cls.mro())
                if (
                    s_cls in self._listeners
                    and tuple() in self._listeners[s_cls]
                    and s_cls is not cls
                )
            )
        except StopIteration:
            handled = False
        else:
            # Emit an unscoped event for the event superclass
            # TODO: Should we use an empty scope, or the current scope
            handled = self._emit(s_cls, instance, tuple())

        # Range from -1 to include empty scopes in the loop
        for step in range(-1, len(scope)):
            step += 1  # Fix scope index
            listeners = self._listeners[cls][scope[:step]]
            # .items() returns a dynamic view, make it static by transforming it to a tuple
            # This is necessary to allow listeners to remove events without interfering with any
            # current running event emission.
            for listener, opts in tuple(listeners.items()):
                handled = True

                # Remove listener from the queue if it was set to only exec once
                if opts & ListenerOpts.ONCE:
                    del listeners[listener]

                try:
                    coroutine = listener(instance)
                except Exception as exc:
                    # Chain any listener raised Exceptions with a ListenerFutureError and raise
                    # it's respective event
                    internal_exc = ListenerExecutionError(
                        "A listener raised an exception on execution"
                    )
                    internal_exc.__cause__ = exc
                    self.emit(internal_exc)
                else:
                    try:
                        result_fut = ensure_future(T.cast(T.Awaitable[None], coroutine))
                    except TypeError:
                        pass  # Not an awaitable
                    else:
                        result_fut.add_done_callback(self._future_callback)

        return handled

    @T.overload
    def on(
        self,
        event_type: T.Type[K],
        listener: ListenerCb[K],
        *,
        once: bool = False,
        scope: str = "",
    ) -> ListenerCb[K]:
        ...

    @T.overload
    def on(
        self,
        event_type: T.Type[K],
        listener: Te.Literal[None] = None,
        *,
        once: bool = False,
        scope: str = "",
    ) -> T.Callable[[ListenerCb[K]], ListenerCb[K]]:
        ...

    def on(
        self,
        event_type: T.Type[K],
        listener: T.Optional[ListenerCb[K]] = None,
        *,
        once: bool = False,
        scope: str = "",
    ) -> T.Union[ListenerCb[K], T.Callable[[ListenerCb[K]], ListenerCb[K]]]:
        """Add a listener to event type.

        Arguments:
            event_type: Event type to attach the listener to.
            listener: Callable to be executed when there is an emission of the given event type.
            once: Whether this listener is to be removed after being executed for the first time.
            scope: Define scope for limiting this listener execution.

        Raises:
            ValueError: event_type is not a type instance, or it is a builtin type, or it is
                        BaseExceptions or listener is not callable.

        Returns:
            If listener isn't provided, this method returns a function that takes a Callable as a \
            single argument. As such it can be used as a decorator. In both the decorated and \
            undecorated forms this function returns the given event listener.

        """
        if issubclass(event_type, BaseException) and not issubclass(event_type, Exception):
            raise ValueError("Event type can't be a BaseException")

        self._validate_event_type(event_type)

        if listener is None:
            # Decorator behaviour
            return lambda cb: self.on(event_type, cb, once=once, scope=scope)

        if not callable(listener):
            raise ValueError("Listener must be callable")

        # Fire NewListener before adding the new listener
        self.emit(NewListener(event_type, listener))

        opts = ListenerOpts.NOP
        if once:
            opts |= ListenerOpts.ONCE

        # Add the given listener to queue
        self._listeners[event_type][tuple(scope.split("."))][listener] = opts

        return listener

    def emit(self, event_instance: object, *, scope: str = "") -> bool:
        """Emit an event, and execute its listeners.

        Arguments:
            event_instance: Event instance to be emitted.
            scope: Define till which scopes this event will execute its listeners.

        Raises:
            ValueError: event_instance is an instance of a builtin type, or it is a type instead
                        of an instance.
            BaseException: Re-raise event instance if it is a BaseException

        Returns:
            Whether this event emission resulted in any listener execution.

        """
        event_type = type(event_instance)
        handled = self._emit(event_type, event_instance, tuple(scope.split(".")))

        # Exception event special case
        if not handled and isinstance(event_instance, Exception):
            # Raise exception to user context when there is no listener registered to handle it
            raise RuntimeError(
                f"No listener registered to handle the event generate by {event_type.__qualname__}"
            ) from event_instance

        return handled

    def listeners(
        self, event_type: T.Type[K], *, scope: T.Optional[str] = None
    ) -> T.Sequence[ListenerCb[K]]:
        """List all listeners, limited by scope, registered to the given event type.

        Arguments:
            event_type: Define from which event types the listeners will be retrieve.
            scope: Define scope to limit listeners retrieval.

        Returns:
            A `Sequence` containing all listeners attached to given event type, limited by the \
            given scope

        """
        return tuple(
            listener
            for _, listener in self._limit_scope(
                scope,
                (
                    (listeners_scope, listener)
                    for listeners_scope, listeners in self._listeners[event_type].items()
                    for listener in listeners
                ),
            )
        )

    def remove_listener(
        self, listener: ListenerCb[K], event_type: T.Type[K], *, scope: T.Optional[str] = None
    ) -> bool:
        """Removes listener, limited by scope, from given event type.

        Not passing an explicit scope results in the removal of the given listener from all scopes
        of the given event.
        To target only the empty scope pass an empty string at the scope argument.

        Arguments:
            listener: Define the listener to be removed.
            event_type: Define from which event types the listeners will be removed.
            scope: Define scope to limit listener removal.

        Returns:
            Whether any listener removal occurred.

        """
        if event_type not in self._listeners:
            return False

        removal = False
        for listeners_scope, listeners in self._limit_scope(
            scope, self._listeners[event_type].items()
        ):
            removal = bool(listeners.pop(listener, None)) or removal
            if not listeners:  # Clear empty scopes
                del self._listeners[event_type][listeners_scope]

        if not self._listeners[event_type]:  # Clear empty event types
            del self._listeners[event_type]

        return removal

    @T.overload
    def remove_all_listeners(
        self, event_type: T.Type[K], *, scope: T.Optional[str] = None
    ) -> bool:
        ...

    @T.overload
    def remove_all_listeners(
        self, event_type: Te.Literal[None] = None, *, scope: Te.Literal[None]
    ) -> bool:
        ...

    def remove_all_listeners(
        self, event_type: T.Optional[T.Type[K]] = None, *, scope: T.Optional[str] = None
    ) -> bool:
        """Remove all listeners, limited by scope, attached to event.

        If event is None, remove all listeners on all events.
        A scope shouldn't be specified in this case.

        Not passing an explicit scope results in the complete removal of the given event.
        To target only the empty scope pass an empty string at the scope argument.

        Arguments:
            event_type: Define from which event types all listeners will be removed.
            scope: Define scope to limit listeners removal.

        Returns:
            Whether any listener removal occurred.

        """
        if not self._listeners:
            return False

        if event_type is None:
            self._listeners.clear()
            return True

        if event_type not in self._listeners:
            return False

        removal = False
        if scope is None:
            removal = True
        else:
            for listeners_scope, _ in self._limit_scope(
                scope, self._listeners[event_type].items()
            ):
                removal = True
                del self._listeners[event_type][listeners_scope]

            if self._listeners[event_type]:
                return removal

        del self._listeners[event_type]
        return removal


__all__ = (
    "Emitter",
    "NewListener",
    "ListenerFutureError",
    "ListenerExecutionError",
)
