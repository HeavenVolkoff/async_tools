# Internal
import typing as T
import unittest
import multiprocessing
from asyncio import gather
from inspect import isawaitable
from concurrent.futures.thread import ThreadPoolExecutor
from concurrent.futures.process import ProcessPoolExecutor

# External
import asynctest

# External
from async_tools.decorator.blocking import thread, process

PI = "3.141592653589793238462643383279502884197169399375105820974944592307816406286208998628034825342117070"
PI_80 = "3.1415926535897932384626433832795028841971693993751058209749445923078164062862087"


def calculate_pi(precision=100):
    from decimal import Decimal, getcontext

    getcontext().prec = precision
    return sum(
        1
        / Decimal(16) ** k
        * (
            Decimal(4) / (8 * k + 1)
            - Decimal(2) / (8 * k + 4)
            - Decimal(1) / (8 * k + 5)
            - Decimal(1) / (8 * k + 6)
        )
        for k in range(precision)
    )


@thread
def test_thread(precision=100):
    return str(calculate_pi(precision))


@thread(10)
def test_thread_int(precision=100):
    return str(calculate_pi(precision))


thread_pool = ThreadPoolExecutor(multiprocessing.cpu_count())


@thread(thread_pool)
def test_thread_multi(precision=100):
    return str(calculate_pi(precision))


@process
def test_process(precision=100):
    return str(calculate_pi(precision))


@process(10)
def test_process_int(precision=100):
    return str(calculate_pi(precision))


process_pool = ProcessPoolExecutor(multiprocessing.cpu_count())


@process(process_pool)
def test_process_multi(precision=100):
    return str(calculate_pi(precision))


class BlockingTestCase(asynctest.TestCase, unittest.TestCase):
    def test_sync_thread(self):
        self.assertEqual(test_thread(), PI)

    async def test_async_thread(self):
        awaitable = test_thread()

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI)
        self.assertIsInstance(test_thread.__decorator__.executor, ThreadPoolExecutor)

        with self.assertRaises(RuntimeError):
            test_thread.__decorator__.executor = ThreadPoolExecutor()

    async def test_async_thread_manual(self):
        t = ThreadPoolExecutor()
        test_thread_manual = thread(test_thread)
        test_thread_manual.__decorator__.executor = t
        awaitable = test_thread_manual()

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI)
        self.assertIs(test_thread_manual.__decorator__.executor, t)

    async def test_async_thread_int(self):
        awaitable = test_thread_int()

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI)
        self.assertIsInstance(test_thread_int.__decorator__.executor, ThreadPoolExecutor)
        self.assertEqual(test_thread_int.__decorator__.executor._max_workers, 10)

    async def test_async_thread_multiple(self):
        results = await gather(*(test_thread_multi() for _ in range(multiprocessing.cpu_count())))

        for r in results:
            self.assertEqual(r, PI)

        self.assertIs(test_thread_multi.__decorator__.executor, thread_pool)

    def test_sync_process(self):
        self.assertEqual(test_process(), PI)

    async def test_async_process(self):
        awaitable = test_process()

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI)
        self.assertIsInstance(test_process.__decorator__.executor, ProcessPoolExecutor)

    async def test_async_process_int(self):
        awaitable = test_process_int()

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI)
        self.assertIsInstance(test_process_int.__decorator__.executor, ProcessPoolExecutor)
        self.assertEqual(test_process_int.__decorator__.executor._max_workers, 10)

    async def test_async_process_multiple(self):
        results = await gather(*(test_process_multi() for _ in range(multiprocessing.cpu_count())))

        for r in results:
            self.assertEqual(r, PI)

        self.assertIs(test_process_multi.__decorator__.executor, process_pool)

    def test_sync_thread_80(self):
        self.assertEqual(test_thread(80), PI_80)

    async def test_async_thread_80(self):
        awaitable = test_thread(80)

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI_80)

    def test_sync_process_80(self):
        self.assertEqual(test_process(80), PI_80)

    async def test_async_process_80(self):
        awaitable = test_process(80)

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI_80)

    async def test_async_thread_80_kwargs(self):
        awaitable = test_thread(precision=80)

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI_80)

    async def test_async_process_80_kwargs(self):
        awaitable = test_process(precision=80)

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI_80)
