__all__ = ("AsyncContextManager",)


try:
    from typing import AsyncContextManager  # type: ignore
except ImportError:
    import typing as T
    from abc import ABCMeta, abstractmethod
    from types import TracebackType

    K = T.TypeVar("K")

    class AsyncContextManager(T.Generic[K], metaclass=ABCMeta):  # type: ignore
        """An abstract base class for asynchronous context managers."""

        async def __aenter__(self) -> T.Union[K, "AsyncContextManager[K]"]:
            """Return `self` upon entering the runtime context."""
            return self

        @abstractmethod
        async def __aexit__(
            self,
            exc_type: T.Optional[T.Type[BaseException]],
            exc_value: T.Optional[BaseException],
            traceback: T.Optional[TracebackType],
        ) -> T.Optional[bool]:
            """Raise any exception triggered within the runtime context."""
            return None
