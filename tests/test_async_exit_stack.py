"""Work derived from cpython.

Reference:
    https://github.com/python/cpython/blob/db8e3a1e4476620b2b5aaf57acfc3ef58a08213b/Lib/test/test_contextlib_async.py
See original licenses in:
    https://github.com/python/cpython/blob/9a69ae8a78785105ded02b083b2e5cd2dd939307/LICENSE
"""

# Internal
import asyncio
import unittest

# External
from tests.misc import _async_test
from tests.base_exit_stack import TestBaseExitStack
from async_tools.context._async_exit_stack import AsyncExitStack


class TestAsyncExitStack(TestBaseExitStack, unittest.TestCase):
    class SyncAsyncExitStack(AsyncExitStack):
        @staticmethod
        def run_coroutine(coro):
            loop = asyncio.get_event_loop()

            f = asyncio.ensure_future(coro)
            f.add_done_callback(lambda f: loop.stop())
            loop.run_forever()

            exc = f.exception()

            if not exc:
                return f.result()
            else:
                context = exc.__context__

                try:
                    raise exc
                except:
                    exc.__context__ = context
                    raise exc

        def close(self):
            return self.run_coroutine(self.aclose())

        def __enter__(self):
            return self.run_coroutine(self.__aenter__())

        def __exit__(self, *exc_details):
            return self.run_coroutine(self.__aexit__(*exc_details))

    exit_stack = SyncAsyncExitStack

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.addCleanup(self.loop.close)
        self.addCleanup(asyncio.set_event_loop_policy, None)

    @_async_test
    async def test_async_callback(self):
        expected = [
            ((), {}),
            ((1,), {}),
            ((1, 2), {}),
            ((), dict(example=1)),
            ((1,), dict(example=1)),
            ((1, 2), dict(example=1)),
        ]
        result = []

        async def _exit(*args, **kwds):
            """Test metadata propagation"""
            result.append((args, kwds))

        async with AsyncExitStack() as stack:
            for args, kwds in reversed(expected):
                if args and kwds:
                    f = stack.push_async_callback(_exit, *args, **kwds)
                elif args:
                    f = stack.push_async_callback(_exit, *args)
                elif kwds:
                    f = stack.push_async_callback(_exit, **kwds)
                else:
                    f = stack.push_async_callback(_exit)
                self.assertIs(f, _exit)
            for wrapper in stack._exit_callbacks:
                self.assertIs(wrapper[1].__wrapped__, _exit)
                self.assertNotEqual(wrapper[1].__name__, _exit.__name__)
                self.assertIsNone(wrapper[1].__doc__, _exit.__doc__)

        self.assertEqual(result, expected)

        result = []
        async with AsyncExitStack() as stack:
            with self.assertRaises(TypeError):
                stack.push_async_callback(arg=1)
            with self.assertRaises(TypeError):
                self.exit_stack.push_async_callback(arg=2)
            with self.assertWarns(DeprecationWarning):
                stack.push_async_callback(callback=_exit, arg=3)
        self.assertEqual(result, [((), {"arg": 3})])

    @_async_test
    async def test_async_push(self):
        exc_raised = ZeroDivisionError

        async def _expect_exc(exc_type, exc, exc_tb):
            self.assertIs(exc_type, exc_raised)

        async def _suppress_exc(*exc_details):
            return True

        async def _expect_ok(exc_type, exc, exc_tb):
            self.assertIsNone(exc_type)
            self.assertIsNone(exc)
            self.assertIsNone(exc_tb)

        class ExitCM(object):
            def __init__(self, check_exc):
                self.check_exc = check_exc

            async def __aenter__(self):
                self.fail("Should not be called!")

            async def __aexit__(self, *exc_details):
                await self.check_exc(*exc_details)

        async with self.exit_stack() as stack:
            stack.push_async_exit(_expect_ok)
            self.assertIs(stack._exit_callbacks[-1][1], _expect_ok)
            cm = ExitCM(_expect_ok)
            stack.push_async_exit(cm)
            self.assertIs(stack._exit_callbacks[-1][1].__self__, cm)
            stack.push_async_exit(_suppress_exc)
            self.assertIs(stack._exit_callbacks[-1][1], _suppress_exc)
            cm = ExitCM(_expect_exc)
            stack.push_async_exit(cm)
            self.assertIs(stack._exit_callbacks[-1][1].__self__, cm)
            stack.push_async_exit(_expect_exc)
            self.assertIs(stack._exit_callbacks[-1][1], _expect_exc)
            stack.push_async_exit(_expect_exc)
            self.assertIs(stack._exit_callbacks[-1][1], _expect_exc)
            1 / 0

    @_async_test
    async def test_async_enter_context(self):
        class TestCM(object):
            async def __aenter__(self):
                result.append(1)

            async def __aexit__(self, *exc_details):
                result.append(3)

        result = []
        cm = TestCM()

        async with AsyncExitStack() as stack:

            @stack.push_async_callback  # Registered first => cleaned up last
            async def _exit():
                result.append(4)

            self.assertIsNotNone(_exit)
            await stack.enter_async_context(cm)
            self.assertIs(stack._exit_callbacks[-1][1].__self__, cm)
            result.append(2)

        self.assertEqual(result, [1, 2, 3, 4])

    @_async_test
    async def test_async_exit_exception_chaining(self):
        # Ensure exception chaining matches the reference behaviour
        async def raise_exc(exc):
            raise exc

        saved_details = None

        async def suppress_exc(*exc_details):
            nonlocal saved_details
            saved_details = exc_details
            return True

        try:
            async with self.exit_stack() as stack:
                stack.push_async_callback(raise_exc, IndexError)
                stack.push_async_callback(raise_exc, KeyError)
                stack.push_async_callback(raise_exc, AttributeError)
                stack.push_async_exit(suppress_exc)
                stack.push_async_callback(raise_exc, ValueError)
                1 / 0
        except IndexError as exc:
            self.assertIsInstance(exc.__context__, KeyError)
            self.assertIsInstance(exc.__context__.__context__, AttributeError)
            # Inner exceptions were suppressed
            self.assertIsNone(exc.__context__.__context__.__context__)
        else:
            self.fail("Expected IndexError, but no exception was raised")
        # Check the inner exceptions
        inner_exc = saved_details[1]
        self.assertIsInstance(inner_exc, ValueError)
        self.assertIsInstance(inner_exc.__context__, ZeroDivisionError)


if __name__ == "__main__":
    unittest.main()
