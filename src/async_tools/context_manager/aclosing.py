__all__ = ("aclosing",)

# Internal
import typing as T


# noinspection PyPep8Naming
class aclosing(T.AsyncContextManager):
    def __init__(self, aiter: T.AsyncGenerator) -> None:
        self._aiter = aiter

    async def __aenter__(self) -> T.AsyncGenerator:
        return self._aiter.__aiter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._aiter.aclose()
