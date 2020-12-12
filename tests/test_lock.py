# Internal
import asyncio
import unittest
from asyncio import get_running_loop
from unittest.mock import Mock, call

# External
import asynctest

from async_tools.lock import ReadLock, WriteLock, AsyncLockStack


@asynctest.strict
class LockTestCase(asynctest.TestCase, unittest.TestCase):
    async def test_read_write_lock(self):
        lock = AsyncLockStack()
        future = self.loop.create_future()
        read_mock = Mock()
        write_mock = Mock()

        async def write():
            async with lock(WriteLock):
                write_mock(1)
                await future

        async def read():
            async with lock(ReadLock):
                read_mock(1)

        loop = get_running_loop()
        done, pending = await asyncio.wait(
            tuple(loop.create_task(task) for task in (read(), read(), read(), read())), timeout=1
        )

        self.assertEqual(len(pending), 0)
        read_mock.assert_has_calls([call(1), call(1), call(1), call(1)])
        read_mock.reset_mock()

        write_task = self.loop.create_task(write())
        await asyncio.sleep(0)
        write_mock.assert_called_once_with(1)

        done, pending = await asyncio.wait(
            tuple(loop.create_task(task) for task in (write(), read(), read())), timeout=1
        )

        self.assertEqual(len(pending), 3)
        write_mock.assert_called_once_with(1)
        write_mock.reset_mock()
        future.set_result(None)
        await write_task

        done, pending = await asyncio.wait(pending, timeout=1)
        self.assertEqual(len(pending), 0)
        read_mock.assert_has_calls([call(1), call(1)])
        write_mock.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
