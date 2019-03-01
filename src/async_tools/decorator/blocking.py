"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/curio/meta.py
See original licenses in:
    https://github.com/dabeaz/curio/blob/3452129f513df501b962f456ef68c4204c2ad4c2/LICENSE
"""

# Internal
import typing as T
from functools import wraps
from concurrent.futures import Executor
from concurrent.futures.process import ProcessPoolExecutor

# Project
from ..operator import anext
from ._from_coroutine import _from_coroutine
from ..get_running_loop import get_running_loop

_default_executor: T.Optional[ProcessPoolExecutor] = None


async def _schedule_default_executor_cleanup(executor: Executor) -> T.AsyncGenerator[None, None]:
    try:
        yield
    except GeneratorExit:
        pass
    finally:
        executor.shutdown(wait=False)


def thread(func: T.Callable[..., T.Any]) -> T.Callable[..., T.Any]:
    """
    Decorator indicating that a function performs a blocking operation.
    If called from synchronous Python code, the function runs normally.
    However, if called from a coroutine, curio arranges for it to run
    in a thread.
    """

    @wraps(func)
    def wrapper(*args: T.Any, **kwargs: T.Any) -> T.Any:
        if _from_coroutine():
            loop = get_running_loop()

            if kwargs:
                return loop.run_in_executor(None, lambda: func(*args, **kwargs))

            return loop.run_in_executor(None, func, *args)
        else:
            return func(*args, **kwargs)

    return wrapper


def process(func: T.Callable[..., T.Any]) -> T.Callable[..., T.Any]:
    """
    Decorator indicating that a function performs a blocking operation.
    If called from synchronous Python code, the function runs normally.
    However, if called from a coroutine, curio arranges for it to run
    in a thread.
    """

    @wraps(func)
    def wrapper(*args: T.Any, **kwargs: T.Any) -> T.Any:
        global _default_executor

        if _from_coroutine():
            loop = get_running_loop()

            if _default_executor is None:
                _default_executor = ProcessPoolExecutor()
                loop.create_task(anext(_schedule_default_executor_cleanup(_default_executor)))

            if kwargs:
                return loop.run_in_executor(_default_executor, lambda: func(*args, **kwargs))

            return loop.run_in_executor(_default_executor, func, *args)
        else:
            return func(*args, **kwargs)

    return wrapper


__all__ = ("process", "thread")
