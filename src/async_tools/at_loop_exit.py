# Internal
import typing as T
from asyncio import AbstractEventLoop
from weakref import WeakKeyDictionary

# Project
from .operator import anext
from .attempt_await import attempt_await
from .wait_with_care import wait_with_care
from .get_running_loop import get_running_loop

_callbacks = (
    WeakKeyDictionary()
)  # type: WeakKeyDictionary[AbstractEventLoop, T.Optional[T.List[T.Callable[[], T.Any]]]]


async def _schedule_at_loop_exit(loop: AbstractEventLoop) -> T.AsyncGenerator[None, None]:
    try:
        yield
    except GeneratorExit:
        pass
    finally:
        callbacks = _callbacks[loop]
        if not callbacks:
            return

        coro = wait_with_care(
            *(attempt_await(callback, loop=loop) for callback in callbacks), ignore_cancelled=True
        )

        _callbacks[loop] = None

        await coro

        del _callbacks[loop]


def at_loop_exit(
    callback: T.Callable[[], T.Any], *, loop: T.Optional[AbstractEventLoop] = None
) -> None:
    if not loop:
        loop = get_running_loop()

    if not loop.is_running():
        raise RuntimeError("Loop must be running to schedule a at_loop_exit callback")

    callbacks: T.Optional[T.List[T.Callable[[], T.Any]]]
    if loop not in _callbacks:
        loop.create_task(anext(_schedule_at_loop_exit(loop)))
        _callbacks[loop] = callbacks = []
    else:
        callbacks = _callbacks[loop]

    if callbacks is None:
        loop.create_task(wait_with_care(attempt_await(callback, loop=loop), ignore_cancelled=True))
    else:
        callbacks.append(callback)
