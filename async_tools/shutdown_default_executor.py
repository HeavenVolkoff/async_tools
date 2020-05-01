"""
This code is a modified version of python 3.9's BaseEventLoop.shutdown_default_executor method
@link: https://github.com/python/cpython/blob/eb0d359b4b0e14552998e7af771a088b4fd01745/Lib/asyncio/base_events.py#L556-L567
@license: https://github.com/python/cpython/blob/eb0d359b4b0e14552998e7af771a088b4fd01745/LICENSE
"""

# Internal
import typing as T
from threading import Thread

if T.TYPE_CHECKING:
    # Internal
    from asyncio import Future, AbstractEventLoop
    from concurrent.futures.thread import ThreadPoolExecutor


def _do_shutdown(
    loop: "AbstractEventLoop", default_executor: "ThreadPoolExecutor", future: "Future[None]"
) -> None:
    try:
        default_executor.shutdown(wait=True)
        loop.call_soon_threadsafe(future.set_result, None)
    except Exception as ex:
        loop.call_soon_threadsafe(future.set_exception, ex)


async def shutdown_default_executor(loop: "AbstractEventLoop") -> None:
    """Schedule the shutdown of the default executor."""

    og: T.Optional[T.Callable[[], T.Awaitable[None]]] = getattr(
        loop, "shutdown_default_executor", None
    )
    if og:
        return await og()

    # self._executor_shutdown_called = True
    default_executor = getattr(loop, "_default_executor", None)

    if default_executor is None:
        return

    future = loop.create_future()
    thread = Thread(target=_do_shutdown, args=(loop, default_executor, future))
    thread.start()
    try:
        await future
    finally:
        thread.join()


__all__ = ("shutdown_default_executor",)
