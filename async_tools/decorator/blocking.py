"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/curio/meta.py
See original licenses in:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/LICENSE
"""

# Internal
import typing as T
from sys import version_info
from asyncio import get_running_loop
from functools import wraps, partial
from concurrent.futures import BrokenExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor

# Project
from ._from_coroutine import _from_coroutine
from ..at_loop_shutdown import at_loop_shutdown

# Generic types
K = T.TypeVar("K")
L = T.TypeVar("L", ThreadPoolExecutor, ProcessPoolExecutor)
M = T.TypeVar("M", covariant=True)


class DecoratorProtocol(T.Protocol[L, M]):
    __decorator__: "_BlockingDecorator[L]"

    def __call__(self, *args: T.Any, **kwargs: T.Any) -> T.Union[T.Awaitable[M], M]:
        ...


class _BlockingDecorator(T.Generic[L]):
    def __init__(self, cls: T.Type[L], executor: T.Optional[T.Union[int, L]] = None):
        self._managed = False
        self._workers: T.Optional[int] = None
        self._executor: T.Optional[L] = None
        self._external = False
        self._executor_cls: T.Type[L] = cls

        if isinstance(executor, int):
            self._workers = executor
        elif isinstance(executor, cls):
            self._external = True
            self._executor = executor
        elif executor is not None:
            raise TypeError(f"Decorator executor must be a {cls.__qualname__}")

    @property
    def executor(self) -> T.Optional[L]:
        if self._executor is None:
            self._update_executor()
            assert self._executor is not None
        return self._executor

    @executor.setter
    def executor(self, executor: L) -> None:
        if self._executor:
            raise RuntimeError("Executor is already defined for this blocking decorator")

        self._executor = executor

    def _clear_executor(self, *, wait: bool = True) -> None:
        if self._executor:
            if version_info >= (3, 9):
                self._executor.shutdown(wait=wait, cancel_futures=True)  # type: ignore
            else:
                self._executor.shutdown(wait=wait)
            self._executor = None

    def _update_executor(self) -> None:
        self._clear_executor(wait=False)

        self._executor = self._executor_cls(max_workers=self._workers)

        if not self._managed:
            at_loop_shutdown(lambda _: self._clear_executor())
            self._managed = True

    async def _exec(self, func: T.Callable[..., T.Any], *args: T.Any, **kwargs: T.Any) -> K:
        loop = get_running_loop()
        _break = False
        while True:
            try:
                if kwargs:
                    return await loop.run_in_executor(
                        self._executor, partial(func, *args, **kwargs)
                    )

                return await loop.run_in_executor(self._executor, func, *args)
            except BrokenExecutor as exc:
                if _break:
                    raise exc
                _break = True
                loop.call_exception_handler({"message": "Executor broke", "exception": exc})
                self._update_executor()
                continue

    def __call__(self, wrapped: T.Callable[..., K]) -> DecoratorProtocol[L, K]:
        @wraps(wrapped)
        def wrapper(*args: T.Any, **kwargs: T.Any) -> T.Union[T.Awaitable[K], K]:
            if not _from_coroutine():
                return wrapped(*args, **kwargs)

            # _exec is called with wrapper instead of wrapped, this is to appease pickle, as it
            # fails with UnpicklingError when _exec is called with wrapped
            return self._exec(wrapper, *args, **kwargs)

        setattr(wrapper, "__decorator__", self)

        return T.cast(DecoratorProtocol[L, K], wrapper)


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
