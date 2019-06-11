# Internal
import asyncio
import unittest

# External
import asynctest
from async_tools.context import aclosing


class MyTestCase(asynctest.TestCase, unittest.TestCase):
    async def test_aclosing_async_iterator(self):
        async def async_iterator():
            for a in range(1, 10):
                await asyncio.sleep(0.01)
                yield a

        async with aclosing(async_iterator()) as g:
            async for _ in g:
                pass

        with self.assertRaises(StopAsyncIteration):
            await g.asend(None)

    async def test_aclosing_async_iterator2(self):
        async def async_iterator():
            for a in range(1, 10):
                await asyncio.sleep(0.01)
                yield a

        async with aclosing(async_iterator()) as g:
            self.assertEqual(await g.asend(None), 1)
            self.assertEqual(await g.asend(None), 2)
            self.assertEqual(await g.asend(None), 3)

        with self.assertRaises(StopAsyncIteration):
            await g.asend(None)

    async def test_aclosing_async_generator(self):
        async def async_generator():
            await asyncio.sleep(0.01)
            yield 10
            yield 9

        async with aclosing(async_generator()) as g:
            self.assertEqual(await g.asend(None), 10)

        with self.assertRaises(StopAsyncIteration):
            await g.asend(None)

    async def test_aclosing_async_generator2(self):
        async def async_generator():
            await asyncio.sleep(0.01)

            try:
                yield 10
            finally:
                yield 1000

        with self.assertRaisesRegex(RuntimeError, "ignored GeneratorExit"):
            async with aclosing(async_generator()) as g:
                self.assertEqual(await g.asend(None), 10)


if __name__ == "__main__":
    unittest.main()
