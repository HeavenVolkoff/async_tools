# Internal
import asyncio
import unittest

# External
import asynctest
from async_tools import wait_with_care


class WaitWithCareTestCase(asynctest.TestCase, unittest.TestCase):
    async def test_wait_with_care_simple(self):
        async def long_running_task():
            await asyncio.sleep(0.01)
            return "done"

        done, pending = await wait_with_care(long_running_task())

        self.assertFalse(pending)
        self.assertEqual(len(done), 1)

        task, = done

        self.assertEqual(task.result(), "done")

    async def test_wait_with_care_multiple(self):
        futures = [self.loop.create_future() for _ in range(100)]
        for i, fut in enumerate(futures):
            fut.set_result(i)

        done, pending = await wait_with_care(*futures)

        self.assertFalse(pending)
        self.assertEqual(len(done), 100)

        for i, fut in enumerate(done):
            self.assertEqual(fut.result(), futures.index(fut))
