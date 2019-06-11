# Internal
import asyncio
import unittest

# External
import asynctest
from async_tools import expires


class ExpiresTestCase(asynctest.TestCase, unittest.TestCase):
    async def test_finish_in_time(self):
        async def long_running_task():
            await asyncio.sleep(0.01)
            return "done"

        with expires(0.1, loop=self.loop):
            resp = await long_running_task()

        self.assertEqual(resp, "done")

    async def test_not_finish_in_time(self):
        canceled_raised = False

        async def long_running_task():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                nonlocal canceled_raised
                canceled_raised = True
                raise

        with self.assertRaises(asyncio.TimeoutError):
            with expires(0.01, loop=self.loop) as exp:
                await long_running_task()
                self.assertIs(exp.loop, self.loop)

        self.assertTrue(canceled_raised, "CancelledError was not raised")

    async def test_loop_get_running_loop(self):
        async def run():
            with expires(10) as exp:
                await asyncio.sleep(0.01)
                self.assertIs(exp.loop, self.loop)

        await run()

    async def test_disable(self):
        async def long_running_task():
            await asyncio.sleep(0.1)
            return "done"

        t0 = self.loop.time()
        with expires(None, loop=self.loop):
            resp = await long_running_task()

        self.assertEqual(resp, "done")
        self.assertAlmostEqual(self.loop.time() - t0, 0.11, delta=0.02)

    async def test_enable_zero(self):
        with self.assertRaises(asyncio.TimeoutError):
            with expires(0, loop=self.loop) as exp:
                await asyncio.sleep(0.1)

        self.assertTrue(exp.expired)

    async def test_enable_zero_coro_not_started(self):
        coro_started = False

        async def coro():
            nonlocal coro_started
            coro_started = True

        with self.assertRaises(asyncio.TimeoutError):
            with expires(0, loop=self.loop) as exp:
                await asyncio.sleep(0)
                await coro()

        self.assertTrue(exp.expired)
        self.assertFalse(coro_started)

    async def test_not_relevant_exception(self):
        with self.assertRaises(KeyError):
            with expires(0.1, loop=self.loop):
                raise KeyError

    async def test_canceled_error_is_not_converted_to_timeout(self):
        with self.assertRaises(asyncio.CancelledError):
            with expires(0.001, loop=self.loop):
                raise asyncio.CancelledError

    async def test_blocking_loop(self):
        async def long_running_task():
            import time

            time.sleep(0.1)
            return "done"

        with expires(0.01, loop=self.loop):
            result = await long_running_task()

        self.assertEqual(result, "done")

    async def test_for_race_conditions(self):
        fut = self.loop.create_future()
        self.loop.call_later(0.1, fut.set_result("done"))
        with expires(0.2, loop=self.loop):
            resp = await fut

        self.assertEqual(resp, "done")

    async def test_time(self):
        foo_running = None

        start = self.loop.time()
        with self.assertRaises(asyncio.TimeoutError):
            with expires(0.1, loop=self.loop):
                foo_running = True
                try:
                    await asyncio.sleep(0.2)
                finally:
                    foo_running = False

        self.assertAlmostEqual(self.loop.time() - start, 0.10, delta=0.01)
        self.assertFalse(foo_running)

    @asynctest.fail_on(unused_loop=False)
    def test_raise_runtime_error_if_no_task(self):
        with self.assertRaises(RuntimeError):
            with expires(None, loop=self.loop):
                pass

    async def test_outer_coro_is_not_cancelled(self):
        has_timeout = False

        async def outer():
            nonlocal has_timeout
            try:
                with expires(0.001, loop=self.loop):
                    await asyncio.sleep(1)
            except asyncio.TimeoutError:
                has_timeout = True

        task = asyncio.ensure_future(outer(), loop=self.loop)
        await task

        self.assertTrue(has_timeout)
        self.assertFalse(task.cancelled())
        self.assertTrue(task.done())

    async def test_cancel_outer_coro(self):
        fut = self.loop.create_future()

        async def outer():
            fut.set_result(None)
            await asyncio.sleep(1)

        task = asyncio.ensure_future(outer(), loop=self.loop)
        await fut
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        self.assertTrue(task.cancelled())
        self.assertTrue(task.done())

    async def test_suppress_exception_chain(self):
        with self.assertRaises(asyncio.TimeoutError) as exp:
            with expires(0.01, loop=self.loop):
                await asyncio.sleep(10)

        self.assertFalse(exp.exception.__suppress_context__)

    async def test_expired(self):
        with self.assertRaises(asyncio.TimeoutError):
            with expires(0.01, loop=self.loop) as exp:
                await asyncio.sleep(10)

        self.assertTrue(exp.expired)

    async def test_inner_other_error(self):
        with self.assertRaises(RuntimeError):
            with expires(0.01, loop=self.loop) as exp:
                raise RuntimeError

        self.assertFalse(exp.expired)

    async def test_remaining(self):
        with expires(None, loop=self.loop) as cm:
            self.assertEqual(cm.remaining, 0.0)

        t = expires(1.0, loop=self.loop)
        self.assertEqual(cm.remaining, 0.0)

        with expires(1.0, loop=self.loop) as cm:
            await asyncio.sleep(0.1)
            self.assertLess(cm.remaining, 1.0)

        with self.assertRaises(asyncio.TimeoutError):
            with expires(0.1, loop=self.loop) as cm:
                await asyncio.sleep(0.5)

        self.assertEqual(cm.remaining, 0.0)

    async def test_cancel_without_starting(self):
        tm = expires(1, loop=self.loop)
        tm._expire_task()
        tm._expire_task()  # double call should success

    async def test_reset(self):
        exp = None

        async def outer():
            nonlocal exp
            with expires(0.3, loop=self.loop) as exp:
                await asyncio.sleep(0.1)
                self.assertAlmostEqual(exp.remaining, 0.2, places=2)
                await asyncio.sleep(0.2)

        task = asyncio.ensure_future(outer(), loop=self.loop)
        await asyncio.sleep(0.2)
        exp.reset()
        await task

        self.assertTrue(task.done())
        self.assertFalse(exp.expired)

    async def test_no_reset(self):
        exp = None

        async def outer():
            nonlocal exp
            with expires(0.3, loop=self.loop) as exp:
                await asyncio.sleep(0.1)
                self.assertAlmostEqual(exp.remaining, 0.2, places=2)
                await asyncio.sleep(0.2)

        task = asyncio.ensure_future(outer(), loop=self.loop)
        await asyncio.sleep(0.2)

        with self.assertRaises(asyncio.TimeoutError):
            await task

        self.assertTrue(task.done())
        self.assertTrue(exp.expired)

    async def test_reuse(self):
        exp = None

        with expires(0.3, loop=self.loop) as exp:
            await asyncio.sleep(0.1)

        self.assertFalse(exp.expired)

        with exp:
            await asyncio.sleep(0.1)

        self.assertFalse(exp.expired)

        with exp:
            await asyncio.sleep(0.1)

        self.assertFalse(exp.expired)

        self.assertAlmostEqual(exp.remaining, 0.2, places=2)

    async def test_incorrect_reuse(self):
        exp = None

        with expires(0.3, loop=self.loop) as exp:
            with self.assertRaises(RuntimeError):
                with exp:
                    await asyncio.sleep(0.1)

    async def test_incorrect_reuse_2(self):
        exp = None

        async def outer():
            nonlocal exp
            with expires(0.3, loop=self.loop) as exp:
                await asyncio.sleep(0.1)
                self.assertAlmostEqual(exp.remaining, 0.2, places=2)

        task = asyncio.ensure_future(outer(), loop=self.loop)
        await task

        with self.assertRaises(ValueError):
            with exp:
                pass

    async def test_incorrect_reuse_3(self):
        exp = expires(None, loop=self.loop)

        with self.assertRaises(ValueError):
            exp.reset()

    async def test_reuse_without_task_reference(self):
        from gc import collect

        exp = None

        async def outer():
            nonlocal exp
            with expires(None, loop=self.loop) as exp:
                pass

        task = asyncio.ensure_future(outer(), loop=self.loop)
        await task

        # Remove reference
        del task

        # Allow loop to remove any internal reference
        await asyncio.sleep(0)

        # Force gc to collect all dangling references
        collect(generation=2)

        with self.assertRaises(ReferenceError):
            exp.reset()

    async def test_suppress_no_expires(self):
        with expires(0.3, loop=self.loop, suppress=True) as exp:
            await asyncio.sleep(0.1)

        self.assertAlmostEqual(exp.remaining, 0.2, places=2)
        self.assertFalse(exp.expired)

    async def test_suppress_expires(self):
        with expires(0, loop=self.loop, suppress=True) as exp:
            await asyncio.sleep(0.1)

        self.assertEqual(exp.remaining, 0.0)
        self.assertTrue(exp.expired)


if __name__ == "__main__":
    unittest.main()
