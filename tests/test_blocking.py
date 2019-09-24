# Internal
import typing as T
import unittest
from inspect import isawaitable

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


@process
def test_process(precision=100):
    return str(calculate_pi(precision))


class BlockingTestCase(asynctest.TestCase, unittest.TestCase):
    def test_sync_thread(self):
        self.assertEqual(test_thread(), PI)

    async def test_async_thread(self):
        awaitable = test_thread()

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI)

    def test_sync_process(self):
        self.assertEqual(test_process(), PI)

    async def test_async_process(self):
        awaitable = test_process()

        self.assertTrue(isawaitable(awaitable))
        self.assertIsInstance(awaitable, T.Awaitable)

        self.assertEqual(await awaitable, PI)

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
