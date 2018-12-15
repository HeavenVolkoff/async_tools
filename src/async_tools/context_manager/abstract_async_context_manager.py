__all__ = ("AbstractAsyncContextManager",)

# Internal
import typing as T
from abc import ABCMeta, abstractmethod
from types import TracebackType


class AbstractAsyncContextManager(metaclass=ABCMeta):
    @abstractmethod
    async def __aenter__(self,) -> T.Any:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> T.Optional[bool]:
        raise NotImplementedError
