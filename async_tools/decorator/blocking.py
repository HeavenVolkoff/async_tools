"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/curio/meta.py
See original licenses in:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/LICENSE
"""

# Internal
import typing as T
from asyncio import AbstractEventLoop
from weakref import WeakKeyDictionary
from functools import wraps, partial
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor

# Project
from ._from_coroutine import _from_coroutine
from ..at_loop_shutdown import at_loop_shutdown
from ..get_running_loop import get_running_loop

# Generic types
K = T.TypeVar("K")

_loop_default_process_pool: T.MutableMapping[
    AbstractEventLoop, ProcessPoolExecutor
] = WeakKeyDictionary()


def _thread_annotation(
    func: T.Callable[..., K], thread_pool: T.Optional[ThreadPoolExecutor] = None
) -> T.Callable[..., T.Union[T.Awaitable[K], K]]:
    @wraps(func)
    def wrapper(*args: T.Any, **kwargs: T.Any) -> T.Union[T.Awaitable[K], K]:
        if _from_coroutine():
            loop = get_running_loop()

            if kwargs:
                return loop.run_in_executor(thread_pool, partial(func, *args, **kwargs))

            return loop.run_in_executor(thread_pool, func, *args)
        return func(*args, **kwargs)

    return wrapper


@T.overload
def thread(func_or_thread_pool: T.Callable[..., K]) -> T.Callable[..., T.Union[T.Awaitable[K], K]]:
    ...


@T.overload
def thread(
    func_or_thread_pool: ThreadPoolExecutor
) -> T.Callable[[T.Callable[..., K]], T.Callable[..., T.Union[T.Awaitable[K], K]]]:
    ...


def thread(
    func_or_thread_pool: T.Union[T.Callable[..., K], ThreadPoolExecutor]
) -> T.Union[
    T.Callable[..., T.Union[T.Awaitable[K], K]],
    T.Callable[[T.Callable[..., K]], T.Callable[..., T.Union[T.Awaitable[K], K]]],
]:
    """
    Decorator indicating that a function performs a blocking operation.
    If called from synchronous Python code, the function runs normally.
    However, if called from a coroutine, curio arranges for it to run
    in a thread.
    """
    if isinstance(func_or_thread_pool, ThreadPoolExecutor):
        return lambda func: _thread_annotation(func, func_or_thread_pool)

    assert callable(func_or_thread_pool)

    return _thread_annotation(func_or_thread_pool)


def _process_annotation(
    func: T.Callable[..., K], process_pool: T.Optional[ProcessPoolExecutor] = None
) -> T.Callable[..., T.Union[T.Awaitable[K], K]]:
    """
    Decorator indicating that a function performs a blocking operation.
    If called from synchronous Python code, the function runs normally.
    However, if called from a coroutine, curio arranges for it to run
    in a thread.
    """

    @wraps(func)
    def wrapper(*args: T.Any, **kwargs: T.Any) -> T.Any:
        nonlocal process_pool

        if _from_coroutine():
            loop = get_running_loop()

            if process_pool is None:
                if loop in _loop_default_process_pool:
                    process_pool = _loop_default_process_pool[loop]
                else:
                    _loop_default_process_pool[loop] = process_pool = ProcessPoolExecutor()
                    at_loop_shutdown(partial(process_pool.shutdown, wait=False))

            if kwargs:
                return loop.run_in_executor(process_pool, lambda: func(*args, **kwargs))

            return loop.run_in_executor(process_pool, func, *args)
        else:
            return func(*args, **kwargs)

    return wrapper


@T.overload
def process(
    func_or_process_pool: T.Callable[..., K]
) -> T.Callable[..., T.Union[T.Awaitable[K], K]]:
    ...


@T.overload
def process(
    func_or_process_pool: ProcessPoolExecutor
) -> T.Callable[[T.Callable[..., K]], T.Callable[..., T.Union[T.Awaitable[K], K]]]:
    ...


def process(
    func_or_process_pool: T.Union[T.Callable[..., K], ProcessPoolExecutor]
) -> T.Union[
    T.Callable[..., T.Union[T.Awaitable[K], K]],
    T.Callable[[T.Callable[..., K]], T.Callable[..., T.Union[T.Awaitable[K], K]]],
]:
    """
    Decorator indicating that a function performs a blocking operation.
    If called from synchronous Python code, the function runs normally.
    However, if called from a coroutine, curio arranges for it to run
    in a thread.
    """
    if isinstance(func_or_process_pool, ProcessPoolExecutor):
        return lambda func: _process_annotation(func, func_or_process_pool)

    assert callable(func_or_process_pool)

    return _process_annotation(func_or_process_pool)


__all__ = ("process", "thread")
