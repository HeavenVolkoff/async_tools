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


async def _schedule_at_loop_shutdown(loop: AbstractEventLoop) -> T.AsyncGenerator[None, None]:
    """Responsible to scheduling all shutdown callbacks of a loop. This rely on the common practice
    of shutting down async generators after the loop stops. Which allows us to detect such event and
    execute the callbacks.

    More info: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.shutdown_asyncgens
    """
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


def at_loop_shutdown(
    callback: T.Callable[[], T.Any], *, loop: T.Optional[AbstractEventLoop] = None
) -> None:
    """Allows scheduling a callback to be called during event loop shutdown logic.

    Args:
        callback: Callback function to be called while lopping is shutting down.
        loop: Aforementioned event loop.

    .. Warning:
        This rely in the shutdown_asyncgens function being called after stopping the loop.
        If you are using `asyncio.run` or any such function to manage the loop life-cycle,
        you probably good. However if you are managing it on your own, make sure to call
        shutdown_asyncgens after the loops stops or this won't work.
        More info: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.shutdown_asyncgens

    """
    if not loop:
        # Get current loop if none was passed
        loop = get_running_loop()

    if not loop.is_running():
        # If the loop isn't running the asyncgen won't be registered internally until next run.
        # To avoid confusion it is best to only allow running loops to have at_stop callbacks.
        raise RuntimeError("Loop must be running to schedule a at_loop_exit callback")

    callbacks: T.Optional[T.List[T.Callable[[], T.Any]]]
    if loop not in _callbacks:
        # Execute scheduling asyncgen first iteration to register it internally
        loop.create_task(anext(_schedule_at_loop_shutdown(loop)))
        _callbacks[loop] = callbacks = []
    else:
        callbacks = _callbacks[loop]

    if callbacks is None:
        # Loop is already closing, just execute callback
        loop.create_task(wait_with_care(attempt_await(callback, loop=loop), ignore_cancelled=True))
    else:
        callbacks.append(callback)
