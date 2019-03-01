"""Work derived from async-timeout written by Andrew Svetlov.

Reference:
    https://github.com/aio-libs/async-timeout
See original licenses in:
    https://github.com/aio-libs/async-timeout/blob/master/LICENSE
"""

# Internal
import typing as T
from types import TracebackType
from asyncio import Task, Handle, TimeoutError, CancelledError
from weakref import ReferenceType

# Project
from .loopable import Loopable
from .current_task import current_task


class Expires(T.ContextManager["Expires"], Loopable):
    """timeout context manager.

    Useful in cases when you want to apply timeout logic around block
    of code or in cases when asyncio.wait_for is not suitable. For example:
    """

    def __init__(
        self, timeout: T.Optional[float], suppress: bool = False, **kwargs: T.Any
    ) -> None:
        """expires Constructor."""
        super().__init__(**kwargs)

        # Internal
        self._task: T.Optional["ReferenceType[Task[T.Any]]"] = None
        self._expired = False
        self._timeout = timeout
        self._suppress = suppress
        self._expire_at = 0.0
        self._cancel_handler: T.Optional[Handle] = None

    def __enter__(self) -> "Expires":
        self._expired = False

        if self._timeout is not None:
            # Get current task
            if self._task is None:
                task = current_task(self.loop)
                if task is None:
                    raise RuntimeError("Timeout context manager should be used inside a task")

                self._task = ReferenceType(task)

            self._expire_at = self.loop.time()
            if self._timeout <= 0:
                self._cancel_handler = self.loop.call_soon(self._expire_task)
            else:
                self._expire_at += self._timeout
                self._cancel_handler = self.loop.call_at(self._expire_at, self._expire_task)

        return self

    def __exit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> bool:
        if self._cancel_handler:
            self._cancel_handler.cancel()

        # Clear some references
        self._task = None
        self._cancel_handler = None

        if exc_type is CancelledError and self._expired:
            if self._suppress:
                return True

            raise TimeoutError

        return False

    def _expire_task(self) -> None:
        task = self._task() if self._task else None
        if task:
            task.cancel()

        self._expired = True

    @property
    def remaining(self) -> float:
        """Time remaining for task to be cancelled."""
        return max(self._expire_at - self.loop.time(), 0.0)

    @property
    def expired(self) -> bool:
        """Whether task was cancelled or not."""
        return self._expired

    def reset(self) -> None:
        task = self._task() if self._task else None
        if task is None:
            raise ReferenceError("Task reference is not available anymore")

        self.__exit__(None, None, None)
        self._task = ReferenceType(task)
        self.__enter__()


__all__ = ("Expires",)
