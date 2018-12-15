__all__ = ("AsyncGeneratorCloseContext",)

# Internal
import typing as T

# Project
from .abstract_async_context_manager import AbstractAsyncContextManager

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


# noinspection PyPep8Naming
class AsyncGeneratorCloseContext(T.Generic[K, L], AbstractAsyncContextManager):
    def __init__(self, aiter: T.AsyncGenerator[K, L]) -> None:
        self._aiter = aiter

    async def __aenter__(self) -> T.AsyncGenerator[K, L]:
        return self._aiter.__aiter__()

    async def __aexit__(self, _: T.Any, __: T.Any, ___: T.Any) -> T.Optional[bool]:
        await self._aiter.aclose()
        return False
