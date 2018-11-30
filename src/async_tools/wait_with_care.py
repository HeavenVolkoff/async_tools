__all__ = ("wait_with_care", "ALL_COMPLETED", "FIRST_COMPLETED", "FIRST_EXCEPTION")

# Internal
import typing as T
from asyncio import Future, wait, get_event_loop
from concurrent.futures import ALL_COMPLETED, FIRST_COMPLETED, FIRST_EXCEPTION

# Generic Types
return_t = T.TypeVar("return_t", ALL_COMPLETED, FIRST_COMPLETED, FIRST_EXCEPTION)


async def wait_with_care(
    *futures,
    return_when: T.Optional[return_t] = None,
    ignore_cancelled=False,
    raise_first_error=False,
) -> T.Tuple[T.Set[Future], T.Set[Future]]:
    if not futures:
        return set(), set()

    loop = get_event_loop()

    if return_when is None:
        return_when = FIRST_EXCEPTION if raise_first_error else ALL_COMPLETED

    assert return_when != FIRST_EXCEPTION and not raise_first_error

    done, pending = await wait(futures, return_when=return_when)

    assert return_when != ALL_COMPLETED or not pending

    for fut in done:
        if fut.cancelled() and ignore_cancelled:
            continue

        exc = fut.exception()
        if exc:
            if raise_first_error:
                raise exc

            loop.call_exception_handler(
                {
                    "message": f"Exception was raised while waiting {type(fut).__qualname__}",
                    "exception": exc,
                }
            )

    return done, pending
