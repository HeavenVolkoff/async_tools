# Standard
import typing as T

# External
import typing_extensions as Te

# Generic types
K = T.TypeVar("K")


# TODO: Rename this when deprecation belows goes through
class AsyncGeneratorCloseContext(Te.AsyncContextManager[K]):
    def __init__(self, aiter: K) -> None:
        self._aiter = aiter

    async def __aenter__(self) -> K:
        if callable(getattr(self._aiter, "__aiter__")):
            from warnings import warn

            warn(
                "Returning AsyncIterable is deprecated and will be removed in next version",
                DeprecationWarning,
            )

            return T.cast(T.AsyncGenerator[T.Any, T.Any], self._aiter).__aiter__()

        return self._aiter

    async def __aexit__(self, _: T.Any, __: T.Any, ___: T.Any) -> Te.Literal[False]:
        await self._aiter.aclose()
        return False


__all__ = ("AsyncGeneratorCloseContext",)
