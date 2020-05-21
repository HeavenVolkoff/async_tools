# Standard
from concurrent.futures.thread import ThreadPoolExecutor
import asyncio
import unittest

# External
from async_tools import shutdown_default_executor


class ShutdownDefaultExecutorTest(unittest.TestCase):
    def test_shutdown_default_executor(self):
        loop = asyncio.get_event_loop()

        def a():
            pass

        async def test_thread():
            await loop.run_in_executor(None, a)

        loop.run_until_complete(test_thread())

        if hasattr(loop, "_default_executor"):
            default_executor: ThreadPoolExecutor = getattr(loop, "_default_executor")
            self.assertIsNotNone(default_executor)
            self.assertFalse(getattr(default_executor, "_shutdown", False))

        loop.run_until_complete(shutdown_default_executor())

        if hasattr(loop, "_default_executor"):
            default_executor: ThreadPoolExecutor = getattr(loop, "_default_executor")
            self.assertIsNotNone(default_executor)
            self.assertTrue(getattr(default_executor, "_shutdown", False))

        loop.close()
