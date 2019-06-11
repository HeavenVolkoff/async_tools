# Internal
import sys
import asyncio
import unittest

# External
from async_tools import get_running_loop


class TestError(Exception):
    pass


class Policy(asyncio.DefaultEventLoopPolicy):
    def get_event_loop(self):
        raise TestError


class GetEventLoopTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.old_policy = asyncio.get_event_loop_policy()

    def tearDown(self):
        super().tearDown()
        asyncio.set_event_loop_policy(self.old_policy)

    @unittest.skipUnless(sys.version_info >= (3, 7), "This test is only valid in Python >= 3.7")
    def test_get_running_loop_native(self):
        from asyncio import get_running_loop as native

        self.assertIs(get_running_loop, native)

    def test_get_running_loop(self):
        loop = None
        try:
            asyncio.set_event_loop_policy(Policy())
            loop = asyncio.new_event_loop()

            with self.assertRaisesRegex(RuntimeError, "no running"):
                self.assertIs(get_running_loop(), None)

            async def func():
                self.assertIs(get_running_loop(), loop)

            loop.run_until_complete(func())

        finally:
            if loop is not None:
                loop.close()

        with self.assertRaisesRegex(RuntimeError, "no running"):
            self.assertIs(get_running_loop(), None)


if __name__ == "__main__":
    unittest.main()
