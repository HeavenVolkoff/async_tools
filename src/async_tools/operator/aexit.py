# Internal
import typing as T
from asyncio import ALL_COMPLETED, Future, wait

# Project
from ..context_manager import AsyncContextManager


async def aexit(*disposables: T.Union[T.AsyncContextManager[T.Any], AsyncContextManager]) -> None:
    """External access to AbstractAsyncContextManager __aexit__ magic method.

    See also: :meth:`~.abstract_async_context_manager.__aexit__`

    Arguments:
        disposables: Objects to be disposed.

    """

    done, pending = await wait(
        tuple(
            T.cast(T.Awaitable[bool], disposable.__aexit__(None, None, None))
            for disposable in disposables
        ),
        return_when=ALL_COMPLETED,
    )  # type: T.Set[Future[bool]], T.Set[Future[bool]]

    assert not pending

    for fut in done:
        exc = fut.exception()
        if exc:
            raise exc


__all__ = ("aexit",)
