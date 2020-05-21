# Standard
from asyncio import AbstractEventLoop
from weakref import WeakKeyDictionary
import typing as T

# Project
from .attempt_await import attempt_await
from .wait_with_care import wait_with_care
from .get_running_loop import get_running_loop


class ShutdownCallablesMeta(type):
    INSTANCES: T.MutableMapping[AbstractEventLoop, "ShutdownCallables"] = WeakKeyDictionary()

    def __call__(cls, *args: T.Any, **kwargs: T.Any) -> "ShutdownCallables":
        loop: AbstractEventLoop = kwargs.pop("loop")
        if loop in cls.INSTANCES:
            return cls.INSTANCES[loop]

        shutdown_callbacks: ShutdownCallables = super(ShutdownCallablesMeta, cls).__call__()
        loop.create_task(shutdown_callbacks())

        cls.INSTANCES[loop] = shutdown_callbacks
        return shutdown_callbacks


class ShutdownCallables(metaclass=ShutdownCallablesMeta):
    def __init__(self, **__: T.Any) -> None:
        self._schedule: T.Optional[T.AsyncGenerator[None, None]] = None
        self._callbacks: T.List[T.Callable[[AbstractEventLoop], T.Any]] = []

    @property
    def available(self) -> bool:
        return self._schedule is not None

    async def _schedule_at_loop_shutdown(self) -> T.AsyncGenerator[None, None]:
        """Responsible to scheduling all shutdown callbacks of a loop. This rely on the common practice
        of shutting down async generators after the loop stops. Which allows us to detect such event and
        execute the callbacks.

        More info: https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.shutdown_asyncgens
        """
        loop = get_running_loop()

        try:
            yield None
        finally:
            self._schedule = None
            callbacks = self._callbacks
            self._callbacks.clear()

            if not loop.is_closed() and callbacks:
                loop.create_task(
                    wait_with_care(
                        *(attempt_await(callback(loop)) for callback in callbacks),
                        ignore_cancelled=True,
                    )
                )

    def __call__(self) -> T.Awaitable[None]:
        self._schedule = self._schedule_at_loop_shutdown()
        return self._schedule.asend(None)

    def append(self, callback: T.Callable[[AbstractEventLoop], T.Any]) -> None:
        self._callbacks.append(callback)


def at_loop_shutdown(
    callback: T.Callable[[AbstractEventLoop], T.Any], *, loop: T.Optional[AbstractEventLoop] = None
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

    shutdown_callbacks = ShutdownCallables(loop=loop)
    if shutdown_callbacks.available:
        shutdown_callbacks.append(callback)
    else:
        # Loop already called `shutdown_asyncgens`, just execute callback
        loop.create_task(wait_with_care(attempt_await(callback(loop)), ignore_cancelled=True))
