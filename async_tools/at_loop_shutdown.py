# Internal
import typing as T
from asyncio import AbstractEventLoop
from weakref import WeakKeyDictionary

# Project
from .operator import anext
from .attempt_await import attempt_await
from .wait_with_care import wait_with_care
from .get_running_loop import get_running_loop

cb_map: T.MutableMapping[AbstractEventLoop, T.Optional[T.List[T.Callable[[], T.Any]]]] = (
    WeakKeyDictionary()
)


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
        callbacks = cb_map[loop]
        if not callbacks:
            return

        coro = wait_with_care(
            *(attempt_await(callback) for callback in callbacks), ignore_cancelled=True
        )

        cb_map[loop] = None

        await coro

        del cb_map[loop]


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
    elif not loop.is_running():
        # If the loop isn't running the asyncgen won't be registered internally until next run.
        # To avoid confusion it is best to only allow running loops to have at_stop callbacks.
        raise RuntimeError("Loop must be running to schedule a at_loop_exit callback")

    callbacks: T.Optional[T.List[T.Callable[[], T.Any]]]
    if loop not in cb_map:
        # Execute scheduling asyncgen first iteration to register it internally
        loop.create_task(anext(_schedule_at_loop_shutdown(loop)))
        cb_map[loop] = callbacks = []
    else:
        callbacks = cb_map[loop]

    if callbacks is None:
        # Loop is already closing, just execute callback
        loop.create_task(wait_with_care(attempt_await(callback), ignore_cancelled=True))
    else:
        callbacks.append(callback)
