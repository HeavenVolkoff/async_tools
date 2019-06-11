__all__ = ("AsyncGeneratorCloseContext",)

# Internal
import typing as T

# External
import typing_extensions as Te

# Generic types
K = T.TypeVar("K")
L = T.TypeVar("L")


class AsyncGeneratorCloseContext(T.Generic[K, L], Te.AsyncContextManager[Te.AsyncGenerator[K, L]]):
    def __init__(self, aiter: T.AsyncGenerator[K, L]) -> None:
        self._aiter = aiter

    async def __aenter__(self) -> T.AsyncGenerator[K, L]:
        return self._aiter.__aiter__()

    async def __aexit__(self, _: T.Any, __: T.Any, ___: T.Any) -> T.Optional[bool]:
        await self._aiter.aclose()
        return False
