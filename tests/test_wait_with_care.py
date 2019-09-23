# Internal
import asyncio
import unittest
from asyncio import CancelledError

# External
import asynctest
from async_tools import wait_with_care


class WaitWithCareTestCase(asynctest.TestCase, unittest.TestCase):
    async def test_wait_with_care_empty(self):
        done, pending = await wait_with_care()

        self.assertEqual(len(done), 0)
        self.assertEqual(len(pending), 0)
        self.assertIsInstance(done, set)
        self.assertIsInstance(pending, set)

    async def test_wait_with_care_simple(self):
        async def long_running_task():
            await asyncio.sleep(0.01)
            return "done"

        done, pending = await wait_with_care(long_running_task())

        self.assertFalse(pending)
        self.assertEqual(len(done), 1)
        self.assertIsInstance(done, set)
        self.assertIsInstance(pending, set)

        task, = done

        self.assertEqual(task.result(), "done")

    async def test_wait_with_care_multiple(self):
        futures = [self.loop.create_future() for _ in range(100)]
        for i, fut in enumerate(futures):
            fut.set_result(i)

        done, pending = await wait_with_care(*futures)

        self.assertFalse(pending)
        self.assertEqual(len(done), 100)
        self.assertIsInstance(done, set)
        self.assertIsInstance(pending, set)

        for i, fut in enumerate(done):
            self.assertEqual(fut.result(), futures.index(fut))

    async def test_wait_with_care_cancelled(self):
        futures = [self.loop.create_future() for _ in range(100)]
        cancelled_future = self.loop.create_future()

        cancelled_future.cancel()

        for i, fut in enumerate(futures):
            fut.set_result(i)

        with self.assertRaises(CancelledError):
            _, __ = await wait_with_care(cancelled_future)

        with self.assertRaises(CancelledError):
            _, __ = await wait_with_care(*futures, cancelled_future)

        done, pending = await wait_with_care(cancelled_future, ignore_cancelled=True)

        self.assertFalse(pending)
        self.assertEqual(len(done), 1)
        self.assertIsInstance(done, set)
        self.assertIsInstance(pending, set)

        cancelled_task, = done

        with self.assertRaises(CancelledError):
            cancelled_task.result()
