# Internal
import asyncio
import functools


def _async_test(func):
    """Decorator to turn an async function into a test case.

    Work derived from cpython.

    Reference:
        https://github.com/python/cpython/blob/db8e3a1e4476620b2b5aaf57acfc3ef58a08213b/Lib/test/test_contextlib_async.py
    See original licenses in:
        https://github.com/python/cpython/blob/9a69ae8a78785105ded02b083b2e5cd2dd939307/LICENSE
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
            asyncio.set_event_loop_policy(None)

    return wrapper
