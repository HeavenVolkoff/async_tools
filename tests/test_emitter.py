# Internal
import typing as T
import asyncio
import unittest
from typing import NamedTuple
from asyncio import Future, AbstractEventLoop
from unittest.mock import Mock

# External
import asynctest

# External
from async_tools.emitter import Emitter, ListenerFutureError, ListenerExecutionError

# Generic types
K = T.TypeVar("K")


class MockAwaitable(Future):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._awaited = 0
        self._add_callbacks = 0

    def __await__(self) -> T.Generator[T.Any, None, K]:
        self._awaited += 1
        return super().__await__()

    @property
    def callbacks(self) -> T.Sequence[T.Callable[..., T.Any]]:
        return tuple(zip(*self._callbacks))[0]

    @property
    def times_awaited(self) -> int:
        return self._awaited

    @property
    def added_callbacks(self) -> int:
        return self._add_callbacks

    def add_done_callback(self, *args, **kwargs) -> None:
        self._add_callbacks += 1
        return super().add_done_callback(*args, **kwargs)


@asynctest.strict
class EmitterTestCase(asynctest.TestCase, unittest.TestCase):
    @asynctest.fail_on(unused_loop=False)
    def test_listener_simple(self) -> None:
        ee = Emitter()
        listener = Mock()

        class Event(NamedTuple):
            data: str

        ee.on(Event, listener)

        event = Event("Wowow")
        ee.emit(event)

        listener.assert_called_once_with(event)

    @asynctest.fail_on(unused_loop=False)
    def test_listener_decorator(self) -> None:
        ee = Emitter()
        mock = Mock()

        class Event(NamedTuple):
            data: str

        @ee.on(Event)
        def listener(event: Event) -> None:
            self.assertEqual("Wowow", event.data)
            mock(event)

        event = Event("Wowow")
        ee.emit(event)

        mock.assert_called_once_with(event)

    @asynctest.fail_on(unused_loop=False)
    def test_listener_callable_class(self) -> None:
        ee = Emitter()
        mock = Mock()
        this = self

        class Event(NamedTuple):
            data: str

        class Listener:
            def __call__(self, event: Event) -> None:
                this.assertEqual("Wowow", event.data)
                mock(event)

        ee.on(Event, Listener())

        event = Event("Wowow")
        ee.emit(event)

        mock.assert_called_once_with(event)

    async def test_listener_coroutine(self) -> None:
        ee = Emitter()
        mock = Mock()
        future = self.loop.create_future()

        class Event(NamedTuple):
            data: str

        @ee.on(Event)
        async def listener(event: Event) -> None:
            await asyncio.sleep(0)
            self.assertEqual("Wowow", event.data)
            mock(event)
            future.set_result(event)

        event = Event("Wowow")
        ee.emit(event)

        self.assertIs(event, await future)

        mock.assert_called_once_with(event)

    async def test_listener_awaitable(self) -> None:
        ee = Emitter()
        mock = MockAwaitable()

        class Event(NamedTuple):
            data: str

        @ee.on(Event)
        def listener(event: Event) -> T.Awaitable[None]:
            self.assertEqual("Wowow", event.data)
            return mock

        event = Event("Wowow")
        ee.emit(event)

        self.assertIn(ee._future_callback, mock.callbacks)

        mock.set_result(event)
        self.assertIs(event, await mock)
        self.assertEqual(1, mock.added_callbacks)
        self.assertEqual(1, mock.times_awaited)

    @asynctest.fail_on(unused_loop=False)
    def test_listener_execution_error(self) -> None:
        ee = Emitter()

        class Event(NamedTuple):
            data: str

        @ee.on(Event)
        def listener(_: T.Any) -> None:
            raise RuntimeError("Ooops...")

        event = Event("Wowow")

        with self.assertRaises(RuntimeError) as ctx:
            ee.emit(event)

        self.assertIsInstance(ctx.exception.__cause__, ListenerExecutionError)
        self.assertIsInstance(ctx.exception.__cause__.__cause__, RuntimeError)
        self.assertEqual(str(ctx.exception.__cause__.__cause__), "Ooops...")

    async def test_listener_coro_error(self) -> None:
        ee = Emitter()
        future = self.loop.create_future()

        class Event(NamedTuple):
            data: str

        @ee.on(Event)
        async def listener(_: T.Any) -> None:
            await asyncio.sleep(0)
            raise RuntimeError("Ooops...")

        @self.loop.set_exception_handler
        def handle_error(_, ctx) -> None:
            future.set_exception(ctx["exception"])

        event = Event("Wowow")
        ee.emit(event)

        with self.assertRaises(RuntimeError) as ctx:
            await future

        self.assertIsInstance(ctx.exception.__cause__, ListenerFutureError)
        self.assertIsInstance(ctx.exception.__cause__.__cause__, RuntimeError)
        self.assertEqual(str(ctx.exception.__cause__.__cause__), "Ooops...")
