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
from concurrent.futures import Executor
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor

# External
import typing_extensions as Te

# Project
from ._from_coroutine import _from_coroutine
from ..at_loop_shutdown import at_loop_shutdown
from ..get_running_loop import get_running_loop

# Generic types
K = T.TypeVar("K")
L = T.TypeVar("L", bound=Executor)
M = T.TypeVar("M", covariant=True)


async def _delay_executor(
    executor: Executor,
    func: T.Callable[..., K],
    args: T.Tuple[T.Any, ...],
    kwargs: T.Dict[str, T.Any],
) -> K:
    loop = get_running_loop()

    if kwargs:
        return await loop.run_in_executor(executor, partial(func, *args, **kwargs))

    return await loop.run_in_executor(executor, func, *args)


class DecoratorProtocol(Te.Protocol[L, M]):
    __decorator__: "_BlockingDecorator[L]"

    def __call__(self, *args: T.Any, **kwargs: T.Any) -> T.Union[T.Awaitable[M], M]:
        ...


class _BlockingDecorator(T.Generic[L]):
    DEFAULT_POOL: T.MutableMapping[AbstractEventLoop, T.Set[Executor]] = WeakKeyDictionary()

    def __init__(self, executor_cls: T.Type[L], executor: T.Optional[T.Union[int, L]] = None):
        if isinstance(executor, int):
            managed = True
            executor = executor_cls(max_workers=executor)  # type: ignore
        else:
            if executor:
                managed = False
                if not isinstance(executor, executor_cls):
                    raise TypeError(f"Decorator executor must be a {executor_cls.__qualname__}")
            else:
                managed = True

        self._managed = managed
        self._executor = executor
        self._executor_cls = executor_cls

    @property
    def executor(self) -> T.Optional[L]:
        return self._executor

    @executor.setter
    def executor(self, executor: L) -> None:
        if self._executor:
            raise RuntimeError("Executor is already defined for this blocking decorator")

        self._executor = executor

    def _clear_executor(self, loop: AbstractEventLoop) -> None:
        loop_pool = self.DEFAULT_POOL[loop]

        if self._executor:
            if self._executor in loop_pool:
                loop_pool.remove(self._executor)

            self._executor.shutdown(wait=True)
            self._executor = None

    def __call__(self, wrapped: T.Callable[..., K]) -> DecoratorProtocol[L, K]:
        @wraps(wrapped)
        def wrapper(*args: T.Any, **kwargs: T.Any) -> T.Union[T.Awaitable[K], K]:
            if not _from_coroutine():
                return wrapped(*args, **kwargs)

            loop = get_running_loop()

            if self._executor:
                executor = self._executor
            else:
                try:
                    loop_pool = self.DEFAULT_POOL[loop]
                except KeyError:
                    loop_pool = set()

                candidates = tuple(
                    candidate
                    for candidate in loop_pool
                    if isinstance(candidate, self._executor_cls)
                )

                if candidates:
                    # Candidates should be a single element tuple
                    assert len(candidates) == 1
                    executor, = candidates
                else:
                    self._executor = executor = self._executor_cls()
                    loop_pool.add(executor)

                if self._managed:
                    at_loop_shutdown(self._clear_executor, loop=loop)
                    self._managed = False

                self.DEFAULT_POOL[loop] = loop_pool

            return _delay_executor(executor, wrapper, args, kwargs)

        wrapper.__decorator__ = self  # type: ignore

        return wrapper  # type: ignore


@T.overload
def thread(func_or_executor: T.Callable[..., K]) -> DecoratorProtocol[ThreadPoolExecutor, K]:
    ...


@T.overload
def thread(
    func_or_executor: T.Union[ThreadPoolExecutor, int]
) -> T.Callable[[T.Callable[..., K]], DecoratorProtocol[ThreadPoolExecutor, K]]:
    ...


def thread(
    func_or_executor: T.Union[T.Callable[..., K], ThreadPoolExecutor, int]
) -> T.Union[
    DecoratorProtocol[ThreadPoolExecutor, K],
    T.Callable[[T.Callable[..., K]], DecoratorProtocol[ThreadPoolExecutor, K]],
]:
    """
    Decorator indicating that a function performs a blocking operation.
    If called from synchronous Python code, the function runs normally.
    However, if called from a coroutine, curio arranges for it to run
    in a thread.
    """
    return (
        _BlockingDecorator(ThreadPoolExecutor)(func_or_executor)
        if callable(func_or_executor)
        else _BlockingDecorator(ThreadPoolExecutor, func_or_executor)
    )


@T.overload
def process(func_or_executor: T.Callable[..., K]) -> DecoratorProtocol[ProcessPoolExecutor, K]:
    ...


@T.overload
def process(
    func_or_executor: T.Union[ProcessPoolExecutor, int]
) -> T.Callable[[T.Callable[..., K]], DecoratorProtocol[ProcessPoolExecutor, K]]:
    ...


def process(
    func_or_executor: T.Union[T.Callable[..., K], ProcessPoolExecutor, int]
) -> T.Union[
    DecoratorProtocol[ProcessPoolExecutor, K],
    T.Callable[[T.Callable[..., K]], DecoratorProtocol[ProcessPoolExecutor, K]],
]:
    """
    Decorator indicating that a function performs a blocking operation.
    If called from synchronous Python code, the function runs normally.
    However, if called from a coroutine, curio arranges for it to run
    in a thread.
    """
    return (
        _BlockingDecorator(ProcessPoolExecutor)(func_or_executor)
        if callable(func_or_executor)
        else _BlockingDecorator(ProcessPoolExecutor, func_or_executor)
    )


__all__ = ("process", "thread")
