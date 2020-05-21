# Standard
from asyncio import ALL_COMPLETED, wait
import typing as T

# External
import typing_extensions as Te


async def aexit(*disposables: Te.AsyncContextManager[T.Any]) -> None:
    """External access to AbstractAsyncContextManager __aexit__ magic method.

    See also: :meth:`~.abstract_async_context_manager.__aexit__`

    Arguments:
        disposables: Objects to be disposed.

    """

    done, pending = await wait(
        tuple(disposable.__aexit__(None, None, None) for disposable in disposables),
        return_when=ALL_COMPLETED,
    )

    # Ensure no future remained pending
    assert not pending

    for fut in done:
        exc = fut.exception()
        if exc:
            raise exc


__all__ = ("aexit",)
