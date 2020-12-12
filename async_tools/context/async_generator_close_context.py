# Internal
import typing as T

# External
# Generic types
from async_tools import attempt_await

K = T.TypeVar("K")


# TODO: Rename this when deprecation belows goes through
class AsyncGeneratorCloseContext(T.AsyncContextManager[K]):
    def __init__(self, aiter: K) -> None:
        self._aiter = aiter

    async def __aenter__(self) -> K:
        if callable(getattr(self._aiter, "__aiter__")):
            # Internal
            from warnings import warn

            warn(
                "Returning AsyncIterable is deprecated and will be removed in next version",
                DeprecationWarning,
            )

            return T.cast(T.AsyncGenerator[T.Any, T.Any], self._aiter).__aiter__()  # type: ignore

        return self._aiter

    async def __aexit__(self, _: T.Any, __: T.Any, ___: T.Any) -> T.Literal[False]:
        aclose = getattr(self._aiter, "aclose", None)
        if callable(aclose):
            await attempt_await(aclose())
        return False


__all__ = ("AsyncGeneratorCloseContext",)
